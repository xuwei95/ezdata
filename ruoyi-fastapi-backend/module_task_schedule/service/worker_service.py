"""
Worker 管理服务(不依赖 Flower)

全部基于 Celery 原生 control/inspect 广播 API：
- 列表/信息：inspect().stats() + active_queues() + active() + control.ping()
- 动态订阅队列：control.add_consumer / cancel_consumer
- 伸缩并发：control.pool_grow / pool_shrink / autoscale（仅 prefork 池有效）
- 当前运行任务：inspect().active()

说明：control/inspect 经 broker 广播并按 timeout 收集应答，destination 指定单个 worker；
离线 worker 不应答。pool_grow/shrink/autoscale 在 solo 池下无效(返回空)。
"""

from typing import Any

from exceptions.exception import ServiceException

# inspect 为广播命令，会等待 timeout 秒收集所有 worker 的应答(无法提前返回)，
# 故每个 inspect 调用约耗时 timeout 秒。列表用较短超时并复用单连接、去掉冗余 ping 以提速。
_TIMEOUT = 1.0
_LIST_TIMEOUT = 0.8


class WorkerService:
    """Celery Worker 运维服务"""

    @classmethod
    def _control(cls) -> Any:
        from config.celery_app import celery_app

        return celery_app.control

    @classmethod
    def get_worker_list(cls) -> list[dict[str, Any]]:
        """汇总在线 worker 的基础信息、消费队列、运行中任务数"""
        from config.celery_app import celery_app

        # 复用单条 broker 连接执行 3 个 inspect(stats/active_queues/active)，避免重复建连
        with celery_app.connection_or_acquire() as conn:
            insp = celery_app.control.inspect(timeout=_LIST_TIMEOUT, connection=conn)
            stats = insp.stats() or {}
            queues = insp.active_queues() or {}
            active = insp.active() or {}

        names = set(stats) | set(queues) | set(active)
        workers: list[dict[str, Any]] = []
        for name in sorted(names):
            st = stats.get(name, {})
            pool = st.get('pool', {}) if isinstance(st, dict) else {}
            act = active.get(name, []) or []
            workers.append(
                {
                    'name': name,
                    # stats 有应答即视为在线
                    'status': 'online' if name in stats else 'offline',
                    'maxConcurrency': pool.get('max-concurrency'),
                    'processes': pool.get('processes'),
                    'queues': [q.get('name') for q in (queues.get(name) or [])],
                    'activeCount': len(act),
                    'activeTasks': [cls._fmt_task(t, name) for t in act],
                    'total': st.get('total') if isinstance(st, dict) else None,
                    'pid': st.get('pid') if isinstance(st, dict) else None,
                }
            )
        return workers

    @classmethod
    def get_active_tasks(cls, worker: str | None = None) -> list[dict[str, Any]]:
        """获取当前正在运行的任务(可按 worker 过滤)"""
        insp = cls._control().inspect(destination=[worker] if worker else None, timeout=_TIMEOUT)
        active = insp.active() or {}
        result: list[dict[str, Any]] = []
        for wname, tasks in active.items():
            for t in tasks or []:
                result.append(cls._fmt_task(t, wname))
        return result

    @classmethod
    def _fmt_task(cls, t: dict[str, Any], worker: str) -> dict[str, Any]:
        return {
            'id': t.get('id'),
            'name': t.get('name'),
            'args': t.get('args'),
            'kwargs': t.get('kwargs'),
            'worker': t.get('hostname') or worker,
            'timeStart': t.get('time_start'),
        }

    @classmethod
    def _require_reply(cls, reply: list | None, worker: str, action: str) -> dict[str, Any]:
        """校验广播应答：无应答视为 worker 离线/不支持，抛业务异常"""
        if not reply:
            raise ServiceException(message=f'{action}失败：worker [{worker}] 无应答(可能离线，或当前池不支持该操作)')
        # reply 形如 [{'celery@host': {'ok': '...'}}]
        for item in reply:
            for wname, res in item.items():
                if isinstance(res, dict) and 'error' in res:
                    raise ServiceException(message=f'{action}失败：{res.get("error")}')
        return {'reply': reply}

    @classmethod
    def add_consumer(cls, worker: str, queue: str) -> dict[str, Any]:
        reply = cls._control().add_consumer(queue, destination=[worker], reply=True, timeout=_TIMEOUT)
        return cls._require_reply(reply, worker, '增加消费队列')

    @classmethod
    def cancel_consumer(cls, worker: str, queue: str) -> dict[str, Any]:
        reply = cls._control().cancel_consumer(queue, destination=[worker], reply=True, timeout=_TIMEOUT)
        return cls._require_reply(reply, worker, '移除消费队列')

    @classmethod
    def pool_grow(cls, worker: str, n: int) -> dict[str, Any]:
        reply = cls._control().pool_grow(int(n), destination=[worker], reply=True, timeout=_TIMEOUT)
        return cls._require_reply(reply, worker, '增加并发')

    @classmethod
    def pool_shrink(cls, worker: str, n: int) -> dict[str, Any]:
        reply = cls._control().pool_shrink(int(n), destination=[worker], reply=True, timeout=_TIMEOUT)
        return cls._require_reply(reply, worker, '减少并发')

    @classmethod
    def autoscale(cls, worker: str, max_c: int, min_c: int) -> dict[str, Any]:
        reply = cls._control().autoscale(int(max_c), int(min_c), destination=[worker], reply=True, timeout=_TIMEOUT)
        return cls._require_reply(reply, worker, '设置弹性并发')
