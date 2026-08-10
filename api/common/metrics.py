"""Prometheus 指标:HTTP / Celery / 运行时(DB 池、队列积压)。

- HTTP:中间件调 observe_http();Celery:信号调 inc_celery_task/observe_celery_duration()。
- 运行时 Gauge(DB 池、队列长度)在 /metrics 被抓取时现算(_refresh_runtime)。
- /metrics 由 metrics_response() 输出标准 exposition 文本。
单进程直采即可;多 uvicorn/worker 进程需设 PROMETHEUS_MULTIPROC_DIR 走 multiprocess 模式(部署时再开)。
"""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

# —— HTTP ——
http_requests_total = Counter(
    'ezdata_http_requests_total', 'HTTP 请求数', ['method', 'path', 'status']
)
http_request_duration_seconds = Histogram(
    'ezdata_http_request_duration_seconds', 'HTTP 请求耗时(秒)', ['method', 'path']
)

# —— Celery ——
celery_task_total = Counter(
    'ezdata_celery_task_total', 'Celery 任务计数', ['name', 'status']
)
celery_task_duration_seconds = Histogram(
    'ezdata_celery_task_duration_seconds', 'Celery 任务耗时(秒)', ['name']
)

# —— 运行时 Gauge(抓取时现算) ——
db_pool_checked_out = Gauge('ezdata_db_pool_checked_out', '数据库连接池已借出连接数')
db_pool_size = Gauge('ezdata_db_pool_size', '数据库连接池大小')
celery_queue_pending = Gauge('ezdata_celery_queue_pending', '各队列待处理任务数', ['queue'])


def observe_http(method: str, path: str, status: int, duration: float) -> None:
    http_requests_total.labels(method=method, path=path, status=str(status)).inc()
    http_request_duration_seconds.labels(method=method, path=path).observe(duration)


def inc_celery_task(name: str, status: str) -> None:
    celery_task_total.labels(name=name, status=status).inc()


def observe_celery_duration(name: str, duration: float) -> None:
    celery_task_duration_seconds.labels(name=name).observe(duration)


def _refresh_runtime() -> None:
    """抓取时刷新运行时 Gauge(尽力而为,任一失败不影响其余指标)。"""
    try:
        from config.database import async_engine

        pool = async_engine.sync_engine.pool
        db_pool_checked_out.set(pool.checkedout())
        db_pool_size.set(pool.size())
    except Exception:
        pass
    try:
        import redis

        from config.env import CeleryConfig, RedisConfig

        auth = {}
        if RedisConfig.redis_password:
            auth = {'username': RedisConfig.redis_username or None, 'password': RedisConfig.redis_password}
        r = redis.Redis(
            host=RedisConfig.redis_host, port=RedisConfig.redis_port,
            db=CeleryConfig.celery_redis_database, socket_timeout=2, **auth,
        )
        for q in CeleryConfig.queue_list:
            try:
                celery_queue_pending.labels(queue=q).set(r.llen(q))
            except Exception:
                pass
        r.close()
    except Exception:
        pass


def metrics_response() -> tuple[bytes, str]:
    """返回 (exposition 文本, content_type),供 /metrics 端点直接回。"""
    _refresh_runtime()
    return generate_latest(), CONTENT_TYPE_LATEST
