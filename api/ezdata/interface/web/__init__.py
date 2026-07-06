"""ezdata.interface.web:自包含的对外接口 app(轻量 HTTP 服务 + 单页 UI)。

一处集齐(与核心隔离,只演示/对外用):
  sources.py —— 连接目录 CRUD(SQLite,纯标准库);
  core.py    —— 数据 facade:数据管理 / 取数 / AI 取数(NL→查询→执行) / 同步 ETL;
  llm.py     —— LLM 客户端(agno:openai / anthropic,惰性导入);
  config.py  —— 从 env 读 LLM_* 等;
  server.py  —— 标准库 http.server 暴露 JSON API + 托管 static/index.html。

core 保持传输无关(不 import server),将来若加 mcp/cli 可直接复用 `from ...web.core import Core`。
启动见 __main__(python -m ezdata.interface.web)。
"""

from ezdata.interface.web import config
from ezdata.interface.web.core import Core
from ezdata.interface.web.llm import LLMClient, LLMError, strip_code_fence
from ezdata.interface.web.server import make_handler, serve
from ezdata.interface.web.sources import ConnectionStore

__all__ = [
    'ConnectionStore',
    'Core',
    'LLMClient',
    'LLMError',
    'config',
    'make_handler',
    'serve',
    'strip_code_fence',
]
