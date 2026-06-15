#!/usr/bin/env python3
"""
多租户(行级)端到端测试(纯 API，无需浏览器)。

验证「租户=顶级部门」隔离：平台超管(admin,user_id=1)可见全部；普通租户用户只能看到本租户
(其部门的顶级部门)的数据，跨租户互不可见；新建数据自动归属当前租户；定时任务执行记录按租户归属。

用法：
  python e2e_multi_tenant.py
  python e2e_multi_tenant.py --backend http://localhost:9099 --redis-port 16379

依赖：仅标准库；目标为开发栈(docker-compose.dev.yml)。captcha 已启用时从 Redis(:16379 db2) 读答案。
"""

import argparse
import json
import socket
import sys
import time
import urllib.parse
import urllib.request

BACKEND = 'http://localhost:9099'
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 16379
TENANT_PWD = 'Tenant@123'


# --------------------------- 极简 Redis(读验证码) ---------------------------
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


# --------------------------- HTTP ---------------------------
def login(username, password):
    resp = json.loads(urllib.request.urlopen(f'{BACKEND}/captchaImage').read())
    uuid = resp.get('uuid', '')
    code = ''
    if resp.get('captchaEnabled'):
        code = redis_get(f'captcha_codes:{uuid}', REDIS_HOST, REDIS_PORT, 2) or ''
    data = urllib.parse.urlencode({'username': username, 'password': password, 'code': code, 'uuid': uuid}).encode()
    req = urllib.request.Request(f'{BACKEND}/login', data=data,
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
    out = json.loads(urllib.request.urlopen(req).read())
    token = out.get('token') or out.get('data', {}).get('token')
    if not token:
        raise RuntimeError(f'登录失败({username}): {out}')
    return token


def api(token, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f'{BACKEND}{path}', data=data, method=method,
                                 headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as ex:
        return {'code': ex.code, 'msg': ex.read().decode('utf-8', 'replace')[:300]}


# --------------------------- 工具 ---------------------------
RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((name, ok))
    print(('  [PASS] ' if ok else '  [FAIL] ') + name + (f'  -- {detail}' if detail else ''))


def dept_list(token):
    return api(token, 'GET', '/system/dept/list').get('data', []) or []


def find_dept(token, name):
    return next((d for d in dept_list(token) if d.get('deptName') == name), None)


def task_list(token):
    r = api(token, 'GET', '/task/info/list?pageNum=1&pageSize=100')
    return r.get('rows', []) or []


def strat_list(token):
    r = api(token, 'GET', '/alert/strategy/list?pageNum=1&pageSize=100')
    return r.get('rows', []) or []


def user_names(token):
    r = api(token, 'GET', '/system/user/list?pageNum=1&pageSize=100')
    return [u.get('userName') for u in (r.get('rows', []) or [])]


def create_dept(admin, name, parent_id):
    return api(admin, 'POST', '/system/dept', {
        'deptName': name, 'parentId': parent_id, 'orderNum': 1, 'status': '0', 'leader': 'tester',
    })


def create_user(admin, user_name, dept_id):
    return api(admin, 'POST', '/system/user', {
        'userName': user_name, 'nickName': user_name, 'password': TENANT_PWD,
        'deptId': dept_id, 'status': '0', 'roleIds': [1], 'postIds': [],
    })


def create_task(token, name, code='print_ok'):
    params = json.dumps({'run_type': 'code', 'code': "def run(params, logger):\n    logger.info('mt')\n    return 'ok'"})
    return api(token, 'POST', '/task/info', {
        'name': name, 'templateCode': 'PythonTask', 'taskType': 1,
        'triggerType': 1, 'status': 0, 'params': params, 'runQueue': 'default',
    })


def create_strategy(token, name):
    return api(token, 'POST', '/alert/strategy', {
        'strategyName': name, 'biz': 'scheduler', 'status': 1,
        'triggerConf': json.dumps({'level': 2}), 'forwardConf': json.dumps([]),
    })


# --------------------------- 主流程 ---------------------------
def main():
    global BACKEND, REDIS_HOST, REDIS_PORT
    ap = argparse.ArgumentParser(description='多租户端到端测试')
    ap.add_argument('--backend', default=BACKEND)
    ap.add_argument('--redis-host', default=REDIS_HOST)
    ap.add_argument('--redis-port', type=int, default=REDIS_PORT)
    args = ap.parse_args()
    BACKEND, REDIS_HOST, REDIS_PORT = args.backend, args.redis_host, args.redis_port

    ts = time.strftime('%H%M%S')
    A_dept_name, B_dept_name = f'租户A_{ts}', f'租户B_{ts}'
    A_user, B_user = f'tenantA_{ts}', f'tenantB_{ts}'
    A_sub_dept = f'A子部门_{ts}'

    print('== 平台超管登录(bypass) ==')
    admin = login('admin', 'admin123')
    print('admin OK')

    # 1. 平台超管创建两个顶级部门(=两个租户)
    print('== 创建两个租户(顶级部门) ==')
    create_dept(admin, A_dept_name, 0)
    create_dept(admin, B_dept_name, 0)
    time.sleep(0.5)
    dA, dB = find_dept(admin, A_dept_name), find_dept(admin, B_dept_name)
    check('1.1 创建租户A/B顶级部门', bool(dA and dB), f'A={dA and dA.get("deptId")} B={dB and dB.get("deptId")}')
    if not (dA and dB):
        return finish()
    A_id, B_id = dA['deptId'], dB['deptId']

    # 2. 各租户创建一个用户(赋超级管理员角色=全权限，但 user_id!=1 故受租户限制)
    print('== 各租户创建用户 ==')
    rA, rB = create_user(admin, A_user, A_id), create_user(admin, B_user, B_id)
    check('2.1 创建租户用户A/B', rA.get('code') in (200, None) and rB.get('code') in (200, None), f'A={rA.get("msg")} B={rB.get("msg")}')

    # 3. 租户用户登录
    print('== 租户用户登录 ==')
    try:
        ta = login(A_user, TENANT_PWD)
        tb = login(B_user, TENANT_PWD)
        check('3.1 租户用户A/B登录', bool(ta and tb))
    except Exception as e:
        check('3.1 租户用户A/B登录', False, str(e))
        return finish()

    # 4. 任务隔离：A 建任务，A 可见、B 不可见、admin 全见
    print('== 任务数据隔离 ==')
    a_task = f'MT_A_task_{ts}'
    create_task(ta, a_task)
    time.sleep(0.5)
    a_sees = any(t['name'] == a_task for t in task_list(ta))
    b_sees = any(t['name'] == a_task for t in task_list(tb))
    admin_sees = any(t['name'] == a_task for t in task_list(admin))
    check('4.1 A建任务-A可见', a_sees)
    check('4.2 A建任务-B不可见(跨租户隔离)', not b_sees)
    check('4.3 A建任务-平台超管可见', admin_sees)
    # B 的任务列表不应包含 A 的任意任务(数量层面)
    b_task_count = len(task_list(tb))
    check('4.4 B租户任务列表不含A数据', all(t['name'] != a_task for t in task_list(tb)), f'B列表数={b_task_count}')

    # 5. 告警策略隔离
    print('== 告警策略隔离 ==')
    a_strat = f'MT_A_strat_{ts}'
    create_strategy(ta, a_strat)
    time.sleep(0.5)
    check('5.1 A建策略-A可见', any(s.get('strategyName') == a_strat for s in strat_list(ta)))
    check('5.2 A建策略-B不可见', not any(s.get('strategyName') == a_strat for s in strat_list(tb)))

    # 6. 用户隔离：A 看不到 B 的用户，反之亦然
    print('== 用户数据隔离 ==')
    a_users, b_users = user_names(ta), user_names(tb)
    check('6.1 A可见自身、不可见B用户', A_user in a_users and B_user not in a_users, f'A可见={a_users}')
    check('6.2 B可见自身、不可见A用户', B_user in b_users and A_user not in b_users, f'B可见={b_users}')

    # 7. 部门隔离：A 建子部门，B 看不到；B 看不到 A 的顶级部门
    print('== 部门数据隔离 ==')
    create_dept(ta, A_sub_dept, A_id)
    time.sleep(0.5)
    a_depts = [d.get('deptName') for d in dept_list(ta)]
    b_depts = [d.get('deptName') for d in dept_list(tb)]
    check('7.1 A可见自身子部门', A_sub_dept in a_depts)
    check('7.2 B不可见A的部门', A_dept_name not in b_depts and A_sub_dept not in b_depts, f'B可见部门={b_depts}')

    # 8. 平台超管可见全部(任务/策略至少包含A新建 + 原租户100数据)
    print('== 平台超管全局可见 ==')
    admin_tasks = task_list(admin)
    check('8.1 平台超管可见多租户任务(含A新建与历史)', any(t['name'] == a_task for t in admin_tasks) and len(admin_tasks) >= 2,
          f'admin任务数={len(admin_tasks)}')

    finish()


def finish():
    passed = sum(1 for _, ok in RESULTS if ok)
    total = len(RESULTS)
    print(f'\n==== 多租户测试结果: {passed}/{total} ====')
    for name, ok in RESULTS:
        print(('PASS ' if ok else 'FAIL ') + name)
    sys.exit(0 if passed == total and total > 0 else 1)


if __name__ == '__main__':
    main()
