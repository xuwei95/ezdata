"""ezdata 轻 UI 启动入口。

用法(任选,cwd 不限):
    python -m ezdata.interface.web                 # 在 api/ 下
    python ezdata/interface/web/__main__.py        # 或直接跑本文件
    python __main__.py / python server.py          # 在 interface/web/ 目录下
  可选:--host 0.0.0.0 --port 9000

依赖:ezdata 核心(SQLAlchemy 等,数据源驱动按需装);UI/LLM/连接目录仅用标准库。
LLM 配置:本目录 .env(见 .env.example)> api/.env.dev,或 EZDATA_ENV_FILE 指定;连接目录见 EZDATA_LOCAL_DB。
"""

# 允许直接把本文件当脚本运行(无包上下文时):把 api/ 加进 sys.path,后续 import ezdata 才解析
if __package__ in (None, ''):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # web -> interface -> ezdata -> api

import argparse

from ezdata.interface.web import ConnectionStore, Core, LLMClient, config, serve


def build_core() -> Core:
    """按环境配置装配一个 Core(连接目录 + LLM 客户端)。"""
    store = ConnectionStore(config.DB_PATH)
    return Core(store, LLMClient(config.llm_config()))


def main() -> None:
    ap = argparse.ArgumentParser(description='ezdata 轻 UI(数据管理 / 取数 / AI 取数)')
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', type=int, default=8077)
    args = ap.parse_args()
    print(f'连接目录 SQLite: {config.DB_PATH}')
    serve(build_core(), host=args.host, port=args.port)


if __name__ == '__main__':
    main()
