"""可选可观测性接入:OpenTelemetry → Langfuse / 任意 OTLP 后端。

默认**关闭**;仅当配置了 Langfuse 或通用 OTLP 环境变量时才启用,零侵入、缺依赖优雅降级。

启用方式(二选一):
  1) Langfuse:LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY(+ LANGFUSE_BASE_URL,自建必填;
     不填默认 https://cloud.langfuse.com)。自动拼 OTLP 端点 /api/public/otel/v1/traces + Basic 鉴权。
  2) 通用 OTLP:OTEL_EXPORTER_OTLP_ENDPOINT(+ 可选 OTEL_EXPORTER_OTLP_HEADERS="k=v,k2=v2")。

采集内容:
  - AgnoInstrumentor(核心):agent / 工具调用 / LLM 生成 span,含 token 用量;
  - 可选全栈(OBS_INSTRUMENT_STACK=true):FastAPI 请求 / SQLAlchemy / httpx 出站 span。

依赖(未装则本模块自动跳过,不影响主程序):
  opentelemetry-sdk / opentelemetry-exporter-otlp-proto-http / openinference-instrumentation-agno
  (全栈可选:opentelemetry-instrumentation-{fastapi,sqlalchemy,httpx})

备注:MCP 路径在独立 asyncio task 内跑 agent(见 chat.mcp_bridge);asyncio.create_task 会自动
复制当前 contextvars(OTel context 即基于 contextvars),故父子 span 链路自动传播,无需特殊处理。
"""

from __future__ import annotations

import base64
import os
from typing import TYPE_CHECKING

from utils.log_util import logger

if TYPE_CHECKING:
    from fastapi import FastAPI

_initialized = False


def _resolve_otlp_target() -> tuple[str, dict[str, str]] | None:
    """从环境变量解析 (traces_endpoint, headers);未配置返回 None。"""
    pub = os.environ.get('LANGFUSE_PUBLIC_KEY')
    sec = os.environ.get('LANGFUSE_SECRET_KEY')
    generic = os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT')

    if pub and sec:
        base = (os.environ.get('LANGFUSE_BASE_URL') or os.environ.get('LANGFUSE_HOST') or 'https://cloud.langfuse.com').rstrip('/')
        endpoint = f'{base}/api/public/otel/v1/traces'
        auth = base64.b64encode(f'{pub}:{sec}'.encode()).decode()
        return endpoint, {'Authorization': f'Basic {auth}'}

    if generic:
        endpoint = generic.rstrip('/')
        if not endpoint.endswith('/v1/traces'):
            endpoint = f'{endpoint}/v1/traces'
        headers: dict[str, str] = {}
        raw = os.environ.get('OTEL_EXPORTER_OTLP_HEADERS', '')
        for pair in raw.split(','):
            if '=' in pair:
                k, v = pair.split('=', 1)
                headers[k.strip()] = v.strip()
        return endpoint, headers

    return None


def init_observability(app: FastAPI | None = None) -> bool:
    """按环境变量启用 OTel → Langfuse/OTLP。未配置或缺依赖则返回 False(不启用,不报错)。幂等。"""
    global _initialized
    if _initialized:
        return True

    target = _resolve_otlp_target()
    if target is None:
        return False  # 未配置 → 默认关
    endpoint, headers = target

    try:
        import opentelemetry.trace as ot
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except Exception as e:
        logger.warning(f'[otel] 已配置可观测性但缺 opentelemetry 依赖,跳过:{e}')
        return False

    service = os.environ.get('OTEL_SERVICE_NAME', 'ezdata')
    environment = os.environ.get('OTEL_DEPLOYMENT_ENVIRONMENT') or os.environ.get('APP_ENV', 'dev')
    provider = TracerProvider(
        resource=Resource.create({'service.name': service, 'deployment.environment': environment})
    )
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, headers=headers or None)))
    ot.set_tracer_provider(provider)

    # 核心:agno instrumentor(agent/工具/LLM 生成 span)
    try:
        from openinference.instrumentation.agno import AgnoInstrumentor

        AgnoInstrumentor().instrument(tracer_provider=provider)
    except Exception as e:
        logger.warning(f'[otel] AgnoInstrumentor 未启用(缺 openinference-instrumentation-agno?):{e}')

    # 可选:全栈 span(默认关,OBS_INSTRUMENT_STACK=true 开)
    if (os.environ.get('OBS_INSTRUMENT_STACK', '') or '').lower() in ('1', 'true', 'yes'):
        _instrument_stack(app, provider)

    _initialized = True
    logger.info(f'[otel] 可观测性已启用 → {endpoint}(service={service}, env={environment})')
    return True


def _instrument_stack(app: FastAPI | None, provider) -> None:
    """可选:FastAPI / SQLAlchemy / httpx 自动埋点。单个失败只告警、不影响其余。"""
    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
        except Exception as e:
            logger.warning(f'[otel] FastAPI 埋点跳过:{e}')
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(tracer_provider=provider)
    except Exception as e:
        logger.warning(f'[otel] SQLAlchemy 埋点跳过:{e}')
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        HTTPXClientInstrumentor().instrument(tracer_provider=provider)
    except Exception as e:
        logger.warning(f'[otel] httpx 埋点跳过:{e}')
