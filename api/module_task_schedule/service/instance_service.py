from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_task_schedule.dao.instance_dao import TaskInstanceDao
from module_task_schedule.dao.log_dao import TaskLogDao
from module_task_schedule.entity.vo.task_vo import TaskInstanceModel, TaskInstancePageQueryModel
from utils.common_util import CamelCaseUtil


class TaskInstanceService:
    """
    任务实例(执行记录)服务层
    """

    @classmethod
    async def get_instance_list_services(
        cls, query_db: AsyncSession, query_object: TaskInstancePageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """获取执行记录列表service"""
        return await TaskInstanceDao.get_instance_list(query_db, query_object, is_page)

    @classmethod
    async def instance_detail_services(cls, query_db: AsyncSession, instance_id: str) -> TaskInstanceModel:
        """获取执行记录详情service"""
        instance = await TaskInstanceDao.get_instance_by_id(query_db, instance_id)
        return TaskInstanceModel(**CamelCaseUtil.transform_result(instance)) if instance else TaskInstanceModel()

    @classmethod
    async def delete_instance_services(cls, query_db: AsyncSession, instance_ids: str) -> CrudResponseModel:
        """删除执行记录service(同时删除其执行明细日志)"""
        if not instance_ids:
            raise ServiceException(message='传入实例id为空')
        id_list = [i for i in instance_ids.split(',') if i]
        try:
            await TaskInstanceDao.delete_instance_dao(query_db, id_list)
            await TaskLogDao.delete_task_log_by_uuid(query_db, id_list)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def stop_instance_services(cls, query_db: AsyncSession, instance_id: str) -> CrudResponseModel:
        """终止正在运行的执行实例(向 Celery 发送 revoke)"""
        instance = await TaskInstanceDao.get_instance_by_id(query_db, instance_id)
        if not instance or not instance.id:
            raise ServiceException(message='执行实例不存在')
        try:
            from config.celery_app import celery_app

            celery_app.control.revoke(instance_id, terminate=True, signal='SIGTERM')
            return CrudResponseModel(is_success=True, message='终止指令已发送')
        except Exception as e:  # noqa: BLE001
            raise ServiceException(message=f'终止任务失败: {e}')
