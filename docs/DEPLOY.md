# ezdata 部署指南

> 适用分支:`v2.0`。本文反映**当前实际部署形态**(容器-per-service,无 supervisord;Scheduler 进程内;ES8 + MinIO 已纳入 compose;调试层沙箱已就位)。
> 一句话:开发用 `docker-compose.dev.yml` 一键起;生产用 `docker-compose.my.yml`(MySQL)或 `docker-compose.pg.yml`(PostgreSQL)。

---

## 1. 架构概览

容器-per-service,纤巧镜像(`python:3.10` / `node:18`),后端单进程内跑 FastAPI + APScheduler(启动锁选主,多副本时只一个实例调度),Celery worker 独立容器执行任务。

```
        :12580 ──► frontend (nginx / vite)
                       │ 反代 /dev-api
        :9099  ──► backend (uvicorn FastAPI + 进程内 APScheduler)
                  ┌────┼─────────┬───────────┐
              worker  redis     mysql/pg     ├── elasticsearch  (任务日志 + RAG 向量库 + ES 数据服务,一套三用)
             (celery) broker   主数据库       └── minio          (对象存储,S3 协议)

dev/prod: sandbox(调试态代码执行,无状态隔离容器) ── egress-proxy(出网域名白名单)
```

| service | 镜像/构建 | 作用 | dev | prod(my/pg) |
|---|---|---|:--:|:--:|
| frontend | `web/Dockerfile`(node→nginx)/ vite | 前端 | ✅ | ✅ |
| backend | `api/Dockerfile.dev` / `.my` / `.pg` | API + 进程内调度 | ✅ | ✅ |
| worker | 复用 backend 镜像 | Celery 任务执行 | ✅ | ✅ |
| mysql / postgres | `mysql:8.0` / `postgres:14` | 主库 | ✅ | ✅ |
| redis | `redis:latest` | broker / 缓存 / 验证码 | ✅ | ✅ |
| elasticsearch | `elasticsearch:8.13.4` | 日志 + 向量库 + 数据服务 | ✅ | ✅ |
| minio + minio-init | `minio/minio` + `minio/mc` | 对象存储 + 建桶 | ✅ | ✅ |
| sandbox | 复用 backend 镜像 | 调试态代码执行(隔离) | ✅ | ✅ |
| egress-proxy | tinyproxy | 沙箱出网白名单 | ✅ | ✅ |

> **沙箱**:三套 compose(dev / my / pg)均已部署沙箱 + egress 并 `SANDBOX_ENABLED=true`。沙箱跑在内网专用网络(`internal=true`,无直连公网),出网只经 egress-proxy 的域名白名单。非容器 / 自定义部署若未起沙箱,把 `SANDBOX_ENABLED` 置空即回落本地真实执行(详见 [9.4](#94-调试态代码执行))。

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

生产应用口令烤进镜像的 `.env.docker{my,pg}`(`ruoyi app run --env=dockermy/pg`),compose 仅覆盖中间件 host 为服务名。

```bash
# MySQL 版
docker compose -f docker-compose.my.yml up -d --build

# PostgreSQL 版
docker compose -f docker-compose.pg.yml up -d --build
```

- 前端 `http://<宿主>:12580`,后端 `http://<宿主>:19099`(注意 prod 后端宿主端口是 **19099**)。
- 首启同样自动导入 `api/sql/ezdata.sql` / `ezdata-pg.sql` + 建 MinIO 桶。
- **上线前务必**:① 改默认口令(见 [10](#10-安全加固));② 把 `STORAGE_PUBLIC_ENDPOINT` 改成浏览器可达的真实域名/宿主 IP;③ 填好 `JWT_SECRET_KEY`、LLM/embedding 的 API Key。

---

## 4. 端口 & 默认账号口令

| 用途 | dev(宿主) | prod(宿主) |
|---|---|---|
| 后端 API | 9099 | **19099** |
| 前端 | 12580 | 12580 |
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

- 后端按 `APP_ENV` 加载 `api/.env.<APP_ENV>`:dev=`.env.dev`,prod=`.env.dockermy`/`.env.dockerpg`(由 `Dockerfile.my/.pg` 的 `--env=` 指定)。
- **compose 的 `environment:` 优先于 `.env`**(`load_dotenv` 不覆盖已存在环境变量)。dev compose 用它把 `.env.dev` 里指向 `127.0.0.1` 的连接覆盖成服务名,并注入统一口令 / ES·RAG 鉴权。
- `.env.dev` 被 git 忽略(只跟踪 `.env.dev.example`);`.env.dockermy`/`.env.dockerpg`/`.env.prod` 被跟踪。**不要把真实密钥提交进仓库**。

关键变量:

| 变量 | 含义 |
|---|---|
| `DB_TYPE` / `DB_HOST` / `DB_DATABASE` / `DB_USERNAME` / `DB_PASSWORD` | 主库连接 |
| `REDIS_HOST` / `REDIS_PASSWORD` / `REDIS_DATABASE` | Redis(broker / 缓存);Celery broker URL 自动带密 |
| `TASK_LOG_TYPE=es` + `TASK_ES_HOSTS` / `TASK_ES_USERNAME` / `TASK_ES_PASSWORD` | 任务日志写 ES |
| `RAG_VECTOR_BACKEND` / `RAG_VECTOR_HOSTS` / `RAG_VECTOR_USER` / `RAG_VECTOR_PASSWORD` | RAG 向量库(hosts 留空回退 `TASK_ES_HOSTS`,**但账号不回退,需单独给**) |
| `STORAGE_TYPE=s3` + `S3_ENDPOINT` / `S3_BUCKET_NAME` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `STORAGE_PUBLIC_ENDPOINT` | 对象存储(MinIO) |
| `EMBEDDING_TYPE` / `EMBEDDING_MODEL` / `DASHSCOPE_API_KEY` | 知识库 embedding |
| `JWT_SECRET_KEY` | 令牌签名(prod 必填) |
| `SANDBOX_ENABLED` / `SANDBOX_API_URL` / `SANDBOX_BEARER_KEY` | 调试态代码执行沙箱 |

---

## 6. 数据初始化 & 演示数据

- **建库**:首次启动 DB 容器,把 `api/sql/ezdata.sql`(MySQL)/ `ezdata-pg.sql`(PG)挂到 `/docker-entrypoint-initdb.d`,空库时自动导入(表 / 菜单 / 用户 / 字典 / 配置 / 角色全套种子)。
- **开箱即用演示数据**(种子末尾):
  - 数据源 `akshare_cn`(AKShare 财经,api 族,免 key)
  - 数据源 `demo_es`(内置 ES,search 族;config 已带 `elastic/ezdata123456`)
  - 数据集成任务「A股日线→ES」(手动触发,抓贵州茅台前复权日线写入 ES 索引 `demo_stock_daily`)
- **运行时表**:`ai_sessions` 等由 agno 在首次对话时惰性建,无需预建。

> 非容器部署时,手动把对应 `.sql` 导入你的库即可。

---

## 7. 中间件要点

- **Elasticsearch 8**:开了 `xpack.security`(用户 `elastic`),并 `xpack.security.http.ssl.enabled=false` 保持**明文 HTTP + basic auth**(免证书,适合内网)。`ELASTIC_PASSWORD` **仅在数据目录为空(首次初始化)时生效**;改已存在集群的密码要 `down -v` 清卷或进容器跑 `elasticsearch-reset-password`。
- **Redis**:`--requirepass ezdata123456`,健康检查与 Celery broker 均带密。
- **MinIO**:`minio-init` 一次性容器建 `ezdata` 桶并设匿名下载;改了 root 口令后该容器的 `mc alias` 口令需同步(compose 已同步)。
- **数据源 `demo_es` 的口令**放在 `config`(明文)而非加密 `secrets`——这样静态 SQL 种子即可直连加密 ES。运行无碍;但在 UI 编辑该数据源时密码框会显示为空(handler 仍能连)。生产可在 UI 重填一次密码存进加密 secrets。

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
dev 源码挂载,改完代码后端自动 reload;worker 需 `docker restart ezdata-worker-dev`。prod 改完 `docker compose -f docker-compose.my.yml up -d --build` 重建镜像。

### 9.4 调试态代码执行
平台「调试 / 预览」态的代码(ETL 代码取数、AI 图表等)在沙箱执行(子进程隔离 + 超时/内存 + import 白名单 + 出网域名白名单)。**dev / my / pg 三套 compose 均已部署沙箱并 `SANDBOX_ENABLED=true`**;沙箱出网域名白名单由 egress-proxy 的 `SANDBOX_EGRESS_ALLOW` 控制(默认财经/行情域名,按需增删)。非容器或自定义部署若未起沙箱,置空 `SANDBOX_ENABLED` 即回落 worker/后端本地真实执行。正式任务恒走 worker。

---

## 10. 安全加固(对外部署)

默认 `ezdata123456` 仅供本地/内网。公网或多人环境务必:

- **改强口令**:各中间件用独立强口令;改 `admin` 初始密码。
- **不写死在仓库**:把 compose 里的口令改成 `${MYSQL_ROOT_PASSWORD}` 等占位,值放部署机的 `.env` / secret 管理,不提交。
- **填 `JWT_SECRET_KEY`**:prod 用足够随机的值。
- **收敛暴露面**:数据库 / Redis / ES / MinIO 端口不对公网开放,只暴露前端(和必要的后端 API)。
- **ES TLS**:如需链路加密,改 `xpack.security.http.ssl.enabled=true` 并配证书,客户端 hosts 改 `https://`。
- **沙箱**:三套 compose 已默认部署独立沙箱 + egress 白名单(代码取数/AI 代码执行不裸跑在 worker)。上线务必改 `SANDBOX_BEARER_KEY`(默认 `ezdata-sandbox-prod-key`),并按需收紧 `SANDBOX_EGRESS_ALLOW` 出网域名白名单。

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

---

## 附录:后置 / 可选

- **flower**(Celery 监控):复用 backend 镜像 `celery -A config.celery_app flower`,默认 5555,按需另加 service。
- **K8s / Helm**:工作负载按 backend / worker / frontend 拆分(scheduler 进程内,无独立 Deployment);依赖 mysql/redis/minio/es 子 chart;backend 多副本靠 `server.py` 启动锁保证调度单实例。
