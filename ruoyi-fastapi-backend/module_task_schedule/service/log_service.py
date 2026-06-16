from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from config.env import TaskLogConfig
from exceptions.exception import ServiceException
from module_task_schedule.dao.log_dao import TaskLogDao
from module_task_schedule.entity.vo.task_vo import TaskLogQueryModel


class TaskLogService:
    """
    任务执行明细日志服务层(db 后端)

    执行记录(谁/何时/成败/起止/进度)由 task_instance 承载；
    本服务只负责"执行明细日志"(task_log)的查询与可见性判断。
    """

    @classmethod
    def is_viewable(cls) -> bool:
        """任务执行明细日志是否支持 UI 在线查看(file 后端不支持)"""
        return TaskLogConfig.task_log_type != 'file'

    @classmethod
    async def get_task_log_list_services(
        cls, query_db: AsyncSession, query_object: TaskLogQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """获取执行明细日志列表service"""
        if not cls.is_viewable():
            raise ServiceException(
                message=f'当前任务执行日志后端为 {TaskLogConfig.task_log_type}，不支持在线查看，请查看日志文件'
            )
        if not query_object.task_uuid:
            raise ServiceException(message='缺少实例ID')
        # 读取后端与写入后端(TaskLogConfig.task_log_type)对齐:es 走 ES 读取层,其余走 db。
        # ES 客户端为同步阻塞,放入线程池执行避免阻塞事件循环(轮询每 3s 调用)。
        if TaskLogConfig.task_log_type == 'es':
            from fastapi.concurrency import run_in_threadpool

            from module_task_schedule.dao.es_log_dao import EsTaskLogDao

            return await run_in_threadpool(EsTaskLogDao.get_task_log_list, query_object)
        return await TaskLogDao.get_task_log_list(query_db, query_object, is_page)
