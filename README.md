<h1 align="center">ezdata</h1>
<h4 align="center">AI 原生数据平台 —— 数据接入 · ETL 集成 · 任务编排 · 知识库 RAG · AI 分析</h4>

<p align="center">
  <img alt="python" src="https://img.shields.io/badge/python-≥3.10-blue">
  <img alt="node" src="https://img.shields.io/badge/node-≥18-blue">
  <img alt="vue" src="https://img.shields.io/badge/Vue-3-42b883">
  <img alt="fastapi" src="https://img.shields.io/badge/FastAPI-async-009688">
  <img alt="es" src="https://img.shields.io/badge/Elasticsearch-8-005571">
</p>

<p align="center">
  🌐 在线演示:<a href="http://124.220.57.72/"><b>http://124.220.57.72/</b></a>
</p>

> ezdata 是一个 AI 原生的数据平台:统一接入异构数据源,做 ETL 集成与任务编排,沉淀数据源专属知识库(RAG),并把知识喂给 AI 取数/分析。基于 [RuoYi-Vue3-FastAPI](https://github.com/insistence/RuoYi-Vue3-FastAPI) 重构(RBAC + 多租户 + 数据权限开箱即用)。

## ✨ 核心能力

- **数据管理** `module_data`:60+ 连接器(RDBMS / Elasticsearch / MongoDB / Kafka / 向量库 / 对象存储 …),数据源 → 数据模型 → 取数 / 数据接口,基于 [dlt](https://dlthub.com/) 的 ETL 集成;只读护栏 + AI 取数。
- **任务调度 & 工作流** `module_task_schedule`:Celery + APScheduler 定时调度;**任务工作流(DAG)** 用 AntV X6 画布编排,事件驱动、版本化、单机/分布式两种运行模式 + 运行监控。
- **知识库(RAG)** `module_rag`:文档(pdf/docx/excel/pptx/csv/md/网页…)抽取 → 切分(含语义/Markdown)→ 向量化 → **ES8 向量库(dense_vector + kNN + BM25 混合检索)**;Contextual Retrieval、增量训练、QA、**每个数据源的专属知识库**;处理层接入 [Agno](https://github.com/agno-agi/agno)(readers / chunking / VectorDb 封装)。
- **AI** `module_ai` / `module_dashboard`:统一 AI 模型管理(密钥 AES 加密,支持**深度思考**模型);Agno Agent 对话——发现数据源、查表结构、检索知识库,在沙箱里跑取数/计算并产出结论 + **图表/表格**;**AI 工具**(内置百度搜索等 + MCP 接入)、**AI 应用**(把提示词/工具/知识库打包成独立助手 + 对外 APIKey)、**跨会话长期记忆**;对话内还能**提议 / 修改 / 复制 / 调试运行任务**(AI 填表、人拍板);控制台总览(ECharts)。
- **系统**:用户 / 角色 / 菜单 / 部门 / 字典,RBAC + **多租户** + 数据权限。

## 🧱 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 · Element Plus · ECharts · AntV X6 · Vite |
| 后端 | FastAPI · SQLAlchemy 2.0(async) · Pydantic v2 |
| 任务 | Celery · APScheduler · dlt |
| AI / RAG | Agno · DashScope/OpenAI embedding · chonkie · unstructured |
| 存储 | MySQL 8 / PostgreSQL · Redis · **Elasticsearch 8** · MinIO/S3 |

## 🚀 快速开始(Docker)

```bash
# 1) 准备环境变量(必需:.env.dev 被 git 忽略,缺失会导致后端回退到默认库名而连不上)
cp api/.env.dev.example api/.env.dev

# 2) 一键起开发环境(MySQL + Redis + ES8 + MinIO + 后端 + worker + 前端)
docker compose -f docker-compose.dev.yml up -d

# 生产参考:docker-compose.yml(默认 MySQL;PostgreSQL 加 --env-file .env.pg)
```

- 前端默认 `http://localhost:12580`,后端 `http://localhost:9099`(Swagger:`/docs`)。
- **默认登录**:`admin` / `admin123`。
- **开箱即用财经演示**(首启自动导入,可重跑 `api/demo_seed.py`):AKShare 财经数据源 + 内置 ES(`demo_es`)+ **27 个数据集成任务**(A股/港股/美股快照、日线、涨停池、龙虎榜、概念/行业板块、宏观等,按**北京时间**定时)+ 一个「财经数据分析助手」AI 应用(对话取数 + 绘图)。定时表达式为 7 段 Quartz(秒 分 时 日 月 周 年),与前端 cron 组件一致。
- **默认中间件口令**(dev / prod compose 已统一,仅供本地 / 内网):`ezdata123456` —— MySQL `root`、PostgreSQL `postgres`、Redis、MinIO `minio`、Elasticsearch `elastic`。⚠️ 正式对外部署务必改强口令或改用环境变量 / secret 注入。
- 初始化 SQL:`api/sql/ezdata.sql`(MySQL)/ `api/sql/ezdata-pg.sql`(PostgreSQL),首次启动自动挂载导入。

本地(非容器)开发见 [docs/DEPLOY.md](docs/DEPLOY.md)。

## 📁 目录结构

```
api/                 后端(FastAPI)
  module_admin/      系统:用户/角色/菜单/多租户
  module_data/       数据源 / 模型 / 取数 / ETL(dlt)
  module_task_schedule/  任务调度 + DAG 工作流编排
  module_rag/        知识库(RAG):抽取/切分/向量库(ES8)/检索/专属库
  module_ai/         AI 模型管理 / 对话
  module_dashboard/  控制台概览
web/                 前端(Vue3 + Element Plus)
docs/                设计与部署文档
```

## 📚 文档

- [部署指南](docs/DEPLOY.md)
- [平台重构计划](docs/REFACTOR_PLAN.md)
- [数据模块设计](docs/DATA_MODULE_DESIGN.md)
- [DAG 工作流方案](docs/DAG_REFACTOR_PLAN.md)
- [知识库(RAG)方案](docs/KB_REFACTOR_PLAN.md)
- [变更记录(模板)](docs/CHANGELOG.md)
