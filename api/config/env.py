import argparse
import configparser
import os
import sys
from typing import Literal

from dotenv import load_dotenv
from pydantic import computed_field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """
    应用配置
    """

    app_env: str = 'dev'
    app_name: str = 'ezdata'
    app_root_path: str = '/dev-api'
    app_host: str = '0.0.0.0'
    app_port: int = 9099
    app_version: str = '1.0.0'
    app_reload: bool = True
    app_workers: int = 1
    app_ip_location_query: bool = True
    app_same_time_login: bool = True
    app_demo_mode: bool = False
    app_disable_swagger: bool = False
    app_disable_redoc: bool = False
    app_trusted_proxy_ips: str = '127.0.0.1,::1'
    app_trusted_proxy_hops: int = 1


class JwtSettings(BaseSettings):
    """
    Jwt配置
    """

    jwt_secret_key: str = 'b01c66dc2c58dc6a0aabfe2144256be36226de378bf87f72c0c795dda67f4d55'
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 1440
    jwt_redis_expire_minutes: int = 1440


class DataBaseSettings(BaseSettings):
    """
    数据库配置
    """

    db_type: Literal['mysql', 'postgresql'] = 'mysql'
    db_host: str = '127.0.0.1'
    db_port: int = 3306
    db_username: str = 'root'
    db_password: str = 'mysqlroot'
    db_database: str = 'ruoyi-fastapi'
    db_echo: bool = True
    db_max_overflow: int = 10
    db_pool_size: int = 50
    db_pool_recycle: int = 3600
    db_pool_timeout: int = 30

    @computed_field
    @property
    def sqlglot_parse_dialect(self) -> str:
        if self.db_type == 'postgresql':
            return 'postgres'
        return self.db_type


class RedisSettings(BaseSettings):
    """
    Redis配置
    """

    redis_host: str = '127.0.0.1'
    redis_port: int = 6379
    redis_username: str = ''
    redis_password: str = ''
    redis_database: int = 2


class LogSettings(BaseSettings):
    """
    日志与队列配置
    """

    log_mask_enabled: bool = True
    log_mask_placeholder: str = '******'
    log_mask_fields: str = (
        'password,old_password,new_password,confirm_password,api_key,token,access_token,refresh_token,'
        'authorization,client_secret,secret,secret_key,private_key,private_key_pem,credential,credentials,'
        'sms_code,captcha_code,system_prompt'
    )
    log_partial_mask_fields: str = 'phonenumber,phone,mobile,email'
    log_config_secret_patterns: str = 'password,token,secret,key,private,credential,access,jwt,captcha,sms'
    log_stream_key: str = 'log:stream'
    log_stream_group: str = 'log_aggregator'
    log_stream_consumer_prefix: str = 'worker'
    log_stream_batch_size: int = 100
    log_stream_block_ms: int = 2000
    log_stream_maxlen: int = 100000
    log_stream_claim_idle_ms: int = 60000
    log_stream_claim_interval_ms: int = 5000
    log_stream_claim_batch_size: int = 100
    log_stream_dedup_ttl: int = 3600
    log_stream_dedup_prefix: str = 'log:dedup'

    loguru_json: bool = False
    loguru_level: str = 'INFO'
    loguru_stdout: bool = True
    log_file_enabled: bool = True
    log_file_base_dir: str = 'logs'
    loguru_rotation: str = '50MB'
    loguru_retention: str = '30 days'
    loguru_compression: str = 'zip'
    log_instance_id: str = 'prod'
    log_service_name: str = 'ezdata-backend'
    log_worker_id: str = 'auto'


class CelerySettings(BaseSettings):
    """
    Celery执行器配置

    celery_broker_url/celery_result_backend 为空时，自动根据 Redis 配置构建。
    celery_queues 为逗号分隔的队列名列表，task.run_queue 必须在其中取值。
    """

    celery_broker_url: str = ''
    celery_result_backend: str = ''
    celery_redis_database: int = 3
    celery_default_queue: str = 'default'
    celery_queues: str = 'default'
    celery_timezone: str = 'Asia/Shanghai'
    celery_worker_max_tasks_per_child: int = 200
    celery_result_expires: int = 3600

    @property
    def queue_list(self) -> list[str]:
        return [item.strip() for item in self.celery_queues.split(',') if item.strip()]


class TaskLogSettings(BaseSettings):
    """
    任务执行日志配置

    task_log_type 控制日志输出位置：
        file - 写入文件（前端隐藏任务日志功能）
        db   - 写入数据库 task_log 表
        es   - 写入 Elasticsearch
    """

    task_log_type: Literal['file', 'db', 'es'] = 'db'
    task_log_file_dir: str = 'logs/task'
    task_es_hosts: str = ''
    task_es_index: str = 'task_logs'
    task_es_username: str = ''
    task_es_password: str = ''


class TransportCryptoSettings(BaseSettings):
    """
    传输层加解密配置
    """

    transport_crypto_enabled: bool = True
    transport_crypto_mode: Literal['off', 'optional', 'required'] = 'optional'
    transport_crypto_algorithm: str = 'RSA_OAEP_AES_256_GCM'
    transport_crypto_kid: str = 'default'
    transport_crypto_public_key: str = ''
    transport_crypto_private_key: str = ''
    transport_crypto_legacy_key_pairs: str = '[]'
    transport_crypto_rsa_key_size: int = 2048
    transport_crypto_public_key_ttl_seconds: int = 3600
    transport_crypto_frontend_config_ttl_seconds: int = 300
    transport_crypto_max_get_url_length: int = 4096
    transport_crypto_clock_skew_seconds: int = 120
    transport_crypto_replay_ttl_seconds: int = 300
    transport_crypto_enabled_paths: str = ''
    transport_crypto_required_paths: str = ''
    transport_crypto_exclude_paths: str = (
        '/openapi.json,/docs,/docs/oauth2-redirect,/redoc,'
        '/transport/crypto/frontend-config,/transport/crypto/public-key,/common/download,/common/download/resource'
    )


class GenSettings:
    """
    代码生成配置
    """

    author = 'insistence'
    package_name = 'module_admin.system'
    auto_remove_pre = False
    table_prefix = 'sys_'
    allow_overwrite = False

    GEN_PATH = 'vf_admin/gen_path'

    def __init__(self) -> None:
        if not os.path.exists(self.GEN_PATH):
            os.makedirs(self.GEN_PATH)


class UploadSettings:
    """
    上传配置
    """

    UPLOAD_PREFIX = '/profile'
    UPLOAD_PATH = 'vf_admin/upload_path'
    UPLOAD_MACHINE = 'A'
    DEFAULT_ALLOWED_EXTENSION = [
        # 图片
        'bmp',
        'gif',
        'jpg',
        'jpeg',
        'png',
        # word excel powerpoint
        'doc',
        'docx',
        'xls',
        'xlsx',
        'ppt',
        'pptx',
        'html',
        'htm',
        'txt',
        # 文本/知识库文档
        'md',
        'markdown',
        'csv',
        'tsv',
        'json',
        'jsonl',
        # 压缩文件
        'rar',
        'zip',
        'gz',
        'bz2',
        # 视频格式
        'mp4',
        'avi',
        'rmvb',
        # pdf
        'pdf',
    ]
    DOWNLOAD_PATH = 'vf_admin/download_path'

    def __init__(self) -> None:
        if not os.path.exists(self.UPLOAD_PATH):
            os.makedirs(self.UPLOAD_PATH)
        if not os.path.exists(self.DOWNLOAD_PATH):
            os.makedirs(self.DOWNLOAD_PATH)


class CachePathConfig:
    """
    缓存目录配置
    """

    PATH = os.path.join(os.path.abspath(os.getcwd()), 'caches')
    PATHSTR = 'caches'


class StorageSettings(BaseSettings):
    """
    存储配置（本地磁盘 / 各类对象存储）

    storage_type:
        local         - 本地磁盘（默认，与 /profile 静态服务、UPLOAD_PATH 对齐，行为同模板原状）
        s3            - S3 兼容对象存储（AWS S3 / MinIO 等，MinIO 走 S3 协议，address_style 用 path）
        oci-storage   - Oracle OCI（S3 兼容，依赖 boto3）
        aliyun-oss    - 阿里云 OSS（依赖 oss2）
        azure-blob    - Azure Blob（依赖 azure-storage-blob）
        google-storage- Google Cloud Storage（依赖 google-cloud-storage）
        tencent-cos   - 腾讯云 COS（依赖 cos-python-sdk-v5）

    云后端 SDK 见 requirements-storage.txt，仅在选用对应 storage_type 时才需安装。
    """

    storage_type: Literal['local', 's3', 'oci-storage', 'aliyun-oss', 'azure-blob', 'google-storage', 'tencent-cos'] = (
        'local'
    )
    storage_local_path: str = 'vf_admin/upload_path'
    # 浏览器可达的下载地址前缀；设置后所有后端的下载 URL 均以它为基准
    storage_public_endpoint: str = ''

    # ---- S3 / MinIO ----
    s3_endpoint: str = ''
    s3_bucket_name: str = 'ezdata'
    s3_access_key: str = ''
    s3_secret_key: str = ''
    s3_region: str = ''
    s3_address_style: str = 'path'
    s3_use_aws_managed_iam: bool = False

    # ---- Oracle OCI（S3 兼容）----
    oci_endpoint: str = ''
    oci_bucket_name: str = ''
    oci_access_key: str = ''
    oci_secret_key: str = ''
    oci_region: str = ''

    # ---- 阿里云 OSS ----
    aliyun_oss_endpoint: str = ''
    aliyun_oss_bucket_name: str = ''
    aliyun_oss_access_key: str = ''
    aliyun_oss_secret_key: str = ''
    aliyun_oss_region: str = ''
    aliyun_oss_auth_version: str = 'v4'

    # ---- Azure Blob ----
    azure_blob_account_url: str = ''
    azure_blob_container_name: str = ''
    azure_blob_account_name: str = ''
    azure_blob_account_key: str = ''

    # ---- Google Cloud Storage ----
    google_storage_bucket_name: str = ''
    google_storage_service_account_json_base64: str = ''

    # ---- 腾讯云 COS ----
    tencent_cos_bucket_name: str = ''
    tencent_cos_region: str = ''
    tencent_cos_secret_id: str = ''
    tencent_cos_secret_key: str = ''
    tencent_cos_scheme: str = 'https'


# 兼容旧项目/小写写法的 provider 别名 -> AiUtil 工厂注册名(CamelCase)
_LLM_PROVIDER_ALIASES = {
    'openai': 'OpenAI', 'anthropic': 'Anthropic', 'claude': 'Anthropic',
    'deepseek': 'DeepSeek', 'tongyi': 'DashScope', 'qwen': 'DashScope', 'dashscope': 'DashScope',
    'siliconflow': 'SiliconFlow', 'google': 'Google', 'gemini': 'Google', 'ollama': 'Ollama',
    'openrouter': 'OpenRouter', 'mistral': 'Mistral', 'groq': 'Groq', 'xai': 'xAI',
}


class AiSettings(BaseSettings):
    """
    系统内置 AI 兜底模型配置(环境变量,沿用旧项目 LLM_* 命名)

    用于「AI 模型管理」无可用模型时,系统内部的 AI 生成(ETL AI 取数/转换、数据查询 AI 取数等)
    回退到这里配置的模型。优先级:数据库启用模型 > 环境变量兜底模型。
    api_key 为明文(区别于库内 AES 加密存储)。

    .env 示例:
        LLM_TYPE=anthropic
        LLM_MODEL=claude-sonnet-4-6
        LLM_API_KEY=xxxx
        LLM_URL=http://10.0.3.248:3000/api
    """

    llm_type: str = ''        # 提供商:openai/anthropic/deepseek/tongyi...(大小写均可)
    llm_model: str = ''       # 模型编码,如 claude-sonnet-4-6 / deepseek-chat
    llm_api_key: str = ''
    llm_url: str = ''         # base_url(可空)
    llm_max_tokens: int = 1024

    @property
    def enabled(self) -> bool:
        return bool(self.llm_type and self.llm_model and self.llm_api_key)

    @property
    def provider(self) -> str:
        """归一化为 AiUtil 工厂注册名;未命中别名则按原样(允许直接写 CamelCase)。"""
        t = (self.llm_type or '').strip()
        return _LLM_PROVIDER_ALIASES.get(t.lower(), t)


class RagSettings(BaseSettings):
    """
    知识库(RAG)配置:embedding / rerank / 向量后端 兜底参数(沿用旧项目命名)。

    优先级:知识库绑定的 ai_models 模型 > 这里的环境变量兜底。
    向量后端默认 ES8;rag_vector_hosts 为空时回退到任务日志 ES(task_es_hosts)。

    .env 示例(取自旧 prod.env):
        EMBEDDING_TYPE=dashscope
        EMBEDDING_MODEL=text-embedding-v2
        DASHSCOPE_API_KEY=sk-xxx
        RAG_VECTOR_BACKEND=elasticsearch
        RAG_VECTOR_HOSTS=http://127.0.0.1:9200
    """

    embedding_type: str = 'dashscope'          # EMBEDDING_TYPE
    embedding_model: str = 'text-embedding-v2'  # EMBEDDING_MODEL
    embedding_dims: int = 0                     # EMBEDDING_DIMS(0=自动探测/按已知模型)
    embedding_api_key: str = ''                 # EMBEDDING_API_KEY
    embedding_url: str = ''                     # EMBEDDING_URL(base_url,可空)
    dashscope_api_key: str = ''                 # DASHSCOPE_API_KEY(provider=dashscope 时复用)
    embedding_cache: int = 1                    # EMBEDDING_CACHE(1=启用 rag_embedding 缓存)

    rerank_type: str = ''                       # RERANK_TYPE(空=不启用;dashscope / siliconflow / openai 兼容)
    rerank_model: str = 'gte-rerank'            # RERANK_MODEL
    rerank_api_key: str = ''                    # RERANK_API_KEY
    rerank_url: str = ''                        # RERANK_URL(OpenAI 兼容 rerank 的 base_url,可空;有内置默认的可不填)

    rag_vector_backend: str = 'elasticsearch'   # RAG_VECTOR_BACKEND
    rag_vector_hosts: str = ''                  # RAG_VECTOR_HOSTS(空=回退 task_es_hosts)
    rag_vector_user: str = ''                   # RAG_VECTOR_USER
    rag_vector_password: str = ''               # RAG_VECTOR_PASSWORD
    rag_vector_api_key: str = ''                # RAG_VECTOR_API_KEY

    @property
    def api_key(self) -> str:
        """embedding 用的 key:优先 EMBEDDING_API_KEY,dashscope 系回退 DASHSCOPE_API_KEY。"""
        if self.embedding_api_key:
            return self.embedding_api_key
        if (self.embedding_type or '').lower() in ('dashscope', 'tongyi', 'qwen'):
            return self.dashscope_api_key
        return ''

    @property
    def rerank_key(self) -> str:
        return self.rerank_api_key or self.dashscope_api_key


class SandboxSettings(BaseSettings):
    """代码执行沙箱(仅调试层用:转换/分析「已抽取的数据行」)。

    沙箱是独立容器、独立隔离网络、不持有任何连接凭据;worker 先抽好数据,
    只把「数据行 + 转换代码」发进去执行,日志随响应回传。生产 ETL 任务不走沙箱(直跑)。

    .env 示例:
        SANDBOX_ENABLED=true
        SANDBOX_API_URL=http://ezdata-sandbox-dev:8003
        SANDBOX_BEARER_KEY=xxxx
        SANDBOX_TIMEOUT=60
    """

    sandbox_enabled: bool = False                          # SANDBOX_ENABLED(关=本地 exec 兜底)
    sandbox_api_url: str = 'http://ezdata-sandbox-dev:8003'  # SANDBOX_API_URL
    sandbox_bearer_key: str = 'change-me'                  # SANDBOX_BEARER_KEY
    sandbox_timeout: int = 60                              # SANDBOX_TIMEOUT(秒)


class GetConfig:
    """
    获取配置
    """

    def __init__(self) -> None:
        self.parse_cli_args()

    def get_ai_config(self) -> AiSettings:
        """
        获取系统内置 AI 兜底模型配置
        """
        return AiSettings()

    def get_app_config(self) -> AppSettings:
        """
        获取应用配置
        """
        # 实例化应用配置模型
        return AppSettings()

    def get_jwt_config(self) -> JwtSettings:
        """
        获取Jwt配置
        """
        # 实例化Jwt配置模型
        return JwtSettings()

    def get_database_config(self) -> DataBaseSettings:
        """
        获取数据库配置
        """
        # 实例化数据库配置模型
        return DataBaseSettings()

    def get_redis_config(self) -> RedisSettings:
        """
        获取Redis配置
        """
        # 实例化Redis配置模型
        return RedisSettings()

    def get_log_config(self) -> LogSettings:
        """
        获取日志配置
        """
        return LogSettings()

    def get_transport_crypto_config(self) -> TransportCryptoSettings:
        """
        获取传输层加解密配置
        """
        return TransportCryptoSettings()

    def get_celery_config(self) -> CelerySettings:
        """
        获取Celery执行器配置
        """
        return CelerySettings()

    def get_task_log_config(self) -> TaskLogSettings:
        """
        获取任务执行日志配置
        """
        return TaskLogSettings()

    def get_gen_config(self) -> GenSettings:
        """
        获取代码生成配置
        """
        # 实例化代码生成配置
        return GenSettings()

    def get_upload_config(self) -> UploadSettings:
        """
        获取上传配置
        """
        # 实例上传配置
        return UploadSettings()

    def get_storage_config(self) -> StorageSettings:
        """
        获取存储配置
        """
        return StorageSettings()

    @staticmethod
    def parse_cli_args() -> None:
        """
        解析命令行参数
        """
        # 检查是否在alembic环境中运行，如果是则跳过参数解析
        if 'alembic' in sys.argv[0] or any('alembic' in arg for arg in sys.argv):
            ini_config = configparser.ConfigParser()
            ini_config.read('alembic.ini', encoding='utf-8')
            if 'settings' in ini_config:
                # 获取env选项
                env_value = ini_config['settings'].get('env')
                os.environ['APP_ENV'] = env_value if env_value else 'dev'
        elif 'uvicorn' in sys.argv[0]:
            # 使用uvicorn启动时，命令行参数需要按照uvicorn的文档进行配置，无法自定义参数
            pass
        else:
            # 使用argparse定义命令行参数
            parser = argparse.ArgumentParser(description='命令行参数')
            parser.add_argument('--env', type=str, default='', help='运行环境')
            # 解析命令行参数
            args, _ = parser.parse_known_args()
            # 设置环境变量，如果未设置命令行参数，默认APP_ENV为dev
            os.environ['APP_ENV'] = args.env if args.env else 'dev'
        # 读取运行环境
        run_env = os.environ.get('APP_ENV', '')
        # 运行环境未指定时默认加载.env.dev
        env_file = '.env.dev'
        # 运行环境不为空时按命令行参数加载对应.env文件
        if run_env != '':
            env_file = f'.env.{run_env}'
        # 加载配置
        load_dotenv(env_file)


# 实例化获取配置类
get_config = GetConfig()
# 应用配置
AppConfig = get_config.get_app_config()
# Jwt配置
JwtConfig = get_config.get_jwt_config()
# 数据库配置
DataBaseConfig = get_config.get_database_config()
# Redis配置
RedisConfig = get_config.get_redis_config()
# 日志配置
LogConfig = get_config.get_log_config()
# 传输层加解密配置
TransportCryptoConfig = get_config.get_transport_crypto_config()
# Celery执行器配置
CeleryConfig = get_config.get_celery_config()
# 任务执行日志配置
TaskLogConfig = get_config.get_task_log_config()
# 代码生成配置
GenConfig = get_config.get_gen_config()
# 上传配置
UploadConfig = get_config.get_upload_config()
# 存储配置
StorageConfig = get_config.get_storage_config()
# 系统内置 AI 兜底模型配置
AiConfig = get_config.get_ai_config()
# 知识库(RAG)兜底配置
RagConfig = RagSettings()
# 代码执行沙箱(调试层)配置
SandboxConfig = SandboxSettings()
