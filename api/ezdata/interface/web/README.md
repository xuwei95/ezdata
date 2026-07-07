# ezdata 轻量查数 UI(`ezdata.interface.web`)

与平台核心隔离的**对外接口层**:一个自包含的极简查数工具,脱离整套 web/DB/celery 环境也能跑。
只做几件事:**数据源管理(CRUD)→ 浏览表/字段 → 原生查询(只读护栏)/ AI 取数 → 导出 Excel**。

- UI 用标准库 `http.server`、连接目录用 `sqlite3`、配置用纯标准库解析 —— 除 `ezdata` 核心外,**运行时只需 `SQLAlchemy`(SQL 族)、`pandas/openpyxl`(导出)**;
- AI 取数的 LLM 走 **agno**(暂支持 openai 及一切 OpenAI 兼容端点、anthropic 两族),**惰性导入**——不做 AI 时无需装 agno;
- `ezdata` 核心只管数据、**绝不 import 本层**(依赖箭头单向:interface → core)。

## 目录

```
ezdata/interface/web/
  server.py          # http.server:JSON API + 托管单页 UI(可直接 python server.py 运行)
  __main__.py        # 入口:python -m ezdata.interface.web
  core.py            # 门面:数据管理 / 取数 / AI 取数 / 同步 ETL(传输无关,可复用给 mcp/cli)
  sources.py         # SQLite 连接目录(add/update/remove/list/resolve)
  llm.py             # agno LLM 客户端(openai / anthropic,惰性导入)
  config.py          # 读 .env 的 LLM_* 等(就近发现:本目录 .env > api/.env.dev)
  static/index.html  # 单页前端(原生 JS)
  requirements.txt   # 运行依赖(SQLAlchemy / pandas / openpyxl / agno / openai / anthropic)
  .env.example       # 配置模板
```

## 运行

```bash
# 装依赖(数据源驱动按需再装,如 pip install PyMySQL elasticsearch;页面也能一键 pip 装)
pip install -r requirements.txt

# 配置 LLM:复制 .env.example 为 .env 填好 key(也可用 api/.env.dev,或 EZDATA_ENV_FILE 指定)
cp .env.example .env

# 启动(以下等价,cwd 不限)
python -m ezdata.interface.web           # 在 api/ 下
python server.py                          # 在本目录下(--host 0.0.0.0 --port 9000 可选)
```

浏览器开 `http://127.0.0.1:8077`。

## 配置(见 `.env.example`)

- `LLM_TYPE` / `LLM_API_KEY` / `LLM_URL` / `LLM_MODEL` / `LLM_MAX_TOKENS` / `LLM_REASONING` —— AI 取数用的模型(推理模型首 token 慢,要秒出用 Instruct 类非推理模型)。
- `EZDATA_ENV_FILE` —— 指定 .env 路径;不设时按 `本目录 .env(.dev) → api/.env(.dev)` 就近发现。
- `EZDATA_LOCAL_DB` —— 连接目录 SQLite 路径;默认锚定 `api/ezdata_local.db`(与启动目录无关)。

## 说明

- 连接目录里数据源的密钥以**明文**存本机 SQLite —— 仅适合本地/受信内网;对外部署需自行加密或加鉴权。
- AI「生成查询」是**只生成**:结果在预览区,点「应用到查询框」才覆盖,再点「查询」才执行(不自动跑)。
- Docker 部署可参考 `api/data/`(本地沙箱,已 gitignore)的 `Dockerfile`;构建上下文取 `api/`,`COPY ezdata` 即用同一份核心。
