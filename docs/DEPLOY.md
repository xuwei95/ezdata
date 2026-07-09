# ezdata 部署指南

> 适用分支:`v2.0`。本文反映**当前实际部署形态**(容器-per-service,无 supervisord;Scheduler 进程内;ES8 + MinIO 已纳入 compose;调试层沙箱已就位)。
> 一句话:开发用 `docker-compose.dev.yml` 一键起;生产用 `docker-compose.yml`(默认 MySQL,`--env-file .env.pg` 切 PostgreSQL)。

---

## 1. 架构概览

容器-per-service,纤巧镜像(`python:3.10` / `node:18`),后端单进程内跑 FastAPI + APScheduler(启动锁选主,多副本时只一个实例调度),Celery worker 独立容器执行任务。生产 my/pg 二合一为**单个 `docker-compose.yml`**,配置由**同目录单份 `.env`** 统一驱动(见 [5. 配置](#5-配置))。

```
                              宿主 :80                                 :19099
                                │                                        │
  浏览器 ───────────────►  ezdata-frontend (nginx + Vue 静态)             │(后端直连调试口,可不暴露)
                                │  location /       → SPA                 │
                                │  location /api/   → 反代后端(剥 /api)  │
                                ▼                                        ▼
                          ezdata-backend (uvicorn FastAPI + 进程内 APScheduler 选主)
                                │
            ┌───────────┬───────┼──────────────┬──────────────────┐
            ▼           ▼       ▼              ▼                  ▼
       ezdata-mysql  ezdata-  ezdata-es    ezdata-minio       ezdata-worker (celery)
       /-pg(主库,   redis    (任务日志 +    (S3 对象存储,      复用后端镜像,执行
        命名卷持久) broker/   RAG 向量库 +   命名卷持久)         DataIntegration/Python/DAG
                    缓存/     ES 数据服务,                       任务,租户随任务带入)
                    验证码     一套三用,卷持久)

   调试态「运行代码 / AI 取数」─► ezdata-sandbox(无状态隔离执行器,仅 internal 网)
                                       │ 出网仅经
                                       ▼
                                ezdata-egress-proxy(tinyproxy 域名白名单)

   ezdata-db-backup(DB 定时备份 sidecar,默认在 compose 里注释关闭,见 10.1)
```

**两张网络(隔离关键)**:

| 网络 | 类型 | 成员 |
|---|---|---|
| `ezdata-network` | bridge(有 NAT/公网) | frontend / backend / worker / mysql / redis / es / minio / egress-proxy |
| `ezdata-sandbox-net` | **`internal=true`(无直连公网)** | sandbox / egress-proxy / backend·worker(调沙箱)/ mysql·es·minio(供沙箱经内网取数) |

沙箱只在 internal 网、自身无公网,出网必经 egress-proxy 域名白名单(`SANDBOX_EGRESS_ALLOW`),且 `cap_drop ALL + no-new-privileges + pids/mem 限额`;不内置任何 DB/JWT 凭据,执行所需随请求注入、用完即弃。

| service | 镜像/构建 | 作用 | dev | prod |
|---|---|---|:--:|:--:|
| frontend | `web/Dockerfile`(node→nginx)/ vite | 前端 + 反代 `/api` | ✅ | ✅ |
| backend | `api/Dockerfile.dev` / `.my` / `.pg` | API + 进程内调度 | ✅ | ✅ |
| worker | 复用 backend 镜像 | Celery 任务执行 | ✅ | ✅ |
| mysql / postgres | `mysql:8.0` / `postgres:14` | 主库(命名卷持久) | ✅ | ✅ |
| redis | `redis:latest` | broker / 缓存 / 验证码 / 选主锁 / 日志流 | ✅ | ✅ |
| elasticsearch | `elasticsearch:8.13.4` | 日志 + 向量库 + 数据服务(卷持久) | ✅ | ✅ |
| minio + minio-init | `minio/minio` + `minio/mc` | 对象存储 + 建桶(卷持久) | ✅ | ✅ |
| sandbox | 复用 backend 镜像 | 调试态代码执行(隔离) | ✅ | ✅ |
| egress-proxy | tinyproxy | 沙箱出网白名单 | ✅ | ✅ |
| db-backup | 复用 DB 镜像 | DB 定时备份(**默认关闭**) | — | 可选 |

> **沙箱**:dev compose 与生产 `docker-compose.yml`(my / pg)均已部署沙箱 + egress 并 `SANDBOX_ENABLED=true`。非容器 / 自定义部署若未起沙箱,把 `SANDBOX_ENABLED` 置空即回落本地真实执行(详见 [9.4](#94-调试态代码执行))。
>
> **API 前缀**:生产经 nginx `/api/` 反代到后端(`APP_ROOT_PATH=/api`、前端 `VITE_APP_BASE_API=/api`);dev 走 `/dev-api`。GitHub SSO 回调即 `http://<host>/api/oauth/github/callback`。

---

## 2. 快速开始 —— 开发

```bash
# 1) 准备环境变量(必需:.env.dev 被 git 忽略,缺失会让后端回退到默认库名连不上)
cp api/.env.dev.example api/.env.dev

# 2) 一键起(backend + worker + frontend + mysql + redis + es + minio + sandbox + egress)
docker compose -f docker-compose.dev.yml up -d

# 看日志 / 停止 / 彻底清库重来
docker compose -f docker-compose.dev.yml logs -f ezdata-backend-dev
docker compose -f docker-compose.dev.yml down          # 停,保留数据卷
docker compose -f docker-compose.dev.yml down -v       # 停,并清空所有数据卷(全新初始化用)
```

- 源码 `./api`、`./web` 挂载进容器:改 `.py` 触发后端热重载(`--reload`,Windows 已开 `WATCHFILES_FORCE_POLLING`),改 `.vue/.js` 触发前端 HMR。
- 首次起 MySQL 容器会自动导入 `api/sql/ezdata.sql`(空库时执行),MinIO init 容器自动建 `ezdata` 桶。
- 访问前端 `http://localhost:12580`,用 **`admin` / `admin123`** 登录。

---

## 3. 快速开始 —— 生产

生产应用口令烤进镜像的 `.env.docker{my,pg}`(`ruoyi app run --env=dockermy/pg`),compose 仅覆盖中间件 host 为服务名。MySQL / PostgreSQL 二合一在同一个 `docker-compose.yml`:默认 MySQL,`.env.pg` 一次性翻所有 PG 变量(镜像/容器名/库引擎)。所有可调项见 `.env.example`。

```bash
# MySQL 版(默认,零配置)
docker compose up -d --build

# PostgreSQL 版(一个 flag)
docker compose --env-file .env.pg up -d --build
```

- 前端 `http://<宿主>`(prod 映射宿主 **80** 端口),后端 `http://<宿主>:19099`(注意 prod 后端宿主端口是 **19099**)。
- 首启同样自动导入 `api/sql/ezdata.sql` / `ezdata-pg.sql` + 建 MinIO 桶。
- **上线前务必**:① 改默认口令(见 [10](#10-安全加固));② 把 `STORAGE_PUBLIC_ENDPOINT` 改成浏览器可达的真实域名/宿主 IP;③ 填好 `JWT_SECRET_KEY`、LLM/embedding 的 API Key。

---

## 4. 端口 & 默认账号口令

| 用途 | dev(宿主) | prod(宿主) |
|---|---|---|
| 后端 API | 9099 | **19099** |
| 前端 | 12580 | 80 |
| MySQL / PG | 13306 / 15432 | 13306 / 15432 |
| Redis | 16379 | 16379 |
| Elasticsearch | 9200 | 9200 |
| MinIO API / 控制台 | 9000 / 19001 | 9000 / 19001 |
| Scheduler | 进程内(无端口) | 进程内 |
| Sandbox | 8003(容器内网) | 8003(容器内网) |

**默认登录**:`admin` / `admin123`(另有测试用户 `test`)。

**默认中间件口令**(dev / prod compose 已统一为 `ezdata123456`,仅供本地 / 内网):

| 组件 | 用户名 | 口令 |
|---|---|---|
| MySQL | `root` | `ezdata123456` |
| PostgreSQL | `postgres` | `ezdata123456` |
| Redis | — | `ezdata123456` |
| MinIO | `minio` | `ezdata123456` |
| Elasticsearch | `elastic` | `ezdata123456` |

> ⚠️ 这是一套已知弱口令,**只适合本地 / 隔离内网**。对外部署见 [10](#10-安全加固)。

---

## 5. 配置

**两层 + 单文件**:

- **应用层**:后端按 `APP_ENV` 加载镜像内 `api/.env.<APP_ENV>`(dev=`.env.dev`,prod=`.env.dockermy`/`.env.dockerpg`,由 `Dockerfile.my/.pg` 的 `--env=` 指定),作为缺省兜底。
- **单份 `.env` 覆盖**:与 `docker-compose.yml` 同目录的 `.env` 既做 compose 插值(镜像/端口/容器名/基础设施口令),又经 backend/worker 的 `env_file` 注入容器 → **其值覆盖镜像内 `.env.<env>`**(因 `load_dotenv` 不覆盖已存在环境变量,即 compose 注入优先)。故改口令/密钥只需改这一份;`env_file` 为 `required:false`,不建 `.env` 也能零配置起。
- 宿主端口用 `*_HOST_PORT`(如 `DB_HOST_PORT`),与应用连接端口(`DB_PORT=3306` 等)分开,避免单文件注入时撞名。
- **Secrets 不入库**:`.env`、`api/.env.dev`、`api/.env.dockermy`/`.dockerpg`/`.prod`、`docker-compose.override.yml` 均 git 忽略,仓库只跟踪脱敏的 `.example`。强随机密钥用 `python deploy/gen-secrets.py --env dockermy` 一键生成(同时写对齐的 `.env` 与 `api/.env.dockermy`)。**勿提交真实密钥**。
- 跨命名但须同值:ES(`ELASTIC_PASSWORD`=`TASK_ES_PASSWORD`=`RAG_VECTOR_PASSWORD`)、MinIO(`MINIO_ROOT_USER`=`S3_ACCESS_KEY`,`MINIO_ROOT_PASSWORD`=`S3_SECRET_KEY`)——详见根目录 `.env.example`。

关键变量:

| 变量 | 含义 |
|---|---|
| `DB_TYPE` / `DB_HOST` / `DB_DATABASE` / `DB_USERNAME` / `DB_PASSWORD` | 主库连接 |
| `REDIS_HOST` / `REDIS_PASSWORD` / `REDIS_DATABASE` | Redis(broker / 缓存);Celery broker URL 自动带密 |
| `TASK_LOG_TYPE=es` + `TASK_ES_HOSTS` / `TASK_ES_USERNAME` / `TASK_ES_PASSWORD` | 任务日志写 ES |
| `RAG_VECTOR_BACKEND` / `RAG_VECTOR_HOSTS` / `RAG_VECTOR_USER` / `RAG_VECTOR_PASSWORD` | RAG 向量库(hosts 留空回退 `TASK_ES_HOSTS`,**但账号不回退,需单独给**) |
| `STORAGE_TYPE=s3` + `S3_ENDPOINT` / `S3_BUCKET_NAME` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `STORAGE_PUBLIC_ENDPOINT` | 对象存储(MinIO) |
| `EMBEDDING_TYPE` / `EMBEDDING_MODEL` / `DASHSCOPE_API_KEY` | 知识库 embedding |
| `LLM_TYPE` / `LLM_MODEL` / `LLM_API_KEY` / `LLM_URL` | 系统兜底 AI 模型。**内部 AI 生成(ETL AI 取数/转换、数据查询)优先用它**——这些入口没有选模型 UI,统一走兜底,不会被库内某个未配好 key 的模型带跑;兜底未配置才回退库内启用模型。对话/应用的 `modelId=0` 也用它 |
| `LLM_REASONING` / `LLM_SUPPORT_IMAGES` | 兜底模型是否为深度思考 / 多模态模型(`true` 才放开思考内容展示 / 图片输入)。**推理模型首个 token 前有思考延迟(几秒),AI 生成"看着卡一下"属正常;要秒出改用 Instruct 类非推理模型并置 `false`** |
| `CELERY_TASK_SOFT_TIME_LIMIT` / `CELERY_TASK_TIME_LIMIT` | 任务全局超时(秒,默认 `1800`/`2100`)。软超时抛异常→标记失败并告警;硬超时 `SIGKILL` 卡死子进程、释放槽位。任务级 `timeout` 可覆盖:`0`=用此默认、`-1`=不限(流式/超长)、`>0`=自定义 |
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | 每 worker 一次预取的任务数(默认 `1`)。`1` = 慢/卡任务不连累其预取的其它任务,减少队列堵塞 |
| `TZ` / `SCHEDULER_TZ` | 容器时区 / 调度器时区,**默认均 `Asia/Shanghai`**。容器默认 UTC 会让 cron 的"9-15 点"跑到北京 17-23 点,故务必保持北京时区(见 [7.1](#71-定时任务时区)) |
| `JWT_SECRET_KEY` | 令牌签名(prod 必填) |
| `DATA_ENCRYPT_KEY` | 库内数据源/AI 凭据 AES 加密(与 JWT 分离;留空回退由 JWT 派生,兼容旧密文) |
| `SANDBOX_ENABLED` / `SANDBOX_API_URL` / `SANDBOX_BEARER_KEY` | 调试态代码执行沙箱 |
| `GITHUB_SSO_ENABLED` / `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` / `GITHUB_REDIRECT_URI` | GitHub SSO 登录(回调 `…/api/oauth/github/callback`,详见 [10.2](#102-github-sso-登录)) |

---

## 6. 数据初始化 & 演示数据

- **建库**:首次启动 DB 容器,把 `api/sql/ezdata.sql`(MySQL)/ `ezdata-pg.sql`(PG)挂到 `/docker-entrypoint-initdb.d`,空库时自动导入(表 / 菜单 / 用户 / 字典 / 配置 / 角色全套种子)。
- **默认是干净的空项目**:种子只含平台基础数据,不含任何演示数据源 / 任务。
- **运行时表**:`ai_sessions` 等由 agno 在首次对话时惰性建,无需预建。

### 6.1 可选:加载财经演示数据(akshare → ES + AI 分析助手)

想要一套开箱即用的财经 demo,**服务起来后手动跑一次脚本即可**(无需改源码 / 重建镜像):

```bash
# 在仓库根目录执行(脚本经 stdin 喂入容器,镜像里无需有此文件)
docker exec -i ezdata-backend-my python - < api/demo_seed.py
```

它会(幂等,可重复跑;**只影响 demo 命名空间,不碰用户/权限/其他数据**):

- 建 2 个数据源:`akshare_cn`(免 key 财经)、`demo_es`(内置 ES)
- 建 **27 个数据集成任务** + 27 个数据模型(A股/港股/美股快照、日线、涨停池、龙虎榜、概念/行业板块、技术选股、业绩、宏观 GDP/LPR、新闻等),并**派发到 Celery 异步执行**,约 2-3 分钟把数据填进 `demo_es` 的 `fin_*` 索引
- 建 1 个 AI 应用「财经数据分析助手」(app_id=9001,已绑数据源 + 取数/绘图工具)
- 定时任务用 **7 段 Quartz** cron(秒 分 时 日 月 周 年),盘中任务按**北京时间**(见 [7.1 时区](#71-定时任务时区)),周一到周五=`2-6`,步进用 `0/N`,与前端 cron 组件一致
- 跑完自动向运行中的调度器 `PUBLISH scheduler:sync:request` **触发即时重载**(打印 `✅ 已通知…无需重启`);若打印 `⚠️ 未检测到在监听的调度器`(多为镜像旧),则 `docker restart ezdata-backend-my` 激活

> **要让 AI 助手能对话出图,需先配大模型**:设环境变量 `LLM_TYPE` / `LLM_MODEL` / `LLM_API_KEY`(应用 `model.modelId=0` 走此兜底),或在「AI 模型管理」启用一个对话模型。若用**深度思考**模型(如 DeepSeek-V4/R1),再设 `LLM_REASONING=true` 才会展示思考过程。数据 ETL 与查询不依赖大模型。

> 非容器部署时,手动把对应 `.sql` 导入你的库;演示数据同样跑 `python demo_seed.py`(在 api 目录、加载好应用 env 后)。

---

## 7. 中间件要点

- **Elasticsearch 8**:开了 `xpack.security`(用户 `elastic`),并 `xpack.security.http.ssl.enabled=false` 保持**明文 HTTP + basic auth**(免证书,适合内网)。`ELASTIC_PASSWORD` **仅在数据目录为空(首次初始化)时生效**;改已存在集群的密码要 `down -v` 清卷或进容器跑 `elasticsearch-reset-password`。
- **Redis**:`--requirepass ezdata123456`,健康检查与 Celery broker 均带密。
- **MinIO**:`minio-init` 一次性容器建 `ezdata` 桶并设匿名下载;改了 root 口令后该容器的 `mc alias` 口令需同步(compose 已同步)。
- **数据源 `demo_es` 的口令**放在 `config`(明文)而非加密 `secrets`——这样静态 SQL 种子即可直连加密 ES。运行无碍;但在 UI 编辑该数据源时密码框会显示为空(handler 仍能连)。生产可在 UI 重填一次密码存进加密 secrets。

### 7.1 定时任务时区

- **两层默认东八区**:① 镜像内置 `ENV TZ=Asia/Shanghai`(`api/Dockerfile.{dev,my,pg}`)——**默认即北京时间**,任何跑法(dev/prod/非 compose)都不回退 UTC;② dev 与 prod compose 均给 backend/worker 注入 `TZ=${TZ:-Asia/Shanghai}`(宿主 `TZ` 可覆盖),不重建镜像即刻生效。两者统一容器 `date`/日志/`datetime.now()`。
- 调度器(APScheduler)另按 **`SCHEDULER_TZ`(默认 `Asia/Shanghai`)** 解释 cron,并把时区**显式注入每个 trigger**(不依赖容器 TZ);Celery `timezone` 同为 `Asia/Shanghai`。
- **为何重要**:容器若为 UTC,naive `datetime.now()`(create_time/日志时间戳)会慢 8 小时;且 cron 的 `hour=9-15`(意为北京交易时段)会在 **UTC 9-15 = 北京 17-23 点**触发 → 白天看着"定时任务完全不触发"。上述两层默认已消除该问题;老镜像 `docker compose pull` / 重建后落地。
- **cron 格式**:7 段 Quartz `秒 分 时 日 月 周 年`,与前端 cron 生成器一致 —— **步进用 `0/N`**(非 `*/N`,否则组件显示 NaN);**星期用数字**(Quartz 周日=1..周六=7,周一到周五=`2-6`,别用名称/0);**年写 `*`**;日与星期二选一(定了星期则日写 `?`)。例:交易时段每5分钟 `0 0/5 9-15 ? * 2-6 *`。后端会把 Quartz 数字星期自动转成 APScheduler 约定。
- 非法 cron 在**创建/编辑时即被拒绝**(fail-fast 校验);即使存量脏数据,同步时也只跳过那一条、不影响其它任务与调度器。

### 7.2 任务超时(防卡死堵塞)& 重启调度器

- **超时**:任务默认受全局软/硬超时约束(`CELERY_TASK_SOFT_TIME_LIMIT`/`CELERY_TASK_TIME_LIMIT`,默认 1800/2100 秒)。软超时→标记失败并告警(不重试,重试大概率仍超时);硬超时→`SIGKILL` 卡死子进程、释放 worker 槽位,prefork 自动补新子进程。配合 `CELERY_WORKER_PREFETCH_MULTIPLIER=1`,卡死任务不会连累排队任务。
- **任务级 `timeout`**(任务编辑页「超时时间」):`0`=用全局默认、`-1`=**不限**(流式/超长任务必须设 -1,否则会被全局硬超时误杀)、`>0`=自定义秒数(硬超时=软+300)。
- **重启调度器**:调度器若"断"(丢锁、dev 热重载、卡住),在「系统监控 → 定时任务」页点「**重启调度器**」按钮即可 `close→重抢锁→从库重载全部启用任务` 恢复。该按钮权限 `monitor:job:restart` 未分配给普通角色,**默认仅超管可见/可用**。多 worker 时会经 Redis 通道广播,由真正的 leader 执行。
- 注意:重启只**重排库里已启用的任务**,不创建任务、也不立即取数;演示数据初始化仍需手动跑 `demo_seed.py`(见 [6.1](#61-可选加载财经演示数据akshare--es--ai-分析助手))。

---

## 8. 本地(非容器)开发

前置:Python ≥ 3.10、Node ≥ 18,外部已有 MySQL/PG + Redis + ES8 +(可选)MinIO。

```bash
# 后端
cd api
pip install -r requirements.txt          # 基础
pip install -r requirements-data.txt     # ETL / 连接器(dlt 等)
pip install -r requirements-pg.txt       # 用 PG 时
pip install -r requirements-storage.txt  # 用对象存储时
cp .env.dev.example .env.dev             # 改 DB/Redis/ES 等为本机地址,导入 sql/ezdata.sql
python app.py                            # 起 FastAPI(host/port/reload 读 .env)

# Celery worker(另开一个终端,任务调度执行层)
celery -A config.celery_app worker -Q default --autoscale=4,1 --loglevel=INFO

# 前端
cd web
npm install
npm run dev                              # vite,默认 12580
```

> Scheduler 在后端进程内(APScheduler),无需单独起;flower / sandbox 按需另起。

---

## 9. 运维

### 9.1 全新初始化(清库重来)
`docker compose -f docker-compose.dev.yml down -v` 清空 mysql/es/minio 数据卷,再 `up -d` 即重新导入 SQL 种子 + 建桶 + 初始化 ES。

### 9.2 改口令
统一改某个口令时:① 改 compose 对应服务的 root 口令;② 改 `.env.dev`(或 `.env.docker*`)里应用侧连接口令;③ ES/MySQL 等已初始化的需 `down -v` 或用各自的 reset 工具;④ 重启 backend + worker。

### 9.3 升级源码
dev 源码挂载,改完代码后端自动 reload;worker 需 `docker restart ezdata-worker-dev`。prod 改完 `docker compose up -d --build`(PG 加 `--env-file .env.pg`)重建镜像。

### 9.4 调试态代码执行
平台「调试 / 预览」态的代码(ETL 代码取数、AI 图表等)在沙箱执行(子进程隔离 + 超时/内存 + import 白名单 + 出网域名白名单)。**dev compose 与生产 `docker-compose.yml`(my / pg 两种模式)均已部署沙箱并 `SANDBOX_ENABLED=true`**;沙箱出网域名白名单由 egress-proxy 的 `SANDBOX_EGRESS_ALLOW` 控制(默认财经/行情域名,按需增删)。非容器或自定义部署若未起沙箱,置空 `SANDBOX_ENABLED` 即回落 worker/后端本地真实执行。正式任务恒走 worker。

### 9.5 升级已有库(schema 变更)

新功能可能新增列(如任务超时 `task.timeout`)。**全新安装**从 `ezdata.sql`/`ezdata-pg.sql` 建库会自带;**已存在的库不会重跑 SQL**,需补上新列——两种方式(选一):

- **直接改列(单列最省事)**:
  ```bash
  docker exec ezdata-mysql mysql -uroot -p'<库口令>' ezdata -e \
    "ALTER TABLE task ADD COLUMN timeout INT NULL DEFAULT 0 COMMENT '任务超时(秒):0=全局默认,-1=不限,>0=自定义';"
  ```
- **走 alembic 迁移**:本项目库多由 `*.sql` 初始化、**不在 alembic 管控下(无 `alembic_version` 表)**,所以直接 `alembic upgrade head` 会从 baseline 重跑而报错。正确做法是先 `stamp` 到 SQL 对应的版本再升级:
  ```bash
  docker exec -it ezdata-backend-my sh -c "cd /app && alembic stamp 0002_seed_system && alembic upgrade head"
  ```
  之后再有迁移即可正常 `alembic upgrade head`。

> ⚠️ 新代码会查询新列,**先补列、再上带新代码的镜像**(同一维护窗口);列缺失会导致相关查询报错。

**可选:启动时自动迁移** —— 设环境变量 **`AUTO_MIGRATE=true`**(默认关),后端启动时会自动 `alembic upgrade head`,省去手动。对"未纳入 alembic 的库(无 `alembic_version`,由 `*.sql` 建库)"会**先 stamp 基线再 upgrade**:基线由 `AUTO_MIGRATE_BASELINE` 控制(默认 `0002_seed_system`,即 `ezdata.sql` 对应的建表+种子状态)。迁移做了**幂等**(加列/改类型前查存在性),故对全新库(已含新列)、滞后库、已纳管库都安全;迁移失败只记日志、**不阻断启动**。滞后很多的库若基线不是 0002,把 `AUTO_MIGRATE_BASELINE` 设成它实际对应的版本即可。

---

## 10. 安全加固(对外部署)

默认 `ezdata123456` 仅供本地/内网。公网或多人环境务必:

- **一键生成强随机密钥**:`python deploy/gen-secrets.py --env dockermy`(或 `deploy/gen-secrets.sh --env dockermy`)。它生成并写入 `api/.env.dockermy`(JWT 密钥、数据加密密钥、传输层 RSA 公私钥、各中间件强随机口令、沙箱 key)与根 `.env`(compose 基础设施口令,二者对齐)。改完 `admin` 初始密码。
- **secrets 不入库**:`api/.env.prod`/`.env.dockermy`/`.env.dockerpg` 已 `gitignore`,仓库只留 `.example` 模板。生产请用 gen-secrets 生成或外部 secret 注入,切勿提交真实密钥。
- **数据加密密钥与 JWT 分离**:库内数据源/AI 凭据的 AES 加密用独立 `DATA_ENCRYPT_KEY`(留空才回退由 JWT 派生)。轮换 JWT 不影响已加密数据;`MultiFernet` 兼容旧密文,换 `DATA_ENCRYPT_KEY` 后下次保存即用新密钥重写。
- **收敛暴露面**:数据库 / Redis / ES / MinIO 端口不对公网开放,只暴露前端(和必要的后端 API)。
- **ES TLS**:如需链路加密,改 `xpack.security.http.ssl.enabled=true` 并配证书,客户端 hosts 改 `https://`。
- **沙箱**:compose 已默认部署独立沙箱 + egress 白名单(代码取数/AI 代码执行不裸跑在 worker)。上线务必改 `SANDBOX_BEARER_KEY`(默认 `ezdata-sandbox-prod-key`),并按需收紧 `SANDBOX_EGRESS_ALLOW` 出网域名白名单。
- **多租户默认拒绝**:HTTP 请求作用域内空租户上下文一律拒绝(不再 fail-open 看全库);对外数据接口的 `data_api` apikey 强制绑定 `ref_id`。无部门用户需先分配部门(决定租户)才能访问数据。

### 10.1 数据库备份 / 恢复

> ⚠️ `ezdata-db-backup` sidecar **默认关闭**(在 `docker-compose.yml` 中已注释)。需要定时备份时,取消该服务整段注释 + 取消 `volumes` 段 `ezdata-db-backup-data` 的注释,再 `docker compose up -d`。

启用后:按 `BACKUP_INTERVAL_SECONDS`(默认 24h)`mysqldump`/`pg_dump` → gzip 到命名卷 `ezdata-db-backup-data:/backups`,保留最近 `BACKUP_KEEP`(默认 7)份。

```bash
# 启用 sidecar 后:立即手动备份 / 列出 / 恢复(⚠️ 恢复会覆盖现有库)
docker exec ezdata-db-backup sh /scripts/backup.sh
docker exec ezdata-db-backup sh -c 'ls -lh /backups'
docker exec -e DB_PASSWORD=<库口令> ezdata-db-backup sh /scripts/restore.sh /backups/ezdata_mysql_YYYYmmdd_HHMMSS.sql.gz

# 未启用 sidecar 时:一次性容器手动备份到宿主 ./backups
docker run --rm --network ezdata-network -v "$(pwd)/deploy/backup:/scripts:ro" -v "$(pwd)/backups:/backups" \
  -e DB_HOST=ezdata-mysql -e DB_USER=root -e DB_PASSWORD=<库口令> -e DB_NAME=ezdata \
  mysql:8.0 sh /scripts/backup.sh
```

DB 数据已持久化到命名卷 `ezdata-db-data`(PG 用 `DB_DATA_DIR=/var/lib/postgresql/data`),`docker compose down`(不带 `-v`)不再丢数据——备份与持久化是两回事,持久化始终生效。

### 10.2 GitHub SSO 登录

在 `api/.env.<env>` 配置后启用(见 `.env.*.example` 的 `GITHUB_*` 段):

```
GITHUB_SSO_ENABLED = true
GITHUB_CLIENT_ID = <GitHub OAuth App Client ID>
GITHUB_CLIENT_SECRET = <Client Secret>
GITHUB_REDIRECT_URI = https://<域名>/api/oauth/github/callback   # 须与 OAuth App 回调一致
GITHUB_SSO_FRONTEND_URL = https://<域名>/sso-callback
GITHUB_ALLOWED_ORG =                     # 可选:仅限该 GitHub 组织成员
GITHUB_SSO_AUTO_CREATE = true            # 首登自动建号
GITHUB_SSO_DEFAULT_ROLE_KEY = common     # 新用户默认角色
GITHUB_SSO_DEFAULT_DEPT_ID = 100         # 新用户默认部门(决定租户)
```

流程:登录页「使用 GitHub 登录」→ 后端 `/oauth/github/authorize`(带 state 防 CSRF)→ GitHub 授权 → `/oauth/github/callback`(校验 state、换取资料、按 `sys_user_oauth` 绑定/邮箱匹配/自动建号)→ 签发 JWT → 回跳前端 `/sso-callback`。`sys_user_oauth` 表由启动 `create_all` 自动建。

---

## 11. 故障排查

| 现象 | 原因 / 处理 |
|---|---|
| 后端起不来、连 `ruoyi-fastapi` 之类的库 | 没 `cp .env.dev.example .env.dev`,回退到默认库名。补上再重启。 |
| ES 改了 `ELASTIC_PASSWORD` 但仍旧密码 | 该变量只在 ES 数据目录为空时生效。`down -v` 清卷,或进容器 `elasticsearch-reset-password`。 |
| 控制台 / 用量统计页报 `ai_sessions doesn't exist` | 全新环境未对话过,该表尚未由 agno 建。已做空值兜底;发一条对话即建表。 |
| `down -v` 时报 `network ... has active endpoints` | Docker 残留端点。`docker network prune -f`;仍不行重启 Docker。不影响下次 `up`。 |
| 前端能开但接口 401/跨域 | 检查 nginx 反代(prod `web/bin/nginx.docker*.conf`)/ vite 代理目标(dev `VITE_DEV_PROXY_TARGET`)。 |
| worker 不执行任务 | 看 `ezdata-worker-dev` 日志是否 Redis `NOAUTH/WRONGPASS`(口令不一致)或队列名不在 `CELERY_QUEUES`。 |
| 任务卡死 / 队列堵塞 | 已内置超时:全局软/硬超时(`CELERY_TASK_*`,默认 1800/2100)+ 任务级 `timeout`,硬超时会 `SIGKILL` 卡死子进程释放槽位;`prefetch=1` 防连累排队任务(见 [7.2](#72-任务超时防卡死堵塞--重启调度器))。流式/超长任务须把任务 `timeout` 设 `-1`,否则会被全局硬超时误杀。调度器卡住可在「系统监控-定时任务」点「重启调度器」(超管)。存量库先补 `task.timeout` 列(见 [9.5](#95-升级已有库schema-变更))。 |
| AI 取数/转换报 `AIMLAPI_API_KEY not set` 之类 provider key 报错 | 「AI 模型管理」里有个启用中的模型没配 key,被内部 AI 生成挑中。现已改为**内部 AI 生成一律走系统兜底模型(`LLM_*`)**;确认 `LLM_TYPE/LLM_MODEL/LLM_API_KEY` 配好即可,或停用/补全那条库内模型。 |
| 定时任务"完全不触发" | ①时区:容器 UTC 而 cron 按北京时段写 → 跑到北京 17-23 点。用新镜像(`SCHEDULER_TZ=Asia/Shanghai` 已注入 trigger)即修,老镜像 `docker compose pull`。②跑了 `demo_seed` 没重载:新镜像会自动 `PUBLISH` 触发;否则 `docker restart ezdata-backend-my`(调度器仅在后端启动时读 sys_job)。日志 `next run at ... UTC` 是时区没对的铁证。 |
| cron 生成器里"分/时"显示 `NaN/x` | 表达式用了 `*/N` 步进,组件按 `0/N` 解析 → `Number('*')=NaN`。改成 `0/N`(如每5分钟 `0/5`)。 |

---

## 附录:后置 / 可选

- **前端镜像轻量重建**(可选,`docker build` 跑 vite 时 OOM/把 Docker Desktop 跑崩的规避法):把"跑 vite"和"打镜像"拆开——在装好 `node_modules` 的构建容器里 `docker exec` 跑 `npm run build:docker` 产出 `dist`,`docker cp` 出来后再用只 `COPY dist` 的极简 nginx 镜像打包(不在 buildkit 里跑 vite)。资源受限的 Windows/WSL2 上尤其稳;Linux 原生 Docker 一般直接 `docker compose build ezdata-frontend` 即可。
- **flower**(Celery 监控):复用 backend 镜像 `celery -A config.celery_app flower`,默认 5555,按需另加 service。
- **K8s / Helm**:工作负载按 backend / worker / frontend 拆分(scheduler 进程内,无独立 Deployment);依赖 mysql/redis/minio/es 子 chart;backend 多副本靠 `server.py` 启动锁保证调度单实例。
