"""
告警中心服务层

- 异步 CRUD：供策略/记录管理接口使用。
- handle_task_fail_alert_sync：供 Celery worker(同步上下文)在任务失败/重试耗尽时调用，
  按任务绑定的策略(task.alert_strategy_ids)生成告警记录并多渠道转发。
  接口不强绑定任务实现，便于其他业务(监控等)复用。
"""

import json
from datetime import datetime
from typing import Any

from loguru import logger as loguru_logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_alert.channels.base import dispatch_forward
from module_alert.dao.alert_dao import AlertRecordDao, AlertStrategyDao
from module_alert.entity.vo.alert_vo import (
    AlertRecordPageQueryModel,
    AlertStrategyModel,
    AlertStrategyPageQueryModel,
    DeleteAlertRecordModel,
    DeleteAlertStrategyModel,
    EditAlertStatusModel,
)
from module_task_schedule.sync_db import get_sync_session_local
from utils.common_util import CamelCaseUtil


def _parse_json(text: str | None, default: Any) -> Any:
    if not text:
        return default
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return default


class AlertStrategyService:
    """告警策略服务层"""

    @classmethod
    async def get_strategy_list_services(
        cls, query_db: AsyncSession, query_object: AlertStrategyPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        return await AlertStrategyDao.get_strategy_list(query_db, query_object, is_page)

    @classmethod
    async def strategy_detail_services(cls, query_db: AsyncSession, strategy_id: int) -> AlertStrategyModel:
        obj = await AlertStrategyDao.get_strategy_detail_by_id(query_db, strategy_id)
        return AlertStrategyModel(**CamelCaseUtil.transform_result(obj)) if obj else AlertStrategyModel()

    @classmethod
    async def add_strategy_services(cls, query_db: AsyncSession, page_object: AlertStrategyModel) -> CrudResponseModel:
        try:
            await AlertStrategyDao.add_strategy_dao(query_db, page_object)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_strategy_services(cls, query_db: AsyncSession, page_object: AlertStrategyModel) -> CrudResponseModel:
        obj = await AlertStrategyDao.get_strategy_detail_by_id(query_db, page_object.strategy_id)
        if not obj or not obj.strategy_id:
            raise ServiceException(message='告警策略不存在')
        try:
            await AlertStrategyDao.edit_strategy_dao(query_db, page_object.model_dump(exclude_unset=True))
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_strategy_services(
        cls, query_db: AsyncSession, page_object: DeleteAlertStrategyModel
    ) -> CrudResponseModel:
        if not page_object.strategy_ids:
            raise ServiceException(message='传入策略id为空')
        id_list = [int(i) for i in page_object.strategy_ids.split(',') if i]
        try:
            await AlertStrategyDao.delete_strategy_dao(query_db, id_list)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e


class AlertRecordService:
    """告警记录服务层"""

    @classmethod
    async def get_record_list_services(
        cls, query_db: AsyncSession, query_object: AlertRecordPageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        return await AlertRecordDao.get_record_list(query_db, query_object, is_page)

    @classmethod
    async def edit_record_status_services(
        cls, query_db: AsyncSession, page_object: EditAlertStatusModel
    ) -> CrudResponseModel:
        obj = await AlertRecordDao.get_record_detail_by_id(query_db, page_object.alert_id)
        if not obj or not obj.alert_id:
            raise ServiceException(message='告警记录不存在')
        try:
            values: dict[str, Any] = {'alert_id': page_object.alert_id, 'status': page_object.status}
            if page_object.status == 1:
                values['recover_time'] = datetime.now()
            await AlertRecordDao.edit_record_dao(query_db, values)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_record_services(
        cls, query_db: AsyncSession, page_object: DeleteAlertRecordModel
    ) -> CrudResponseModel:
        if not page_object.alert_ids:
            raise ServiceException(message='传入告警id为空')
        id_list = [int(i) for i in page_object.alert_ids.split(',') if i]
        try:
            await AlertRecordDao.delete_record_dao(query_db, id_list)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e


class AlertService:
    """告警中心：失败告警处理入口(同步,供执行层调用)"""

    @classmethod
    def handle_task_fail_alert_sync(
        cls,
        task_id: str,
        instance_id: str,
        worker: str | None,
        retries: int,
        exception: str,
        exception_file: str = '',
        exception_line: str = '',
        task_type: str = 'normal_task',
    ) -> None:
        """任务失败/重试耗尽时触发告警：按任务绑定的策略(task.alert_strategy_ids)生成记录并转发

        告警内容格式参考 ezdata(api/web_apps/alert/strategys/task_alert_strategys.py)。
        """
        from module_task_schedule.entity.do.task_do import Task

        # 任务类型映射(对齐 ezdata)
        task_type_map = {'normal_task': '普通任务', 'dag_task': '任务工作流', 'dag_node_task': '任务工作流节点任务'}

        from common.context import RequestContext

        session_local = get_sync_session_local()
        db = session_local()
        tenant_token = None
        try:
            task = db.execute(select(Task).where(Task.id == task_id)).scalars().first()
            if task is None or not task.alert_strategy_ids:
                return
            # 多租户：按任务所属租户盖章告警记录(Worker 无请求上下文)
            tenant_token = RequestContext.set_current_tenant_id(task.tenant_id)
            strategy_ids = [int(i) for i in str(task.alert_strategy_ids).split(',') if i.strip().isdigit()]
            strategies = AlertStrategyDao.sync_get_enabled_strategies(db, strategy_ids)
            if not strategies:
                return

            task_name = task.name
            content = (
                f'{task_type_map.get(task_type, "普通任务")}失败告警:{task_name} 在重试{retries}次后仍失败。'
                f'任务报错：{exception_file}:{exception_line}:{exception[:500]}'
            )
            for strategy in strategies:
                trigger_conf = _parse_json(strategy.trigger_conf, {})
                forward_conf = _parse_json(strategy.forward_conf, [])
                level = int(trigger_conf.get('level', 0) or 0)
                tags = {
                    'instance_id': instance_id,
                    'worker': worker,
                    'retries': retries,
                    'task_id': task_id,
                    'exception_file': exception_file,
                    'exception_line': exception_line,
                }
                record_values = {
                    'strategy_id': strategy.strategy_id,
                    'title': f'任务执行失败: {task_name}',
                    'content': content,
                    'level': level,
                    'status': 0,
                    'biz': 'scheduler',
                    'source': task_name,
                    'metric': 'task_fail',
                    'tags': json.dumps(tags, ensure_ascii=False),
                    'ext_params': '{}',
                    'create_time': datetime.now(),
                }
                AlertRecordDao.sync_add_record(db, dict(record_values))
                # 转发渠道使用记录内容(record_values 即可作为渠道 payload)
                dispatch_forward(record_values, forward_conf if isinstance(forward_conf, list) else [])
        except Exception as e:
            loguru_logger.error(f'处理任务失败告警异常: {e}')
        finally:
            if tenant_token is not None:
                RequestContext.reset_current_tenant_id(tenant_token)
            db.close()
