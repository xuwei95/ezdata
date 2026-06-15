#!/usr/bin/env python3
"""
任务调度 + 告警中心 端到端浏览器测试脚本(自包含，无需 playwright)。

通过 Chrome DevTools Protocol 驱动**真实 Chrome**，按用例点击页面、断言结果，覆盖：
  1. 任务 CRUD(新增/修改/删除)
  2. 定时任务调度(创建定时任务，等待 cron 触发，校验产生执行记录)
  3. 动态任务表单(选择模板后低代码动态渲染参数表单)
  4. 动态代码运行失败 -> 触发告警 -> 多渠道转发(webhook + 转通知)

用法:
  python e2e_task_alert.py                 # 无头(headless)真实 Chrome，默认
  python e2e_task_alert.py --headed        # 有界面真实浏览器
  python e2e_task_alert.py --frontend http://localhost:12580 --backend http://localhost:9099 --redis-port 16379

依赖：仅标准库 + 本机 Chrome；目标为开发栈(docker-compose.dev.yml)。
captcha 已启用时，脚本会从开发栈暴露的 Redis(默认 :16379, db2)读取验证码答案完成登录。
"""

import argparse
import base64
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    raise RuntimeError('未找到 Chrome/Edge，请安装或修改 CHROME_CANDIDATES')


# ---------------------------------------------------------------------------
# 极简 Redis 客户端(读取验证码答案)
# ---------------------------------------------------------------------------
def redis_get(key, host, port, db):
    s = socket.create_connection((host, port), timeout=5)
    try:
        def send(*args):
            out = f'*{len(args)}\r\n'.encode()
            for a in args:
                a = str(a).encode()
                out += b'$' + str(len(a)).encode() + b'\r\n' + a + b'\r\n'
            s.sendall(out)
            return s.recv(65536)
        send('SELECT', db)
        resp = send('GET', key)
        if resp.startswith(b'$-1'):
            return None
        if resp.startswith(b'$'):
            header, rest = resp.split(b'\r\n', 1)
            n = int(header[1:])
            return rest[:n].decode()
        return None
    finally:
        s.close()


# ---------------------------------------------------------------------------
# 登录(处理验证码)
# ---------------------------------------------------------------------------
def login(backend, redis_host, redis_port):
    resp = json.loads(urllib.request.urlopen(f'{backend}/captchaImage').read())
    uuid = resp.get('uuid', '')
    code = ''
    if resp.get('captchaEnabled'):
        code = redis_get(f'captcha_codes:{uuid}', redis_host, redis_port, 2) or ''
    data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123', 'code': code, 'uuid': uuid}).encode()
    req = urllib.request.Request(f'{backend}/login', data=data,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
    out = json.loads(urllib.request.urlopen(req).read())
    token = out.get('token') or out.get('data', {}).get('token')
    if not token:
        raise RuntimeError(f'登录失败: {out}')
    return token


def api(backend, token, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f'{backend}{path}', data=data, method=method,
                                 headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req).read())


# ---------------------------------------------------------------------------
# CDP 浏览器封装
# ---------------------------------------------------------------------------
class Browser:
    def __init__(self, headed, port=None):
        # 端口/Profile 按 pid 唯一化，避免遗留 Chrome 占用端口或锁定 profile
        self.port = port or (9400 + os.getpid() % 500)
        self.headed = headed
        self.proc = None
        self.s = None
        self._id = 0

    def start(self):
        chrome = find_chrome()
        profile = os.path.join(os.environ.get('TEMP', '/tmp'), f'e2e-task-alert-{os.getpid()}')
        os.makedirs(profile, exist_ok=True)
        args = [chrome, '--no-first-run', '--no-default-browser-check', '--disable-gpu',
                f'--remote-debugging-port={self.port}', f'--user-data-dir={profile}',
                '--window-size=1600,1000', 'about:blank']
        if not self.headed:
            args.insert(1, '--headless=new')
        self.proc = subprocess.Popen(args)
        ws = None
        for _ in range(40):
            try:
                data = json.load(urllib.request.urlopen(f'http://localhost:{self.port}/json'))
                pages = [t for t in data if t.get('type') == 'page']
                if pages:
                    ws = pages[0]['webSocketDebuggerUrl']
                    break
            except Exception:
                pass
            time.sleep(0.5)
        if not ws:
            raise RuntimeError('无法连接 Chrome DevTools')
        self._connect(ws)
        self.cmd('Network.enable')
        self.cmd('Page.enable')
        self.cmd('Runtime.enable')

    def _connect(self, url):
        hp, path = url[5:].split('/', 1)
        host, port = hp.split(':')
        self.s = socket.create_connection((host, int(port)))
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f'GET /{path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n'
                        f'Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.s.recv(4096)

    def _send(self, payload):
        d = payload.encode(); hd = bytearray([0x81]); n = len(d); m = os.urandom(4)
        if n < 126:
            hd.append(0x80 | n)
        elif n < 65536:
            hd.append(0x80 | 126); hd += struct.pack('>H', n)
        else:
            hd.append(0x80 | 127); hd += struct.pack('>Q', n)
        hd += m
        self.s.sendall(bytes(hd) + bytes(b ^ m[i % 4] for i, b in enumerate(d)))

    def _recv(self):
        def rd(n):
            b = b''
            while len(b) < n:
                c = self.s.recv(n - len(b))
                if not c:
                    raise IOError('socket closed')
                b += c
            return b
        b0, b1 = rd(2); ln = b1 & 0x7F
        if ln == 126:
            ln = struct.unpack('>H', rd(2))[0]
        elif ln == 127:
            ln = struct.unpack('>Q', rd(8))[0]
        return rd(ln).decode('utf-8', 'replace')

    def cmd(self, method, params=None):
        self._id += 1
        mid = self._id
        self._send(json.dumps({'id': mid, 'method': method, 'params': params or {}}))
        t = time.time()
        while time.time() - t < 30:
            msg = json.loads(self._recv())
            if msg.get('id') == mid:
                return msg.get('result', {})
        return {}

    def ev(self, expr):
        r = self.cmd('Runtime.evaluate', {'expression': expr, 'returnByValue': True})
        return r.get('result', {}).get('value')

    def set_cookie(self, name, value, domain):
        self.cmd('Network.setCookie', {'name': name, 'value': value, 'domain': domain, 'path': '/'})

    def navigate(self, url):
        self.cmd('Page.navigate', {'url': url})

    def goto_ready(self, url, marker, timeout=90):
        self.navigate(url)
        end = time.time() + timeout
        while time.time() < end:
            if self.ev(f'document.body && document.body.innerText.indexOf({json.dumps(marker)}) >= 0'):
                time.sleep(1.5)
                return True
            time.sleep(2)
        return False

    def wait_text(self, text, timeout=15):
        end = time.time() + timeout
        while time.time() < end:
            if self.ev(f'document.body && document.body.innerText.indexOf({json.dumps(text)}) >= 0'):
                return True
            time.sleep(0.5)
        return False

    def click_text(self, text, nth=0):
        js = ("(function(){var bs=[...document.querySelectorAll('button,a,span')]"
              ".filter(function(x){return x.textContent.trim().indexOf(%s)>=0 && x.offsetParent!==null});"
              "var b=bs[%d];if(b){b.click();return true}return false})()" % (json.dumps(text), nth))
        return self.ev(js)

    def click_row(self, text, nth=0):
        """点击表格行(tbody)内可见按钮，避免误点顶部批量按钮(如批量删除)。"""
        js = ("(function(){var bs=[...document.querySelectorAll('tbody tr button')]"
              ".filter(function(x){return x.offsetParent!==null && x.textContent.indexOf(%s)>=0});"
              "var b=bs[%d];if(b){b.click();return true}return false})()" % (json.dumps(text), nth))
        return self.ev(js)

    def click_dialog_button(self, text):
        js = ("(function(){var b=[...document.querySelectorAll('.el-dialog button,.el-drawer button')]"
              ".filter(function(x){return x.offsetParent!==null})"
              ".find(function(x){return x.textContent.trim().replace(/\\s/g,'')===%s.replace(/\\s/g,'')});"
              "if(b){b.click();return true}return false})()" % json.dumps(text))
        return self.ev(js)

    def fill_label(self, label, value):
        """按 el-form-item label 定位输入框并填值(原生 setter 触发 v-model)；仅可见对话框。"""
        js = ("(function(){var items=[...document.querySelectorAll('.el-dialog .el-form-item,.el-drawer .el-form-item')]"
              ".filter(function(x){return x.offsetParent!==null});"
              "var it=items.find(function(x){var l=x.querySelector('.el-form-item__label');return l&&l.textContent.indexOf(%s)>=0});"
              "if(!it)return false;var el=it.querySelector('input,textarea');if(!el)return false;"
              "var proto=el.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;"
              "var setter=Object.getOwnPropertyDescriptor(proto,'value').set;setter.call(el,%s);"
              "el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));return true})()"
              % (json.dumps(label), json.dumps(value)))
        return self.ev(js)

    def fill_placeholder(self, ph, value):
        js = ("(function(){var el=[...document.querySelectorAll('.el-dialog input,.el-dialog textarea')]"
              ".filter(function(x){return x.offsetParent!==null})"
              ".find(function(x){return (x.placeholder||'').indexOf(%s)>=0});if(!el)return false;"
              "var proto=el.tagName==='TEXTAREA'?window.HTMLTextAreaElement.prototype:window.HTMLInputElement.prototype;"
              "var setter=Object.getOwnPropertyDescriptor(proto,'value').set;setter.call(el,%s);"
              "el.dispatchEvent(new Event('input',{bubbles:true}));el.dispatchEvent(new Event('change',{bubbles:true}));return true})()"
              % (json.dumps(ph), json.dumps(value)))
        return self.ev(js)

    def select_option(self, label, option_text, timeout=8):
        """打开某 el-form-item 内的 el-select 并选中包含 option_text 的项(带轮询，兼容选项异步加载)。"""
        opened = self.ev(
            "(function(){var items=[...document.querySelectorAll('.el-dialog .el-form-item')]"
            ".filter(function(x){return x.offsetParent!==null});"
            "var it=items.find(function(x){var l=x.querySelector('.el-form-item__label');return l&&l.textContent.indexOf(%s)>=0});"
            "if(!it)return false;var sel=it.querySelector('.el-select');if(!sel)return false;"
            "var trig=sel.querySelector('.el-select__wrapper')||sel.querySelector('input')||sel;trig.click();return true})()"
            % json.dumps(label))
        if not opened:
            return False
        end = time.time() + timeout
        while time.time() < end:
            clicked = self.ev(
                "(function(){var os=[...document.querySelectorAll('.el-select-dropdown__item')]"
                ".filter(function(d){return d.offsetParent!==null});"
                "var o=os.find(function(x){return x.textContent.indexOf(%s)>=0});if(o){o.click();return true}return false})()"
                % json.dumps(option_text))
            if clicked:
                return True
            time.sleep(0.5)
        return False

    def click_radio(self, text):
        js = ("(function(){var r=[...document.querySelectorAll('.el-dialog .el-radio')]"
              ".find(function(x){return x.textContent.trim().indexOf(%s)>=0});if(r){r.click();return true}return false})()"
              % json.dumps(text))
        return self.ev(js)

    def screenshot(self, path):
        r = self.cmd('Page.captureScreenshot', {'format': 'png'})
        if r.get('data'):
            with open(path, 'wb') as f:
                f.write(base64.b64decode(r['data']))

    def stop(self):
        try:
            if self.proc:
                self.proc.terminate()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 测试用例
# ---------------------------------------------------------------------------
class Runner:
    def __init__(self, b, front, backend, token, shots_dir):
        self.b = b
        self.front = front
        self.backend = backend
        self.token = token
        self.shots = shots_dir
        self.results = []
        self.ts = time.strftime('%H%M%S')

    def record(self, name, ok, detail=''):
        self.results.append((name, ok, detail))
        print(('  [PASS] ' if ok else '  [FAIL] ') + name + (f'  -- {detail}' if detail else ''))

    def shot(self, name):
        if self.shots:
            self.b.screenshot(os.path.join(self.shots, name + '.png'))

    # --- 用例1：任务 CRUD ---
    def case_task_crud(self):
        print('用例1：任务 CRUD')
        b = self.b
        name = f'E2E_CRUD_{self.ts}'
        b.goto_ready(self.front + '/task/info', '任务名称')
        try:
            b.click_text('新增')
            assert b.wait_text('任务模板', 8), '新增对话框未出现'
            b.fill_label('任务名称', name)
            assert b.select_option('任务模板', 'PythonTask'), '选择模板失败'
            time.sleep(1.5)  # 等待默认代码低代码渲染
            b.click_dialog_button('确 定')
            ok_add = b.wait_text('新增成功', 10)
            self.record('1.1 新增任务', ok_add)
            self.shot('e2e-01-task-add')

            # 搜索
            b.fill_placeholder('请输入任务名称', name)
            b.click_text('搜索')
            time.sleep(1.5)
            self.record('1.2 列表可见', b.wait_text(name, 8))

            # 修改
            b.click_row('修改')
            assert b.wait_text('任务模板', 8)
            time.sleep(2)  # 等待 getTask 回填 + 低代码参数还原
            b.fill_label('任务名称', name + '_edit')
            time.sleep(0.6)
            b.click_dialog_button('确 定')
            self.record('1.3 修改任务', b.wait_text('修改成功', 10))

            # 删除
            b.fill_placeholder('请输入任务名称', name + '_edit')
            b.click_text('搜索')
            time.sleep(1.5)
            b.click_row('删除')
            time.sleep(0.8)
            b.click_text('确定')  # 确认弹窗
            self.record('1.4 删除任务', b.wait_text('删除成功', 10))
        except Exception as e:
            self.record('用例1 异常', False, str(e))

    # --- 用例2：定时任务调度 ---
    def case_schedule(self):
        print('用例2：定时任务调度(等待 cron 触发)')
        b = self.b
        name = f'E2E_CRON_{self.ts}'
        b.goto_ready(self.front + '/task/info', '任务名称')
        try:
            b.click_text('新增')
            assert b.wait_text('任务模板', 8)
            b.fill_label('任务名称', name)
            assert b.select_option('任务模板', 'PythonTask'), '选择模板失败'
            time.sleep(1.5)
            b.click_radio('定时')
            time.sleep(0.5)
            b.fill_placeholder('请输入cron执行表达式', '0/5 * * * * ?')  # 每5秒
            b.click_dialog_button('确 定')
            self.record('2.1 新增定时任务', b.wait_text('新增成功', 10))
            self.shot('e2e-02-cron-add')

            # 校验关联 sys_job 已建(后端API)
            time.sleep(2)
            lst = api(self.backend, self.token, 'GET', '/task/info/list?pageNum=1&pageSize=50')
            row = next((r for r in lst.get('rows', []) if r.get('name') == name), None)
            self.record('2.2 任务为定时且关联调度', bool(row and row.get('triggerType') == 2 and row.get('jobId')),
                        f"jobId={row.get('jobId') if row else None}")

            tid = row.get('id') if row else None
            # 新建任务默认停用 -> 启用后其 sys_job 才会被 APScheduler 调度触发
            if tid:
                api(self.backend, self.token, 'PUT', '/task/info/changeStatus', {'id': tid, 'status': 1})

            # 等待 cron 触发 -> 执行记录抽屉应有实例
            print('  启用任务，等待 cron 触发(最多 35s)...')
            instance_seen = False
            for _ in range(18):
                time.sleep(2.5)
                recs = api(self.backend, self.token, 'GET',
                           f'/task/instance/list?pageNum=1&pageSize=5&taskId={tid}') if tid else {'rows': []}
                if recs.get('rows'):
                    instance_seen = True
                    break
            self.record('2.3 cron 触发产生执行记录', instance_seen)

            # UI 打开记录抽屉截图
            b.fill_placeholder('请输入任务名称', name)
            b.click_text('搜索')
            time.sleep(1.5)
            b.click_row('记录')
            time.sleep(2)
            self.shot('e2e-03-cron-records')

            # 清理：停用并删除
            if tid:
                api(self.backend, self.token, 'PUT', '/task/info/changeStatus', {'id': tid, 'status': 0})
                api(self.backend, self.token, 'DELETE', f'/task/info/{tid}')
        except Exception as e:
            self.record('用例2 异常', False, str(e))

    # --- 用例3：动态任务表单(低代码渲染) ---
    def case_dynamic_form(self):
        print('用例3：动态任务表单(低代码渲染)')
        b = self.b
        name = f'E2E_DYN_{self.ts}'
        b.goto_ready(self.front + '/task/info', '任务名称')
        try:
            b.click_text('新增')
            assert b.wait_text('任务模板', 8)
            # 选 DynamicTask -> 应动态渲染出"消息内容"字段
            assert b.select_option('任务模板', 'DynamicTask'), '选择 DynamicTask 失败'
            time.sleep(1.5)
            rendered = b.wait_text('消息内容', 6)
            self.record('3.1 选择模板后低代码渲染参数字段', rendered)
            self.shot('e2e-04-dynamic-form')

            b.fill_label('任务名称', name)
            b.fill_label('消息内容', 'hello-e2e')
            b.click_dialog_button('确 定')
            self.record('3.2 创建动态代码任务', b.wait_text('新增成功', 10))

            # 执行一次
            b.fill_placeholder('请输入任务名称', name)
            b.click_text('搜索')
            time.sleep(1.5)
            b.click_row('执行')
            time.sleep(0.8)
            b.click_text('确定')
            self.record('3.3 触发执行', b.wait_text('已触发执行', 10))

            # 清理
            time.sleep(1)
            lst = api(self.backend, self.token, 'GET', '/task/info/list?pageNum=1&pageSize=50')
            tid = next((r['id'] for r in lst.get('rows', []) if r.get('name') == name), None)
            if tid:
                api(self.backend, self.token, 'DELETE', f'/task/info/{tid}')
        except Exception as e:
            self.record('用例3 异常', False, str(e))

    # --- 用例4：动态代码失败 -> 告警 -> 转发(webhook + 转通知) ---
    def case_alert(self):
        print('用例4：动态代码失败 -> 告警 -> 转发(webhook + 转通知)')
        b = self.b
        name = f'E2E_ALERT_{self.ts}'
        # 4.0 经 API 准备告警策略(webhook + 转通知)，避免多渠道 UI 自动化脆弱
        forward = [
            {'type': 'webhook', 'webhook_url': f'{self.backend}/dev-api/alert/sink', 'webhook_method': 'POST'},
            {'type': 'notice', 'notice_users': 'admin'},
        ]
        sname = f'E2E告警策略_{self.ts}'
        api(self.backend, self.token, 'POST', '/alert/strategy', {
            'strategyName': sname, 'biz': 'scheduler', 'status': 1,
            'triggerConf': json.dumps({'level': 2}), 'forwardConf': json.dumps(forward),
        })
        try:
            b.goto_ready(self.front + '/task/info', '任务名称')
            b.click_text('新增')
            assert b.wait_text('任务模板', 8)
            b.fill_label('任务名称', name)
            assert b.select_option('任务模板', 'PythonTask'), '选择模板失败'
            time.sleep(1.5)
            # 用失败代码覆盖默认代码
            b.fill_placeholder('需定义 run(params, logger) 函数',
                               'def run(params, logger):\n    raise RuntimeError("e2e boom")')
            # 绑定告警策略(失败告警多选)
            assert b.select_option('失败告警', sname), '绑定告警策略失败'
            time.sleep(0.5)
            b.click_dialog_button('确 定')
            self.record('4.1 创建失败任务并绑定告警策略', b.wait_text('新增成功', 10))
            self.shot('e2e-05-alert-task')

            # 执行(会失败 -> 触发告警)
            b.fill_placeholder('请输入任务名称', name)
            b.click_text('搜索')
            time.sleep(1.5)
            b.click_row('执行')
            time.sleep(0.8)
            b.click_text('确定')
            b.wait_text('已触发执行', 10)
            print('  等待告警生成(最多 40s)...')

            # 校验告警记录(UI: 告警记录页)
            alert_ok = False
            for _ in range(20):
                time.sleep(2)
                recs = api(self.backend, self.token, 'GET',
                           f'/alert/record/list?pageNum=1&pageSize=10&title={urllib.parse.quote(name)}')
                if recs.get('rows'):
                    alert_ok = True
                    break
            self.record('4.2 任务失败生成告警记录', alert_ok)

            b.goto_ready(self.front + '/alert/record', '标题')
            time.sleep(1.5)
            self.shot('e2e-06-alert-record')

            # 校验转通知(UI: 通知公告)：notice 渠道写入 sys_notice，标题含任务名
            notice_ok = b.goto_ready(self.front + '/system/notice', '公告标题')
            time.sleep(1.5)
            notice_ok = notice_ok and b.wait_text(name, 8)
            self.record('4.3 转通知渠道生成系统通知', notice_ok)
            self.shot('e2e-07-notice')

            # 清理任务
            lst = api(self.backend, self.token, 'GET', '/task/info/list?pageNum=1&pageSize=50')
            tid = next((r['id'] for r in lst.get('rows', []) if r.get('name') == name), None)
            if tid:
                api(self.backend, self.token, 'DELETE', f'/task/info/{tid}')
        except Exception as e:
            self.record('用例4 异常', False, str(e))

    # --- 用例5：任务状态同步 / 启用禁用 / 修改 -> 关联 sys_job 同步 ---
    # 说明：以"调度行为"(启用后是否真正被 APScheduler 触发、禁用/删除后是否停止)及任务列表回填的
    #       jobId 作为同步的事实依据。不依赖 /monitor/job(list/detail) 接口——它们带 ApiCache，
    #       而任务模块直接改 sys_job 不会触发其 @ApiCacheEvict，详情/列表可能返回缓存旧值。
    def _task_row(self, name):
        lst = api(self.backend, self.token, 'GET', '/task/info/list?pageNum=1&pageSize=100')
        return next((r for r in lst.get('rows', []) if r.get('name') == name), None)

    def _instance_count(self, tid):
        recs = api(self.backend, self.token, 'GET', f'/task/instance/list?pageNum=1&pageSize=100&taskId={tid}')
        return recs.get('total') or len(recs.get('rows', []))

    def _wait_fire(self, tid, base, attempts=16, interval=2.5):
        """轮询等待执行记录数超过 base，返回是否在限定时间内触发。"""
        for _ in range(attempts):
            time.sleep(interval)
            if self._instance_count(tid) > base:
                return True
        return False

    def case_job_sync(self):
        print('用例5：任务状态同步(启用/禁用/修改) -> 关联调度(sys_job)同步')
        name = f'E2E_SYNC_{self.ts}'
        cron1 = '0/5 * * * * ?'   # 每5秒
        cron2 = '0/4 * * * * ?'   # 修改后：每4秒(改 cron 以验证重建)
        params = json.dumps({'code': "def run(params, logger):\n    logger.info('sync e2e ok')"})
        tid = None
        try:
            # 5.1 新增定时任务(默认停用) -> 回填 jobId(关联调度已建立)，且停用态不被调度触发
            api(self.backend, self.token, 'POST', '/task/info', {
                'name': name, 'templateCode': 'PythonTask', 'taskType': 1,
                'triggerType': 2, 'crontab': cron1, 'status': 0, 'params': params, 'runQueue': 'default',
            })
            time.sleep(1.5)
            row = self._task_row(name)
            tid = row.get('id') if row else None
            job_id = row.get('jobId') if row else None
            print('  停用态观察 12s 应不被调度...')
            time.sleep(12)
            ok_create = bool(tid and job_id and row.get('triggerType') == 2) and self._instance_count(tid) == 0
            self.record('5.1 新增定时任务建立关联调度(回填jobId)且停用态不触发', ok_create,
                        f"jobId={job_id} instances={self._instance_count(tid) if tid else '-'}")
            self.shot('e2e-08-sync-created')

            # 5.2 启用 -> 任务被 APScheduler 真正调度并产生执行记录(行为证明启用已同步)
            api(self.backend, self.token, 'PUT', '/task/info/changeStatus', {'id': tid, 'status': 1})
            print('  启用后等待 cron 触发(最多 40s)...')
            fired = self._wait_fire(tid, 0)
            self.record('5.2 启用同步:任务被调度并触发执行', fired)

            # 5.3 禁用 -> 停止调度(行为证明禁用已同步：观察期内无新增执行记录)
            api(self.backend, self.token, 'PUT', '/task/info/changeStatus', {'id': tid, 'status': 0})
            time.sleep(2)
            base = self._instance_count(tid)
            print('  禁用后观察 14s 应无新增执行记录...')
            time.sleep(14)
            after = self._instance_count(tid)
            self.record('5.3 禁用同步:停止调度(无新增执行记录)', after == base, f"before={base} after={after}")

            # 5.4 修改(改 cron 并启用) -> 关联 sys_job 重建(jobId 变化)且按新配置重新被调度
            api(self.backend, self.token, 'PUT', '/task/info', {
                'id': tid, 'name': name, 'templateCode': 'PythonTask', 'taskType': 1,
                'triggerType': 2, 'crontab': cron2, 'status': 1, 'params': params, 'runQueue': 'default',
            })
            time.sleep(1.5)
            row2 = self._task_row(name)
            new_job_id = row2.get('jobId') if row2 else None
            recreated = bool(new_job_id and new_job_id != job_id)
            base2 = self._instance_count(tid)
            print('  修改启用后等待重新触发(最多 40s)...')
            refired = self._wait_fire(tid, base2)
            self.record('5.4 修改重建关联调度(jobId变化)并按新配置触发', recreated and refired,
                        f"oldJob={job_id} newJob={new_job_id} refired={refired}")
            self.shot('e2e-09-sync-edited')

            # 5.5 单次触发(执行一次) -> 直接投递 Celery，返回 instanceId
            run_resp = api(self.backend, self.token, 'PUT', f'/task/info/run/{tid}')
            run_ok = run_resp.get('code') == 200 and bool((run_resp.get('data') or {}).get('instanceId'))
            self.record('5.5 单次触发执行返回 instanceId', run_ok, f"data={run_resp.get('data')}")

            # 5.6 删除(启用态下直接删除) -> 任务消失且关联调度被移除(删除后不再触发)
            api(self.backend, self.token, 'PUT', '/task/info/changeStatus', {'id': tid, 'status': 1})
            self._wait_fire(tid, self._instance_count(tid))  # 确认删除前确实在跑
            base3 = self._instance_count(tid)
            api(self.backend, self.token, 'DELETE', f'/task/info/{tid}')
            deleted_tid = tid
            tid = None
            print('  删除后观察 14s 应彻底停止触发...')
            time.sleep(14)
            gone = self._task_row(name) is None
            after3 = self._instance_count(deleted_tid)
            self.record('5.6 删除任务移除关联调度(任务消失且停止触发)', gone and after3 == base3,
                        f"taskGone={gone} before={base3} after={after3}")
        except Exception as e:
            self.record('用例5 异常', False, str(e))
        finally:
            # 兜底清理(异常时残留)
            if tid:
                try:
                    api(self.backend, self.token, 'PUT', '/task/info/changeStatus', {'id': tid, 'status': 0})
                    api(self.backend, self.token, 'DELETE', f'/task/info/{tid}')
                except Exception:
                    pass

    def run_all(self):
        self.case_task_crud()
        self.case_schedule()
        self.case_dynamic_form()
        self.case_alert()
        self.case_job_sync()


def main():
    ap = argparse.ArgumentParser(description='任务调度+告警 端到端浏览器测试')
    ap.add_argument('--headed', action='store_true', help='使用有界面的真实浏览器(默认无头)')
    ap.add_argument('--frontend', default='http://localhost:12580')
    ap.add_argument('--backend', default='http://localhost:9099')
    ap.add_argument('--redis-host', default='127.0.0.1')
    ap.add_argument('--redis-port', type=int, default=16379)
    ap.add_argument('--shots', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), '_e2e_shots'))
    args = ap.parse_args()

    if args.shots:
        os.makedirs(args.shots, exist_ok=True)

    print(f'登录 {args.backend} ...')
    token = login(args.backend, args.redis_host, args.redis_port)
    print('登录成功')

    b = Browser(headed=args.headed)
    b.start()
    b.set_cookie('Admin-Token', token, 'localhost')

    runner = Runner(b, args.frontend, args.backend, token, args.shots)
    try:
        runner.run_all()
    finally:
        b.stop()

    print('\n==================== 测试结果 ====================')
    passed = sum(1 for _, ok, _ in runner.results if ok)
    for name, ok, detail in runner.results:
        print(('PASS ' if ok else 'FAIL ') + name + (f'  -- {detail}' if detail else ''))
    total = len(runner.results)
    print(f'\n通过 {passed}/{total}')
    sys.exit(0 if passed == total else 1)


if __name__ == '__main__':
    main()
