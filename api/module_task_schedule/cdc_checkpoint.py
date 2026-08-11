"""
CDC 位点(checkpoint)持久化：把 MySQL binlog 的 (log_file, log_pos) 存到 Redis，
供流式取数重启后断点续读(解决 GitHub issue #19 的重复读/丢事件)。

供 Celery worker 同步上下文调用：模块级同步 redis 客户端(进程内单例)。
Redis 不可用/未配置时所有读操作安全降级为 None、写操作静默跳过，绝不阻断任务执行。

保证等级 at-least-once：位点在「一批装载成功后」才提交，崩在 load 成功与存位点之间会重放最后一批；
要「有效一次」，CDC 装载建议用 load.mode='merge' + id_field(dlt 按主键 upsert，重放不产重复行)。
"""

import json
import os
from typing import Any

from loguru import logger as loguru_logger

from config.env import RedisConfig

# 位点独立 redis db(默认复用 app 缓存库);长 TTL 让死任务位点自动过期、活跃任务每批刷新
_CKPT_REDIS_DB = int(os.environ.get('CDC_REDIS_DB') or RedisConfig.redis_database)
_CKPT_TTL = int(os.environ.get('CDC_CKPT_TTL') or 2592000)  # 30 天

_KEY_PREFIX = 'ezdata:cdc:ckpt'

_client: Any = None
_client_inited = False


def _redis() -> Any:
    """进程内单例同步 redis 客户端;初始化失败返回 None(调用方据此降级)。"""
    global _client, _client_inited
    if _client_inited:
        return _client
    _client_inited = True
    try:
        import redis

        _client = redis.Redis(
            host=RedisConfig.redis_host,
            port=RedisConfig.redis_port,
            username=RedisConfig.redis_username or None,
            password=RedisConfig.redis_password or None,
            db=_CKPT_REDIS_DB,
            encoding='utf-8',
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3,
        )
    except Exception as e:
        loguru_logger.warning(f'CDC 位点 redis 初始化失败，断点续读降级为无位点: {e}')
        _client = None
    return _client


def ckpt_key(task_id: str | None, datasource_code: str | None, obj: str | None) -> str:
    """位点 key：按 任务 + 数据源 + 对象(表/topic) 维度。task_id 跨重启/重试稳定。"""
    return f'{_KEY_PREFIX}:{task_id or "_"}:{datasource_code or "_"}:{obj or "_all"}'


def load_checkpoint(key: str) -> dict | None:
    """读位点 {log_file, log_pos, ts, instance_id}；无/异常返回 None(降级为无位点)。"""
    client = _redis()
    if client is None:
        return None
    try:
        raw = client.get(key)
        if not raw:
            return None
        data = json.loads(raw)
        if data.get('log_file') and data.get('log_pos') is not None:
            return data
        return None
    except Exception as e:
        loguru_logger.warning(f'CDC 位点读取失败({key})，降级为无位点: {e}')
        return None


def save_checkpoint(key: str, log_file: str, log_pos: int, instance_id: str | None = None) -> None:
    """写位点(带 TTL)。写失败只记 warning，不影响任务(位点丢失最坏是下次从当前位点起)。"""
    client = _redis()
    if client is None or not log_file or log_pos is None:
        return
    try:
        from datetime import datetime, timezone

        payload = json.dumps(
            {
                'log_file': log_file,
                'log_pos': int(log_pos),
                'ts': datetime.now(timezone.utc).isoformat(),
                'instance_id': instance_id,
            },
            ensure_ascii=False,
        )
        client.set(key, payload, ex=_CKPT_TTL)
    except Exception as e:
        loguru_logger.warning(f'CDC 位点写入失败({key}): {e}')


def delete_checkpoint(key: str) -> None:
    """清位点(任务删除/重置时用)。"""
    client = _redis()
    if client is None:
        return
    try:
        client.delete(key)
    except Exception as e:
        loguru_logger.warning(f'CDC 位点删除失败({key}): {e}')
