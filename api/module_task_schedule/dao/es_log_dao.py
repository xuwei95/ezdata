"""
任务执行明细日志 Elasticsearch 读取层(task_log_type=es 时使用)

写入由 task_logger.EsTaskLogWriter 负责,文档结构为::

    {'task_uuid': ..., 'level': ..., 'content': ..., '@timestamp': <ISO微秒时间戳>}

读取与 db 后端(TaskLogDao)对齐同一契约:首次取最近 N 条(正序),增量按游标续拉(正序追加),
每行返回 cursor 供前端回传。db 游标=自增id;es 没有自增id,改用 @timestamp 作游标:

- @timestamp 由 datetime.isoformat() 写入,含微秒;单个实例日志在同一进程顺序写入,
  同一微秒写两条几乎不可能,故 range {gt: cursor} 既不丢也不重(唯一理论边界:同微秒)。
- @timestamp 需在索引中映射为 date 类型、task_uuid 映射为可精确匹配(keyword)。动态映射通常
  满足(字符串→text+keyword、ISO串→date);若自定义索引模板,请保证这两点,否则 term/range/sort 失效。

注意:ES 客户端调用为同步阻塞,service 层通过 run_in_threadpool 调用以避免阻塞事件循环。
"""

from typing import Any

from loguru import logger as loguru_logger

from common.vo import PageModel
from config.env import TaskLogConfig
from module_task_schedule.entity.vo.task_vo import TaskLogQueryModel

# 单次增量拉取上限:与 db 后端一致,防止突发日志一次性拉爆;下一轮按新游标续拉,不丢日志
_MAX_INCREMENTAL = 2000


class EsTaskLogDao:
    """任务执行明细日志 ES 读取层"""

    _client: Any = None

    @classmethod
    def _get_client(cls) -> Any:
        """惰性构建并缓存 ES 客户端(未启用 es 时无需安装 elasticsearch 依赖)"""
        if cls._client is None:
            from elasticsearch import Elasticsearch

            es_kwargs: dict[str, Any] = {'hosts': [h for h in TaskLogConfig.task_es_hosts.split(',') if h]}
            if TaskLogConfig.task_es_username:
                es_kwargs['http_auth'] = (TaskLogConfig.task_es_username, TaskLogConfig.task_es_password)
            cls._client = Elasticsearch(**es_kwargs)
        return cls._client

    @classmethod
    def get_task_log_list(cls, query_object: TaskLogQueryModel) -> PageModel:
        """获取某执行实例的执行明细日志(与 db 后端契约一致,按时间正序返回)"""
        index = TaskLogConfig.task_es_index
        filters: list[dict[str, Any]] = [{'term': {'task_uuid.keyword': query_object.task_uuid}}]
        try:
            client = cls._get_client()
            if query_object.after is not None:
                # 增量:仅取 @timestamp 大于游标的新日志,按时间正序,供控制台持续追加。
                # after 为空串表示从头追加(首次实例尚无日志时):不加 range 下界,按正序取(上限 2000)。
                if str(query_object.after).strip():
                    filters.append({'range': {'@timestamp': {'gt': query_object.after}}})
                body = {
                    'query': {'bool': {'filter': filters}},
                    'sort': [{'@timestamp': 'asc'}],
                    'size': _MAX_INCREMENTAL,
                }
                hits = client.search(index=index, body=body).get('hits', {}).get('hits', [])
                rows = [cls._to_row(h) for h in hits]
            else:
                # 首次/重置:按时间倒序取最近 N 条,再反转为正序展示
                limit = query_object.page_size or 100
                body = {
                    'query': {'bool': {'filter': filters}},
                    'sort': [{'@timestamp': 'desc'}],
                    'size': limit,
                }
                hits = client.search(index=index, body=body).get('hits', {}).get('hits', [])
                rows = [cls._to_row(h) for h in reversed(hits)]
        except Exception as e:
            # 索引尚未创建(无日志)/连接异常等:返回空,UI 显示「暂无日志」,不影响轮询
            loguru_logger.warning(f'查询ES执行明细日志失败(返回空): {e}')
            rows = []
        return PageModel(rows=rows, pageNum=1, pageSize=len(rows), total=len(rows), hasNext=False)

    @staticmethod
    def _to_row(hit: dict[str, Any]) -> dict[str, Any]:
        """ES 命中文档 -> 与 db 后端一致的 camelCase 行(含增量游标 cursor=@timestamp)"""
        src = hit.get('_source', {})
        ts = src.get('@timestamp')
        return {
            'id': None,
            'taskUuid': src.get('task_uuid'),
            'level': src.get('level'),
            'content': src.get('content'),
            'createTime': ts,
            'cursor': ts,
        }
