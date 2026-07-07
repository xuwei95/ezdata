# `ezdata` —— 纯数据访问 SDK

统一接入异构数据源的**无状态数据访问内核**:一套 `Connector` 契约 + 80+ 连接器,把「连数据源 / 列表 / 取字段 / 只读取数 / 写入 / 依赖诊断 / 跨源查询提示词」抽象成与业务无关的库。

**核心零依赖 db / web / config / exec / crypto**:入参一律是「数据源描述」(`source_type` + `config` + 明文 `secrets` dict),不认数据库、租户、加密。谁用它,谁负责先把配置/密钥准备好。平台的 `module_data` 只是它的一个宿主(先查库拿配置、解密 secrets,再调 `ezdata`)。

## 结构

```
ezdata/
  __init__.py     # 顶层导出;只导出核心符号,★绝不 import interface/
  errors.py       # 语义异常(EzDataError 及子类);to_dict() 结构化带出原始报错,便于上报/喂 AI
  handlers/       # 80+ 连接器:懒加载注册表 + 实例缓存,统一 Connector 契约
                  #   每个 *_handler/ 的 __init__ 只暴露轻量元数据(name/family/capabilities/
                  #   connection_args),真正带重依赖(驱动/ORM)的类在 create_handler 时才导入
  services/       # 数据访问门面(供各宿主调用)
      facade.py       # list_source_types / connection_schema / test_connection / list_tables /
                      #   get_columns / query(只读护栏)/ write / get_handler
      prompts.py      # 跨源 NL→查询 提示词构造(SQL 出 SELECT / api 出函数调用 / 其余出原生 DSL)
      secrets.py      # 密文解密器注入点 set_decryptor(核心不含加密实现)
      dependencies.py # 连接器依赖诊断 status() / 安装 install()(唯一带 exec 的能力,独立成模块)
  utils/          # 纯工具:etl_util(只读护栏 assert_readonly_sql / JSON 清洗 json_safe_rows)、
                  #   query(过滤条件 DSL 适配、操作符清单)
  interface/      # ★对外接口层(与核心隔离,核心绝不 import 它,依赖箭头单向):
      web/            # 自包含的轻量查数 UI(标准库 http.server + sqlite 目录 + agno LLM);见其 README
```

## 设计要点

- **能力契约**:每个连接器声明 `family`(rdbms/timeseries/search/vector/kv/graph/file/api…)与 `Capability`(READ/WRITE/EXTRACT/SCHEMA/GEN_API…);facade 调用前先校验能力,不支持则抛 `CapabilityError`。
- **懒加载 + 实例缓存**:发现阶段只 import 轻量元数据(不碰 sqlalchemy/驱动);`create_handler` 才加载重依赖并按「内容哈希 key + LRU + TTL」复用实例/连接池(`cache=False` 旁路,供沙箱/测试隔离)。
- **只读护栏**:`query(..., readonly=True)` 对 SQL 文本族拦截 DML/DDL(`ReadOnlyViolation`);非 SQL 源走各自原生查询。
- **密钥零实现**:核心不含加密。宿主要传「密文 secrets」时用 `ezdata.services.secrets.set_decryptor(fn)` 注入解密函数;CLI/MCP 等直接传明文 dict 即可,不触发本模块。
- **结构化错误**:异常保留原始链(`raise ... from e`),`to_dict()` 带出 `cause_type/cause_message/statement`(默认不含 traceback,省 token),便于日志上报与喂给 AI 改代码。

## 快速用法

```python
from ezdata import services, create_handler

# 元信息(不建连接):已注册源类型 + 能力、连接参数 schema
services.list_source_types()
services.connection_schema('mysql')

# 直接访问(入参 = 源描述;明文 secrets)
cfg = {'host': '127.0.0.1', 'port': 3306, 'user': 'root', 'database': 'demo'}
sec = {'password': '***'}
services.test_connection('mysql', cfg, sec)          # {'success': True, ...}
services.list_tables('mysql', cfg, sec)
services.get_columns('mysql', cfg, sec, table='users')
services.query('mysql', cfg, sec, statement='SELECT * FROM users LIMIT 10')  # 只读护栏

# 依赖诊断 / 安装(连接器的 requirements)
from ezdata.services import dependencies
dependencies.status('mysql')                          # {'requirements', 'missing', 'ready'}
dependencies.install('mysql')                         # 当前解释器 pip 装缺失驱动

# NL → 查询语句(提示词构造;LLM 调用由调用方负责)
from ezdata.services import prompts
h = services.get_handler('mysql', cfg, sec)
prompt = prompts.build_query_prompt(h, ['users'], '统计每个城市的用户数')

# 宿主要传密文 secrets 时(如从库里取到的 AES 密文)
from ezdata.services import secrets
secrets.set_decryptor(lambda ciphertext: my_decrypt(ciphertext))
```

## 三类入口共用

同一份 `ezdata`,不同宿主注入不同实现:

- **平台 web**(`module_data`):查库拿数据源配置 + `set_decryptor` 解密 → 调 `services`;async 场景用 `run_in_threadpool` 包裹(handler 方法是同步阻塞的)。
- **CLI / MCP / skill**:自行构造 `config`/明文 `secrets` 直接调 `services`,无需数据库/加密。
- **`interface/web`**:内置的轻量查数 UI(sqlite 连接目录 + agno LLM),即上面「MCP/CLI 一类」的一个现成实现,可脱离平台单跑。见 `interface/web/README.md`。

> 依赖箭头始终单向:`interface → services/handlers`;核心永不反向 import 接口层,保证 `import ezdata` 干净、可作为纯库嵌入别的项目。
