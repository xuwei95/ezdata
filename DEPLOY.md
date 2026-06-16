# ezdata 部署方案（旧结构 × 新模板 结合）

> 适用分支：`v2.0`（RuoYi-Vue3-FastAPI 模板基底，已 rebrand 为 ezdata、目录重构为 `api/web/tests`）
> 制定日期：2026-06-16
> 决策基线：① Scheduler **进程内**；② Sandbox **暂不保留**；③ ES + MinIO **纳入项目 compose**；④ 弃用 supervisord 胖镜像，采用容器-per-service。

---

## 1. 背景：两套部署模型

### 旧 ezdata（master）
- **单胖镜像** `ezdata123/ezdata`（miniconda3），装下 Flask web / scheduler / celery / sandbox / MindsDB+handlers / ETL。
- **supervisord + env 开关**：`init.sh` 启 supervisord → 跑 `init_system.py`(建库/迁移) → 按 `run_web/run_scheduler/run_worker/run_flower/run_sandbox` 选择性启动进程。
- **同镜像按角色起多容器**：`master`(web+worker) / `scheduler`(scheduler+flower)。
- **中间件**：MySQL + Redis + MinIO + Elasticsearch + nginx。
- **产物**：`api/docker-compose.yml`、`deploy/docker/*`、`deploy/kubernetes/`(Helm)。
- 端口：8001 web / 8002 scheduler / 5555 flower / 9001 supervisor / 9200 ES / 9000·19001 MinIO。

### 新模板（v2.0）
- **纤巧镜像** `python:3.10`，按库分 `Dockerfile.my/pg/dev`；前端多阶段 node→nginx。
- **容器-per-service，无 supervisord**：backend(uvicorn `ruoyi app run`) / worker(celery) / frontend(nginx)。
- **Scheduler 进程内**（lifespan→APScheduler，`server.py` 已有启动锁选主）。
- compose 仅 MySQL + Redis；**无 ES / MinIO / worker(prod) / flower / sandbox**。
- 端口：9099 backend / 12580 frontend / 13306 mysql / 16379 redis。

---

## 2. 目标部署架构（结合后）

**骨架沿用新模板**（容器-per-service + 纤巧镜像 + alembic + CLI 启动），在其上补齐 ezdata 必需件：

```
                         ┌─────────────┐
        :12580  ───────► │  frontend   │  nginx (Element Plus 构建产物)
                         └──────┬──────┘
                                │ /dev-api 反代
                         ┌──────▼──────┐
        :9099   ───────► │   backend   │  uvicorn(FastAPI) + 进程内 APScheduler
                         └──┬───┬───┬──┘
            ┌───────────────┘   │   └───────────────┐
     ┌──────▼──────┐     ┌──────▼──────┐     ┌───────▼───────┐
     │   worker    │     │    redis    │     │     mysql     │
     │  (celery)   │     │ broker/cache│     │   主数据库     │
     └─────────────┘     └─────────────┘     └───────────────┘
            │
   ┌────────┴─────────┐
   ▼                  ▼
┌──────────┐   ┌────────────────┐
│  minio   │   │ elasticsearch  │   ← ezdata 必需中间件（日志/RAG 向量/对象存储）
└──────────┘   └────────────────┘

[暂不部署] scheduler 独立容器（已并入 backend 进程内）、flower、sandbox
```

---

## 3. 服务清单

| service | 镜像/构建 | 启动命令 | 端口(宿主:容器) | 依赖 |
|---|---|---|---|---|
| **frontend** | `web/Dockerfile`(node→nginx) | `nginx -g 'daemon off;'` | 12580:80 | backend |
| **backend** | `api/Dockerfile.my`(+MindsDB/ETL) | `ruoyi app run --env=dockermy`（含进程内 APScheduler） | 19099:9099 | mysql, redis, es, minio |
| **worker** | 复用 backend 镜像 | `celery -A config.celery_app worker -Q default --autoscale=4,1` | — | mysql, redis, es, minio |
| **mysql** | `mysql:8.0` | — | 13306:3306 | — |
| **redis** | `redis:latest` | — | 16379:6379 | — |
| **elasticsearch** | `elasticsearch:7.17.x` | single-node | 9200:9200 | — |
| **minio** | `minio/minio` | `server /data --console-address :19001` | 9000:9000 / 19001:19001 | — |
| ~~scheduler~~ | — | 已并入 backend（进程内 APScheduler，启动锁选主） | — | — |
| ~~flower~~ | 复用 backend 镜像 | `celery -A config.celery_app flower`（可选，后置） | (5555) | redis |
| ~~sandbox~~ | — | 暂不保留（需代码执行能力时再加独立隔离容器） | — | — |

> prod 的 `docker-compose.my.yml`/`.pg.yml` 目前缺 **worker / es / minio**，本方案要补齐；dev 已有 worker，补 es/minio。

---

## 4. 镜像构建改造点（backend）

模板 `Dockerfile.my`（`python:3.10` + `pip install -r requirements.txt`）需补：

```dockerfile
FROM python:3.10
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
# ── ezdata 增量 ──
# 1) MindsDB handler 依赖（内嵌 MindsDB）
ARG MINDSDB_HANDLERS="elasticsearch,clickhouse,influxdb,mongodb,mssql"
ENV MINDSDB_HANDLERS=${MINDSDB_HANDLERS}
RUN python install_handlers.py || echo "部分 handler 安装失败，继续"
# 2) ETL 引擎依赖
RUN pip install --no-cache-dir -r etl/requirements.txt
EXPOSE 9099
CMD ["ruoyi", "app", "run", "--env=dockermy"]
```

注意：
- **base 选型**：先尝试保留 `python:3.10`；若 MindsDB/数据科学依赖出现 conda-only 包，再回退 `continuumio/miniconda3`。
- **运行时 pip upgrade 弃用**：旧 `upgrade_packages=akshare,ccxt` 改为在 `requirements.txt`/`etl/requirements.txt` **钉版本**。
- worker 复用同一镜像，仅启动命令不同。

---

## 5. 中间件纳入 compose（ES + MinIO）

从旧 `deploy/docker/middleware-compose.yml` 搬入，对齐网络与健康检查：

```yaml
  elasticsearch:
    image: elasticsearch:7.17.13          # 与 requirements 的 client 7.17.x 对齐
    environment:
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
      - http.cors.enabled=true
      - http.cors.allow-origin=*
    ports: ["9200:9200"]
    volumes: [es-data:/usr/share/elasticsearch/data]
    networks: [ezdata-network]

  minio:
    image: minio/minio
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: <改我>
    command: server /data --console-address ":19001"
    ports: ["9000:9000", "19001:19001"]
    volumes: [minio-data:/data]
    networks: [ezdata-network]
```

backend/worker 的 `depends_on` 增加 `elasticsearch`、`minio`；`.env.docker*` 补 ES/MinIO 连接配置（host 用 compose 服务名）。

---

## 6. 配置与初始化

- **配置**：沿用模板 pydantic `--env=dockermy` → `.env.dockermy`；DB/Redis/ES/MinIO host 在 compose 用服务名覆盖（`load_dotenv` 不覆盖已存在环境变量）。
- **建库迁移**：用模板 **alembic**（CLI 启动时迁移），把旧 `migrations/versions/0001_init_schema`、`0002_seed_data` 并入 `api/alembic/versions/`；初始数据可继续用 `api/sql/*.sql` 挂 initdb 作种子。
- **对象存储/ES 初始化**：参考旧 `init_system.py` 的 S3 bucket 检查、ES 索引创建，迁到模板 CLI 的启动钩子。

---

## 7. compose 文件规划

| 文件 | 用途 | 服务集合 |
|---|---|---|
| `docker-compose.dev.yml` | 本地开发热更新 | backend(uvicorn --reload) + worker + frontend(vite) + mysql + redis + **es + minio(新增)** |
| `docker-compose.my.yml` | 生产(MySQL) | frontend + backend + **worker(新增)** + mysql + redis + **es + minio(新增)** |
| `docker-compose.pg.yml` | 生产(PostgreSQL) | 同上，DB 换 postgres |
| `tests/docker-compose.test.*.yml` | e2e | 维持模板现状，按需加 es/minio |

> 可选：把 es/minio 拆到独立 `docker-compose.middleware.yml`，生产用 `-f` 叠加，便于外部已有中间件时省略。

---

## 8. K8s / Helm（后置阶段）

- 保留并改造旧 `deploy/kubernetes/ezdata` Helm chart：
  - 工作负载从 `master/scheduler` 改为 **backend / worker / frontend**（scheduler 进程内，无独立 Deployment）。
  - 依赖子 chart 保留 bitnami `mysql/redis/minio` + elastic `elasticsearch`。
  - backend 多副本时依赖 `server.py` 启动锁保证 APScheduler 单实例调度。

---

## 9. 落地待办清单

- [ ] backend `Dockerfile.my`/`.pg` 补 `install_handlers.py` + `etl/requirements.txt`（必要时换 miniconda base）
- [ ] `docker-compose.my.yml`/`.pg.yml` 补 `worker` service（复用 backend 镜像）
- [ ] 三套 compose 补 `elasticsearch` + `minio` service 与 volume，backend/worker `depends_on` 跟进
- [ ] `.env.dockermy`/`.env.dockerpg`/`.env.dev` 补 ES/MinIO 连接配置
- [ ] 旧 migrations 并入 alembic；启动迁移流程打通
- [ ] `init_system.py` 的 ES 索引/S3 bucket 初始化迁到模板 CLI 启动钩子
- [ ] requirements 钉死 akshare/ccxt 等版本（弃运行时 upgrade）
- [ ] （后置）flower 可选 service；（后置）sandbox 独立隔离容器；（后置）Helm chart 改造

---

## 附录：端口对照（统一走模板方案）

| 用途 | 旧 ezdata | 新(本方案) |
|---|---|---|
| 后端 API | 8001 | 9099（prod 19099） |
| 前端 | 80 | 12580 |
| Scheduler | 8002(独立) | 进程内(无端口) |
| Flower | 5555 | 5555(可选) |
| MySQL | 3306 | 13306 |
| Redis | 6379 | 16379 |
| Elasticsearch | 9200 | 9200 |
| MinIO | 9000 / 19001 | 9000 / 19001 |
| Supervisor web | 9001 | 弃用 |
| Sandbox | 8001(独立) | 暂不部署 |
