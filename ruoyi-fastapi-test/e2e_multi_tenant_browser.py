#!/usr/bin/env python3
"""
多租户隔离 - 真实浏览器可视化演示。

用 API 准备两个租户(顶级部门)+各自用户+任务，然后用真实 Chrome 依次以
租户A用户 / 租户B用户 / 平台超管 登录，在「任务管理」「用户管理」页面直观看到：
各租户只看到自己的数据，平台超管看到全部。每步截图到 _e2e_shots/。

用法：
  python e2e_multi_tenant_browser.py            # 默认有界面真实浏览器
  python e2e_multi_tenant_browser.py --headless
"""

import argparse
import os
import time

import e2e_multi_tenant as mt
from e2e_task_alert import Browser

FRONT = 'http://localhost:12580'
SHOTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_e2e_shots')


def setup_tenants():
    """以平台超管(API)准备：租户A/B(顶级部门) + 各自用户 + 任务(A两个,B一个)。返回登录信息。"""
    admin = mt.login('admin', 'admin123')
    ts = time.strftime('%H%M%S')
    A_dept, B_dept = f'演示租户A_{ts}', f'演示租户B_{ts}'
    A_user, B_user = f'demoA_{ts}', f'demoB_{ts}'
    mt.create_dept(admin, A_dept, 0)
    mt.create_dept(admin, B_dept, 0)
    time.sleep(0.5)
    dA = mt.find_dept(admin, A_dept)
    dB = mt.find_dept(admin, B_dept)
    mt.create_user(admin, A_user, dA['deptId'])
    mt.create_user(admin, B_user, dB['deptId'])
    # 各租户用户登录后建任务，体现归属与隔离
    ta = mt.login(A_user, mt.TENANT_PWD)
    tb = mt.login(B_user, mt.TENANT_PWD)
    mt.create_task(ta, f'A任务1_{ts}')
    mt.create_task(ta, f'A任务2_{ts}')
    mt.create_task(tb, f'B任务1_{ts}')
    time.sleep(1)
    print(f'准备完成：租户A={A_dept}(用户{A_user}, 2个任务) / 租户B={B_dept}(用户{B_user}, 1个任务)')
    # 顺序：先租户A/B(吸收首屏冷编译)，平台超管放最后展示「看到全部」
    return {f'租户A({A_user})': ta, f'租户B({B_user})': tb, '平台超管(admin)': admin}


def show(b, label, token, idx):
    """以某用户身份(设置其token)展示任务管理 + 用户管理页面并截图。"""
    safe = label.split('(')[0]
    print(f'\n>>> 当前登录：{label}')
    b.set_cookie('Admin-Token', token, 'localhost')
    # 任务管理
    b.goto_ready(FRONT + '/task/info', '任务名称', timeout=120)
    # 轮询等待列表渲染(首屏 Vite 冷编译较慢)
    tasks = []
    for _ in range(12):
        time.sleep(2)
        tasks = b.ev("[...document.querySelectorAll('tbody tr td:nth-child(2)')].map(x=>x.textContent.trim()).filter(Boolean)")
        rows = b.ev("document.querySelectorAll('tbody tr').length")
        if rows:
            break
    print(f'  任务管理可见任务: {tasks}')
    b.screenshot(os.path.join(SHOTS, f'mt-{idx}a-{safe}-tasks.png'))
    # 用户管理
    b.goto_ready(FRONT + '/system/user', '用户名称', timeout=60)
    time.sleep(3)
    b.screenshot(os.path.join(SHOTS, f'mt-{idx}b-{safe}-users.png'))
    time.sleep(2)  # 留时间肉眼观看


def main():
    global FRONT
    ap = argparse.ArgumentParser()
    ap.add_argument('--headless', action='store_true', help='无界面(默认有界面真实浏览器)')
    ap.add_argument('--backend', default='http://localhost:9099')
    ap.add_argument('--frontend', default=FRONT)
    args = ap.parse_args()
    mt.BACKEND = args.backend
    FRONT = args.frontend
    os.makedirs(SHOTS, exist_ok=True)

    print('== 准备多租户演示数据(API) ==')
    sessions = setup_tenants()

    print('\n== 启动真实浏览器演示 ==')
    b = Browser(headed=not args.headless)
    b.start()
    try:
        for i, (label, token) in enumerate(sessions.items(), 1):
            show(b, label, token, i)
        print('\n演示完成，浏览器将保持 20 秒供观看...')
        time.sleep(20)
    finally:
        b.stop()
    print(f'\n截图已保存到: {SHOTS} (mt-*.png)')


if __name__ == '__main__':
    main()
