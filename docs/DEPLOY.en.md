> [简体中文](DEPLOY.md) | **English**

# ezdata Deployment Guide

> Applies to branch: `v2.0`. This document reflects the **current actual deployment shape** (container-per-service, no supervisord; Scheduler runs in-process; ES8 + MinIO now included in compose; the debug-mode sandbox is in place).
> In one sentence: for development, bring everything up with `docker-compose.dev.yml`; for production, use `docker-compose.yml` (MySQL by default, switch to PostgreSQL with `--env-file .env.pg`).

---

## 1. Architecture Overview

Container-per-service, lean images (`python:3.10` / `node:18`). The backend runs FastAPI + APScheduler in a single process (a startup lock elects the leader, so with multiple replicas only one instance schedules), and the Celery worker executes tasks in its own container. Production combines my/pg into a **single `docker-compose.yml`**, driven uniformly by a **single `.env` in the same directory** (see [5. Configuration](#5-configuration)).

```
                              host :80                                 :19099
                                │                                        │
  browser ──────────────►  ezdata-frontend (nginx + Vue static)          │(backend direct debug port, need not be exposed)
                                │  location /       → SPA                 │
                                │  location /api/   → reverse-proxy backend (strip /api) │
                                ▼                                        ▼
                          ezdata-backend (uvicorn FastAPI + in-process APScheduler leader election)
                                │
            ┌───────────┬───────┼──────────────┬──────────────────┐
            ▼           ▼       ▼              ▼                  ▼
       ezdata-mysql  ezdata-  ezdata-es    ezdata-minio       ezdata-worker (celery)
       /-pg(primary  redis    (task logs +   (S3 object store,   reuses backend image, runs
        DB, named    broker/  RAG vector    named-volume        DataIntegration/Python/DAG
        volume)      cache/   store + ES     persistence)        tasks, tenant carried in per task)
                     captcha  data service,
                              three uses in one, volume-persisted)

   debug-mode "run code / AI data fetch" ─► ezdata-sandbox (stateless isolated executor, internal net only)
                                       │ egress only via
                                       ▼
                                ezdata-egress-proxy (tinyproxy domain allowlist)

   ezdata-db-backup (scheduled DB backup sidecar, commented out / disabled by default in compose, see 10.1)
```

**Two networks (the key to isolation)**:

| Network | Type | Members |
|---|---|---|
| `ezdata-network` | bridge (with NAT / public internet) | frontend / worker / mysql / redis / es / minio / egress-proxy |
| `ezdata-sandbox-net` | **`internal=true` (no direct public internet)** | sandbox / egress-proxy / backend·worker (calling the sandbox) / mysql·es·minio (for the sandbox to fetch data over the internal net) |

The sandbox lives only on the internal net, has no public internet itself, and any egress must go through the egress-proxy domain allowlist (`SANDBOX_EGRESS_ALLOW`), with `cap_drop ALL + no-new-privileges + pids/mem quotas`. It bakes in no DB/JWT credentials; anything execution needs is injected per request and discarded after use.

| service | image / build | role | dev | prod |
|---|---|---|:--:|:--:|
| frontend | `web/Dockerfile` (node→nginx) / vite | frontend + reverse-proxy `/api` | ✅ | ✅ |
| backend | `api/Dockerfile.dev` / `.my` / `.pg` | API + in-process scheduling | ✅ | ✅ |
| worker | reuses backend image | Celery task execution | ✅ | ✅ |
| mysql / postgres | `mysql:8.0` / `postgres:14` | primary DB (named-volume persistence) | ✅ | ✅ |
| redis | `redis:latest` | broker / cache / captcha / leader-election lock / log stream | ✅ | ✅ |
| elasticsearch | `elasticsearch:8.13.4` | logs + vector store + data service (volume-persisted) | ✅ | ✅ |
| minio + minio-init | `minio/minio` + `minio/mc` | object storage + bucket creation (volume-persisted) | ✅ | ✅ |
| sandbox | reuses backend image | debug-mode code execution (isolated) | ✅ | ✅ |
| egress-proxy | tinyproxy | sandbox egress allowlist | ✅ | ✅ |
| db-backup | reuses DB image | scheduled DB backup (**disabled by default**) | — | optional |

> **Sandbox**: both the dev compose and the production `docker-compose.yml` (my / pg) already deploy the sandbox + egress with `SANDBOX_ENABLED=true`. For non-container / custom deployments where the sandbox is not started, setting `SANDBOX_ENABLED` empty falls back to real local execution (see [9.4](#94-debug-mode-code-execution)).
>
> **API prefix**: in production, nginx reverse-proxies `/api/` to the backend (`APP_ROOT_PATH=/api`, frontend `VITE_APP_BASE_API=/api`); dev uses `/dev-api`. The GitHub SSO callback is thus `http://<host>/api/oauth/github/callback`.

---

## 2. Quick Start —— Development

```bash
# 1) Prepare environment variables (required: .env.dev is git-ignored; if missing, the backend falls back to the default DB name and cannot connect)
cp api/.env.dev.example api/.env.dev

# 2) Bring everything up (backend + worker + frontend + mysql + redis + es + minio + sandbox + egress)
docker compose -f docker-compose.dev.yml up -d

# View logs / stop / wipe the DB and start over
docker compose -f docker-compose.dev.yml logs -f ezdata-backend-dev
docker compose -f docker-compose.dev.yml down          # stop, keep data volumes
docker compose -f docker-compose.dev.yml down -v       # stop and wipe all data volumes (for a fresh init)
```

- The source dirs `./api` and `./web` are mounted into the containers: editing a `.py` triggers backend hot reload (`--reload`, `WATCHFILES_FORCE_POLLING` is enabled on Windows), editing a `.vue/.js` triggers frontend HMR.
- On first start the MySQL container automatically imports `api/sql/ezdata.sql` (runs when the DB is empty), and the MinIO init container automatically creates the `ezdata` bucket.
- Open the frontend at `http://localhost:12580` and log in with **`admin` / `admin123`**.

---

## 3. Quick Start —— Production

Production app credentials are baked into the image's `.env.docker{my,pg}` (`ruoyi app run --env=dockermy/pg`); compose only overrides the middleware hosts with service names. MySQL / PostgreSQL are combined into a single `docker-compose.yml`: MySQL by default, and `.env.pg` flips all PG variables at once (image / container names / DB engine). See `.env.example` for all tunable options.

```bash
# MySQL edition (default, zero config)
docker compose up -d --build

# PostgreSQL edition (one flag)
docker compose --env-file .env.pg up -d --build
```

- Frontend at `http://<host>` (prod maps host port **80**), backend at `http://<host>:19099` (note the prod backend host port is **19099**).
- The first start likewise auto-imports `api/sql/ezdata.sql` / `ezdata-pg.sql` and creates the MinIO bucket.
- **Before going live, be sure to**: ① change the default credentials (see [10](#10-security-hardening-for-external-deployment)); ② set `STORAGE_PUBLIC_ENDPOINT` to a real domain / host IP the browser can reach; ③ fill in `JWT_SECRET_KEY` and the LLM/embedding API keys.

---

## 4. Ports & Default Accounts / Credentials

| Purpose | dev (host) | prod (host) |
|---|---|---|
| Backend API | 9099 | **19099** |
| Frontend | 12580 | 80 |
| MySQL / PG | 13306 / 15432 | 13306 / 15432 |
| Redis | 16379 | 16379 |
| Elasticsearch | 9200 | 9200 |
| MinIO API / console | 9000 / 19001 | 9000 / 19001 |
| Scheduler | in-process (no port) | in-process |
| Sandbox | 8003 (container internal net) | 8003 (container internal net) |

**Default login**: `admin` / `admin123` (there is also a test user `test`).

**Default middleware credentials** (dev / prod compose have standardized on `ezdata123456`, for local / internal-network use only):

| Component | Username | Password |
|---|---|---|
| MySQL | `root` | `ezdata123456` |
| PostgreSQL | `postgres` | `ezdata123456` |
| Redis | — | `ezdata123456` |
| MinIO | `minio` | `ezdata123456` |
| Elasticsearch | `elastic` | `ezdata123456` |

> ⚠️ These are a set of known weak credentials, **suitable only for local / isolated internal networks**. For external deployment see [10](#10-security-hardening-for-external-deployment).

---

## 5. Configuration

**Two layers + single file**:

- **Application layer**: the backend loads the in-image `api/.env.<APP_ENV>` based on `APP_ENV` (dev=`.env.dev`, prod=`.env.dockermy`/`.env.dockerpg`, specified by the `--env=` in `Dockerfile.my/.pg`), serving as the default fallback.
- **Single `.env` override**: the `.env` in the same directory as `docker-compose.yml` both drives compose interpolation (images / ports / container names / infrastructure credentials) and is injected into containers via the backend/worker `env_file` → **its values override the in-image `.env.<env>`** (because `load_dotenv` does not overwrite already-existing environment variables, i.e. compose injection takes precedence). So to change a credential/secret you only need to change this one file; `env_file` is `required:false`, so even without a `.env` it starts with zero config.
- Host ports use `*_HOST_PORT` (e.g. `DB_HOST_PORT`), kept separate from the application's connection port (`DB_PORT=3306`, etc.), to avoid name collisions when injecting from a single file.
- **Secrets stay out of the repo**: `.env`, `api/.env.dev`, `api/.env.dockermy`/`.dockerpg`/`.prod`, and `docker-compose.override.yml` are all git-ignored; the repo tracks only redacted `.example` files. Generate strong random keys in one shot with `python deploy/gen-secrets.py --env dockermy` (which writes an aligned `.env` and `api/.env.dockermy`). **Never commit real secrets.**
- Different names but must share the same value: ES (`ELASTIC_PASSWORD`=`TASK_ES_PASSWORD`=`RAG_VECTOR_PASSWORD`), MinIO (`MINIO_ROOT_USER`=`S3_ACCESS_KEY`, `MINIO_ROOT_PASSWORD`=`S3_SECRET_KEY`) —— see the root `.env.example` for details.

Key variables:

| Variable | Meaning |
|---|---|
| `DB_TYPE` / `DB_HOST` / `DB_DATABASE` / `DB_USERNAME` / `DB_PASSWORD` | Primary DB connection |
| `REDIS_HOST` / `REDIS_PASSWORD` / `REDIS_DATABASE` | Redis (broker / cache); the Celery broker URL automatically includes the password |
| `TASK_LOG_TYPE=es` + `TASK_ES_HOSTS` / `TASK_ES_USERNAME` / `TASK_ES_PASSWORD` | Task logs written to ES |
| `RAG_VECTOR_BACKEND` / `RAG_VECTOR_HOSTS` / `RAG_VECTOR_USER` / `RAG_VECTOR_PASSWORD` | RAG vector store (if hosts is left empty it falls back to `TASK_ES_HOSTS`, **but the account does not fall back and must be provided separately**) |
| `STORAGE_TYPE=s3` + `S3_ENDPOINT` / `S3_BUCKET_NAME` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` / `STORAGE_PUBLIC_ENDPOINT` | Object storage (MinIO) |
| `EMBEDDING_TYPE` / `EMBEDDING_MODEL` / `DASHSCOPE_API_KEY` | Knowledge-base embedding |
| `LLM_TYPE` / `LLM_MODEL` / `LLM_API_KEY` / `LLM_URL` | System fallback AI model. **Internal AI generation (ETL AI data fetch/transform, data query) prefers this** —— these entry points have no model-picker UI and all go through the fallback, so they won't get dragged off by some in-DB model with an unconfigured key; only if the fallback is unconfigured does it fall back to an enabled in-DB model. Conversations/apps with `modelId=0` also use this. |
| `LLM_REASONING` / `LLM_SUPPORT_IMAGES` | Whether the fallback model is a reasoning / multimodal model (`true` opens up display of thinking content / image input). **A reasoning model has a thinking delay (a few seconds) before its first token, so AI generation "seeming to stall for a moment" is normal; for instant output, switch to an Instruct-class non-reasoning model and set `false`.** |
| `CELERY_TASK_SOFT_TIME_LIMIT` / `CELERY_TASK_TIME_LIMIT` | Global task timeouts (seconds, default `1800`/`2100`). The soft timeout raises an exception → marks failure and alerts; the hard timeout `SIGKILL`s the stuck child process and frees the slot. A task-level `timeout` can override: `0`=use this default, `-1`=unlimited (streaming/very long), `>0`=custom. |
| `CELERY_WORKER_PREFETCH_MULTIPLIER` | Number of tasks each worker prefetches at once (default `1`). `1` = a slow/stuck task won't drag down the others it prefetched, reducing queue congestion. |
| `TZ` / `SCHEDULER_TZ` | Container timezone / scheduler timezone, **both default to `Asia/Shanghai`**. The container's default UTC would make a cron "9am-3pm" run at Beijing 5pm-11pm, so be sure to keep Beijing time (see [7.1](#71-scheduled-task-timezone)). |
| `JWT_SECRET_KEY` | Token signing (required in prod) |
| `DATA_ENCRYPT_KEY` | AES encryption of in-DB data-source/AI credentials (separate from JWT; if left empty it falls back to being derived from JWT, compatible with old ciphertext) |
| `SANDBOX_ENABLED` / `SANDBOX_API_URL` / `SANDBOX_BEARER_KEY` | Debug-mode code-execution sandbox |
| `GITHUB_SSO_ENABLED` / `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` / `GITHUB_REDIRECT_URI` | GitHub SSO login (callback `…/api/oauth/github/callback`, see [10.2](#102-github-sso-login)) |

---

## 6. Data Initialization & Demo Data

- **DB creation**: on the first start of the DB container, `api/sql/ezdata.sql` (MySQL) / `ezdata-pg.sql` (PG) is mounted into `/docker-entrypoint-initdb.d` and auto-imported when the DB is empty (the full seed of tables / menus / users / dictionaries / config / roles).
- **The default is a clean, empty project**: the seed contains only platform base data, no demo data sources / tasks whatsoever.
- **Runtime tables**: `ai_sessions` and the like are lazily created by agno on the first conversation, no need to pre-create them.

### 6.1 Optional: load the finance demo data (akshare → ES + AI analysis assistant)

If you want an out-of-the-box finance demo, **just run the script once by hand after the services are up** (no source changes / image rebuild needed):

```bash
# Run from the repo root (the script is fed into the container via stdin; the image need not contain this file)
docker exec -i ezdata-backend-my python - < api/demo_seed.py
```

It will (idempotent, safe to re-run; **only touches the demo namespace, never users/permissions/other data**):

- Create 2 data sources: `akshare_cn` (key-free finance), `demo_es` (built-in ES)
- Create **27 data integration tasks** + 27 data models (A-share/HK/US snapshots, daily bars, limit-up pool, dragon-tiger list, concept/sector boards, technical stock screening, earnings, macro GDP/LPR, news, etc.), and **dispatch them to Celery for async execution**, filling data into the `fin_*` indices of `demo_es` in about 2-3 minutes
- Create 1 AI app "Finance Data Analysis Assistant" (app_id=9001, already bound to the data source + data-fetch/charting tools)
- The scheduled tasks use **7-field Quartz** cron (second minute hour day month weekday year); intraday tasks follow **Beijing time** (see [7.1 Timezone](#71-scheduled-task-timezone)), Monday-Friday=`2-6`, step with `0/N`, consistent with the frontend cron component
- On completion it automatically issues `PUBLISH scheduler:sync:request` to the running scheduler to **trigger an immediate reload** (prints `✅ notified… no restart needed`); if it prints `⚠️ no listening scheduler detected` (usually a stale image), then `docker restart ezdata-backend-my` to activate

> **To let the AI assistant chat and produce charts, you must configure an LLM first**: set the environment variables `LLM_TYPE` / `LLM_MODEL` / `LLM_API_KEY` (the app's `model.modelId=0` uses this fallback), or enable a conversation model in "AI Model Management". If using a **reasoning** model (e.g. DeepSeek-V4/R1), also set `LLM_REASONING=true` to display the thinking process. Data ETL and queries do not depend on an LLM.

> For non-container deployments, manually import the corresponding `.sql` into your DB; the demo data likewise runs `python demo_seed.py` (in the api directory, after the app env is loaded).

---

## 7. Middleware Notes

- **Elasticsearch 8**: `xpack.security` is enabled (user `elastic`), with `xpack.security.http.ssl.enabled=false` to keep **plaintext HTTP + basic auth** (certificate-free, suitable for internal networks). `ELASTIC_PASSWORD` **takes effect only when the data directory is empty (first init)**; to change the password of an existing cluster, either `down -v` to wipe the volume or run `elasticsearch-reset-password` inside the container.
- **Redis**: `--requirepass ezdata123456`; both the health check and the Celery broker carry the password.
- **MinIO**: the `minio-init` one-shot container creates the `ezdata` bucket and sets anonymous download; after changing the root credential, that container's `mc alias` credential must be synced too (compose already syncs it).
- **The `demo_es` data source's password** is stored in `config` (plaintext) rather than in the encrypted `secrets` —— this lets the static SQL seed connect directly to the encrypted ES. It runs fine; but when editing that data source in the UI the password field shows as empty (the handler can still connect). In production you can re-enter the password once in the UI to store it in encrypted secrets.

### 7.1 Scheduled Task Timezone

- **Two layers both default to UTC+8**: ① the image bakes in `ENV TZ=Asia/Shanghai` (`api/Dockerfile.{dev,my,pg}`) —— **Beijing time by default**, no fallback to UTC in any run mode (dev/prod/non-compose); ② both the dev and prod compose inject `TZ=${TZ:-Asia/Shanghai}` into backend/worker (a host `TZ` can override), taking effect immediately without rebuilding the image. Together they align the container `date` / logs / `datetime.now()`.
- The scheduler (APScheduler) separately interprets cron by **`SCHEDULER_TZ` (default `Asia/Shanghai`)** and **explicitly injects the timezone into every trigger** (not relying on the container TZ); Celery `timezone` is likewise `Asia/Shanghai`.
- **Why it matters**: if the container is UTC, a naive `datetime.now()` (create_time / log timestamps) will be 8 hours behind; and a cron `hour=9-15` (meaning the Beijing trading session) would fire at **UTC 9-15 = Beijing 5pm-11pm** → during the day it "looks like the scheduled task never fires at all." The two-layer defaults above eliminate this; old images land it after `docker compose pull` / rebuild.
- **cron format**: 7-field Quartz `second minute hour day month weekday year`, consistent with the frontend cron generator —— **step with `0/N`** (not `*/N`, otherwise the component shows NaN); **weekday as a number** (Quartz Sunday=1..Saturday=7, Monday-Friday=`2-6`, don't use names/0); **write `*` for year**; day and weekday are mutually exclusive (if weekday is set, write `?` for day). Example: every 5 minutes during the trading session `0 0/5 9-15 ? * 2-6 *`. The backend automatically converts the Quartz numeric weekday to the APScheduler convention.
- An invalid cron is **rejected at create/edit time** (fail-fast validation); even for existing dirty data, syncing only skips that one entry without affecting the other tasks or the scheduler.

### 7.2 Task Timeout (prevent stalls/congestion) & Restarting the Scheduler

- **Timeout**: tasks are by default subject to the global soft/hard timeouts (`CELERY_TASK_SOFT_TIME_LIMIT`/`CELERY_TASK_TIME_LIMIT`, default 1800/2100 seconds). The soft timeout → marks failure and alerts (no retry, since a retry would most likely still time out); the hard timeout → `SIGKILL`s the stuck child process and frees the worker slot, and prefork automatically spawns a new child. Combined with `CELERY_WORKER_PREFETCH_MULTIPLIER=1`, a stuck task won't drag down queued tasks.
- **Task-level `timeout`** (the "Timeout" field on the task edit page): `0`=use the global default, `-1`=**unlimited** (streaming/very long tasks must set -1, or they'll be wrongly killed by the global hard timeout), `>0`=custom seconds (hard timeout = soft + 300).
- **Restarting the scheduler**: if the scheduler "breaks" (loses the lock, dev hot reload, gets stuck), click the "**Restart Scheduler**" button on the "System Monitor → Scheduled Tasks" page to recover via `close → re-grab lock → reload all enabled tasks from the DB`. That button's permission `monitor:job:restart` is not assigned to ordinary roles, **so by default only the super admin can see/use it**. With multiple workers it broadcasts over a Redis channel, and the real leader executes it.
- Note: restarting only **reschedules the already-enabled tasks in the DB**; it does not create tasks or fetch data immediately; demo data initialization still requires running `demo_seed.py` by hand (see [6.1](#61-optional-load-the-finance-demo-data-akshare--es--ai-analysis-assistant)).

---

## 8. Local (Non-Container) Development

Prerequisites: Python ≥ 3.10, Node ≥ 18, with an existing external MySQL/PG + Redis + ES8 + (optional) MinIO.

```bash
# Backend
cd api
pip install -r requirements.txt          # base
pip install -r requirements-data.txt     # ETL / connectors (dlt, etc.)
pip install -r requirements-pg.txt       # when using PG
pip install -r requirements-storage.txt  # when using object storage
cp .env.dev.example .env.dev             # change DB/Redis/ES etc. to local addresses, import sql/ezdata.sql
python app.py                            # start FastAPI (host/port/reload read from .env)

# Celery worker (open another terminal, the task scheduling/execution layer)
celery -A config.celery_app worker -Q default --autoscale=4,1 --loglevel=INFO

# Frontend
cd web
npm install
npm run dev                              # vite, default 12580
```

> The Scheduler is in the backend process (APScheduler), no need to start it separately; flower / sandbox can be started separately as needed.

---

## 9. Operations

### 9.1 Fresh Initialization (wipe the DB and start over)
`docker compose -f docker-compose.dev.yml down -v` wipes the mysql/es/minio data volumes, then `up -d` re-imports the SQL seed + creates buckets + initializes ES.

### 9.2 Changing Credentials
To change a credential consistently: ① change the root credential of the corresponding compose service; ② change the app-side connection credential in `.env.dev` (or `.env.docker*`); ③ for already-initialized ES/MySQL etc., `down -v` or use their respective reset tools; ④ restart backend + worker.

### 9.3 Upgrading the Source Code
Dev source is mounted, so after editing code the backend auto-reloads; the worker needs `docker restart ezdata-worker-dev`. In prod, after editing, rebuild the image with `docker compose up -d --build` (add `--env-file .env.pg` for PG).

### 9.4 Debug-Mode Code Execution
Code in the platform's "debug / preview" mode (ETL code data fetch, AI charts, etc.) executes in the sandbox (subprocess isolation + timeout/memory + import allowlist + egress domain allowlist). **Both the dev compose and the production `docker-compose.yml` (both my / pg modes) already deploy the sandbox with `SANDBOX_ENABLED=true`**; the sandbox egress domain allowlist is controlled by the egress-proxy's `SANDBOX_EGRESS_ALLOW` (defaults to finance/market-data domains, add/remove as needed). For non-container or custom deployments where the sandbox is not started, setting `SANDBOX_ENABLED` empty falls back to real local execution in the worker/backend. Formal tasks always run in the worker.

### 9.5 Upgrading an Existing DB (schema changes)

New features may add columns (e.g. task timeout `task.timeout`). A **fresh install** built from `ezdata.sql`/`ezdata-pg.sql` includes them; an **existing DB does not re-run the SQL**, so you need to add the new columns —— two ways (pick one):

- **Alter the column directly (simplest for a single column)**:
  ```bash
  docker exec ezdata-mysql mysql -uroot -p'<DB password>' ezdata -e \
    "ALTER TABLE task ADD COLUMN timeout INT NULL DEFAULT 0 COMMENT 'Task timeout (seconds): 0=global default, -1=unlimited, >0=custom';"
  ```
- **Via an alembic migration**: this project's DB is mostly initialized from `*.sql` and is **not under alembic control (no `alembic_version` table)**, so running `alembic upgrade head` directly would re-run from baseline and error out. The correct approach is to first `stamp` to the version corresponding to the SQL, then upgrade:
  ```bash
  docker exec -it ezdata-backend-my sh -c "cd /app && alembic stamp 0002_seed_system && alembic upgrade head"
  ```
  After that, any further migrations can just run `alembic upgrade head` normally.

> ⚠️ New code queries the new columns, so **add the columns first, then deploy the image with the new code** (in the same maintenance window); a missing column will cause the related queries to error.

**Optional: auto-migrate on startup** —— set the environment variable **`AUTO_MIGRATE=true`** (off by default) and the backend will automatically `alembic upgrade head` on startup, saving the manual steps. For a "DB not under alembic (no `alembic_version`, built from `*.sql`)" it will **stamp the baseline first, then upgrade**: the baseline is controlled by `AUTO_MIGRATE_BASELINE` (default `0002_seed_system`, i.e. the table-creation + seed state corresponding to `ezdata.sql`). The migrations are **idempotent** (they check existence before adding a column/changing a type), so they are safe for a fresh DB (which already has the new columns), a lagging DB, and an already-managed DB alike; a failed migration is only logged and **does not block startup**. For a DB that lags far behind, if the baseline is not 0002, just set `AUTO_MIGRATE_BASELINE` to the version it actually corresponds to.

---

## 10. Security Hardening (for external deployment)

The default `ezdata123456` is for local/internal-network use only. On the public internet or in a multi-user environment, be sure to:

- **Generate strong random keys in one shot**: `python deploy/gen-secrets.py --env dockermy` (or `deploy/gen-secrets.sh --env dockermy`). It generates and writes to `api/.env.dockermy` (JWT key, data encryption key, transport-layer RSA key pair, strong random credentials for each middleware, sandbox key) and the root `.env` (compose infrastructure credentials, the two aligned). Then change the `admin` initial password.
- **Secrets stay out of the repo**: `api/.env.prod`/`.env.dockermy`/`.env.dockerpg` are already in `gitignore`; the repo keeps only `.example` templates. In production, use gen-secrets or external secret injection, and never commit real secrets.
- **Data encryption key separate from JWT**: AES encryption of in-DB data-source/AI credentials uses a dedicated `DATA_ENCRYPT_KEY` (only if left empty does it fall back to being derived from JWT). Rotating JWT does not affect already-encrypted data; `MultiFernet` is compatible with old ciphertext, and after changing `DATA_ENCRYPT_KEY` the next save rewrites it with the new key.
- **Shrink the exposure surface**: do not open the database / Redis / ES / MinIO ports to the public internet; expose only the frontend (and the necessary backend API).
- **ES TLS**: if you need link encryption, set `xpack.security.http.ssl.enabled=true` and configure certificates, and change the client hosts to `https://`.
- **Sandbox**: compose deploys a dedicated sandbox + egress allowlist by default (code data fetch / AI code execution do not run bare in the worker). Before going live, be sure to change `SANDBOX_BEARER_KEY` (default `ezdata-sandbox-prod-key`), and tighten the `SANDBOX_EGRESS_ALLOW` egress domain allowlist as needed.
- **Multi-tenant deny by default**: within an HTTP request scope, an empty tenant context is always denied (no more fail-open showing the whole DB); the `data_api` apikey for external data interfaces is forced to bind a `ref_id`. A user with no department must first be assigned a department (which determines the tenant) before they can access data.

### 10.1 Database Backup / Restore

> ⚠️ The `ezdata-db-backup` sidecar is **disabled by default** (commented out in `docker-compose.yml`). When you need scheduled backups, uncomment that entire service block + uncomment the `ezdata-db-backup-data` entry in the `volumes` block, then `docker compose up -d`.

Once enabled: per `BACKUP_INTERVAL_SECONDS` (default 24h) it runs `mysqldump`/`pg_dump` → gzip into the named volume `ezdata-db-backup-data:/backups`, keeping the most recent `BACKUP_KEEP` (default 7) copies.

```bash
# After enabling the sidecar: manual backup now / list / restore (⚠️ restore overwrites the existing DB)
docker exec ezdata-db-backup sh /scripts/backup.sh
docker exec ezdata-db-backup sh -c 'ls -lh /backups'
docker exec -e DB_PASSWORD=<DB password> ezdata-db-backup sh /scripts/restore.sh /backups/ezdata_mysql_YYYYmmdd_HHMMSS.sql.gz

# When the sidecar is not enabled: a one-shot container to manually back up to the host ./backups
docker run --rm --network ezdata-network -v "$(pwd)/deploy/backup:/scripts:ro" -v "$(pwd)/backups:/backups" \
  -e DB_HOST=ezdata-mysql -e DB_USER=root -e DB_PASSWORD=<DB password> -e DB_NAME=ezdata \
  mysql:8.0 sh /scripts/backup.sh
```

The DB data is already persisted to the named volume `ezdata-db-data` (PG uses `DB_DATA_DIR=/var/lib/postgresql/data`), so `docker compose down` (without `-v`) no longer loses data —— backup and persistence are two different things, persistence is always in effect.

### 10.2 GitHub SSO Login

Enable it after configuring in `api/.env.<env>` (see the `GITHUB_*` section of `.env.*.example`):

```
GITHUB_SSO_ENABLED = true
GITHUB_CLIENT_ID = <GitHub OAuth App Client ID>
GITHUB_CLIENT_SECRET = <Client Secret>
GITHUB_REDIRECT_URI = https://<domain>/api/oauth/github/callback   # must match the OAuth App callback
GITHUB_SSO_FRONTEND_URL = https://<domain>/sso-callback
GITHUB_ALLOWED_ORG =                     # optional: restrict to members of this GitHub org
GITHUB_SSO_AUTO_CREATE = true            # auto-create an account on first login
GITHUB_SSO_DEFAULT_ROLE_KEY = common     # default role for new users
GITHUB_SSO_DEFAULT_DEPT_ID = 100         # default department for new users (determines the tenant)
```

Flow: the login page's "Sign in with GitHub" → backend `/oauth/github/authorize` (with state for CSRF protection) → GitHub authorization → `/oauth/github/callback` (validates state, exchanges for the profile, binds via `sys_user_oauth` / matches by email / auto-creates an account) → issues a JWT → redirects back to the frontend `/sso-callback`. The `sys_user_oauth` table is auto-created by the startup `create_all`.

---

## 11. Troubleshooting

| Symptom | Cause / Fix |
|---|---|
| Backend won't start, connecting to a DB like `ruoyi-fastapi` | Missing `cp .env.dev.example .env.dev`, fell back to the default DB name. Add it and restart. |
| Changed `ELASTIC_PASSWORD` but ES still uses the old password | That variable only takes effect when the ES data directory is empty. `down -v` to wipe the volume, or run `elasticsearch-reset-password` inside the container. |
| Console / usage-stats page reports `ai_sessions doesn't exist` | A fresh environment that has never had a conversation, so the table has not yet been created by agno. A null fallback is in place; send one message to create the table. |
| `down -v` reports `network ... has active endpoints` | Docker leftover endpoints. `docker network prune -f`; if that still fails, restart Docker. Doesn't affect the next `up`. |
| Frontend opens but APIs return 401 / CORS | Check the nginx reverse proxy (prod `web/bin/nginx.docker*.conf`) / the vite proxy target (dev `VITE_DEV_PROXY_TARGET`). |
| Worker doesn't execute tasks | Check the `ezdata-worker-dev` logs for Redis `NOAUTH/WRONGPASS` (credential mismatch) or a queue name not in `CELERY_QUEUES`. |
| Tasks stall / queue congestion | Timeouts are built in: global soft/hard timeouts (`CELERY_TASK_*`, default 1800/2100) + task-level `timeout`; the hard timeout `SIGKILL`s the stuck child process to free the slot; `prefetch=1` prevents dragging down queued tasks (see [7.2](#72-task-timeout-prevent-stallscongestion--restarting-the-scheduler)). Streaming/very long tasks must set the task `timeout` to `-1`, or they'll be wrongly killed by the global hard timeout. If the scheduler is stuck, click "Restart Scheduler" on "System Monitor - Scheduled Tasks" (super admin). For an existing DB, first add the `task.timeout` column (see [9.5](#95-upgrading-an-existing-db-schema-changes)). |
| AI data fetch/transform reports a provider key error like `AIMLAPI_API_KEY not set` | There's an enabled model in "AI Model Management" with no key configured, and internal AI generation picked it. It's now changed so that **internal AI generation always uses the system fallback model (`LLM_*`)**; just confirm `LLM_TYPE/LLM_MODEL/LLM_API_KEY` are configured, or disable/complete that in-DB model. |
| Scheduled tasks "never fire at all" | ① Timezone: the container is UTC while the cron is written for the Beijing session → fires at Beijing 5pm-11pm. A new image (with `SCHEDULER_TZ=Asia/Shanghai` injected into the trigger) fixes it; for old images `docker compose pull`. ② Ran `demo_seed` without a reload: the new image auto-`PUBLISH`es to trigger it; otherwise `docker restart ezdata-backend-my` (the scheduler reads sys_job only on backend startup). A log line `next run at ... UTC` is ironclad proof the timezone is off. |
| The cron generator shows `NaN/x` for "minute/hour" | The expression used a `*/N` step, but the component parses `0/N` → `Number('*')=NaN`. Change to `0/N` (e.g. every 5 minutes `0/5`). |

---

## Appendix: Post-setup / Optional

- **Lightweight frontend image rebuild** (optional, a workaround for when `docker build` runs vite and OOMs / crashes Docker Desktop): split "running vite" from "building the image" —— in a build container that already has `node_modules`, `docker exec` to run `npm run build:docker` to produce `dist`, `docker cp` it out, then package with a minimal nginx image that only `COPY dist` (not running vite inside buildkit). This is especially stable on resource-constrained Windows/WSL2; native Docker on Linux can generally just `docker compose build ezdata-frontend` directly.
- **flower** (Celery monitoring): reuse the backend image `celery -A config.celery_app flower`, default 5555, add a service as needed.
- **K8s / Helm**: split workloads by backend / worker / frontend (the scheduler is in-process, no separate Deployment); depend on the mysql/redis/minio/es sub-charts; backend multi-replica relies on the `server.py` startup lock to guarantee a single scheduling instance.
