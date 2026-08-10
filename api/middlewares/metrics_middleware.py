import time

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Prometheus HTTP 指标:请求数 + 耗时。path 用路由模板(如 /data/model/{m_id}/query),
    避免把 ID 拼进 label 造成基数爆炸;未匹配路由归一为 <unmatched>。"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path == '/metrics':  # 不给自身埋点
            return await call_next(request)
        t0 = time.monotonic()
        status = 500
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            route = request.scope.get('route')
            path = getattr(route, 'path', None) or '<unmatched>'
            try:
                from common import metrics

                metrics.observe_http(request.method, path, status, time.monotonic() - t0)
            except Exception:
                pass


def add_metrics_middleware(app: FastAPI) -> None:
    app.add_middleware(MetricsMiddleware)
