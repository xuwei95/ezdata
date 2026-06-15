import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_task_schedule.dao.task_dao import TaskDao
from module_task_schedule.entity.do.task_do import Task
from module_task_schedule.entity.vo.task_vo import (
    DeleteTaskModel,
    EditTaskStatusModel,
    TaskModel,
    TaskPageQueryModel,
)
from utils.common_util import CamelCaseUtil

# 定时任务回调入口(在 sys_job 白名单 module_task* 内)，job_args 为 task_id
_INVOKE_TARGET = 'module_task_schedule.dispatch.run_task'
# 必须与 APScheduler 配置的 jobstore 名一致(默认 'default')，否则 add_scheduler_job 会报
# 'No such job store'，定时任务将无法被调度触发。
_JOB_GROUP = 'default'
# 触发方式：1单次(手动触发) 2定时(交由 APScheduler)
_TRIGGER_CRON = 2
# 任务状态：1启用 0停用
_STATUS_ENABLED = 1


class TaskService:
    """
    任务服务层

    任务的"执行"由 Celery 承载(见 dispatch/celery_tasks)。定时任务额外在 sys_job 上维护一条
    调度记录(invoke_target 指向 dispatch.run_task)，由 APScheduler 按 crontab 触发后投递 Celery；
    APScheduler 会周期性地从 sys_job 表同步调度，故本服务只需维护 sys_job 行并请求一次同步。
    """

    @classmethod
    async def get_task_list_services(
        cls, query_db: AsyncSession, query_object: TaskPageQueryModel, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """获取任务列表service"""
        return await TaskDao.get_task_list(query_db, query_object, is_page)

    @classmethod
    async def task_detail_services(cls, query_db: AsyncSession, task_id: str) -> TaskModel:
        """获取任务详情service"""
        task = await TaskDao.get_task_by_id(query_db, task_id)
        return TaskModel(**CamelCaseUtil.transform_result(task)) if task else TaskModel()

    @classmethod
    def _build_job_model(cls, task: Task | TaskModel, job_id: int | None = None) -> Any:
        """根据任务构建 sys_job 调度记录(camelCase 入参以匹配 JobModel 别名)"""
        from module_admin.entity.vo.job_vo import JobModel

        return JobModel(
            jobId=job_id,
            jobName=f'TASK_{task.id}',
            jobGroup=_JOB_GROUP,
            jobExecutor='default',
            invokeTarget=_INVOKE_TARGET,
            jobArgs=str(task.id),
            cronExpression=task.crontab,
            # misfirePolicy='2'(执行一次/coalesce=True)：调度被延迟而错过若干次触发时，
            # 只补发一次，避免重复触发。切勿用 '3'——其在 get_scheduler 中被映射为
            # misfire_grace_time≈无限 + coalesce=False，会把所有错过的触发一次性补发。
            misfirePolicy='2',
            concurrent='1',
            status='0' if task.status == _STATUS_ENABLED else '1',
            createBy=task.create_by,
            remark=task.remark,
        )

    @classmethod
    async def _create_schedule(cls, query_db: AsyncSession, task: Task) -> int:
        """为定时任务创建 sys_job 调度记录，返回 sys_job 主键"""
        from module_admin.dao.job_dao import JobDao

        sys_job = await JobDao.add_job_dao(query_db, cls._build_job_model(task))
        await query_db.flush()
        return sys_job.job_id

    @classmethod
    async def _remove_schedule(cls, query_db: AsyncSession, job_id: int) -> None:
        """删除任务关联的 sys_job 调度记录"""
        from module_admin.dao.job_dao import JobDao
        from module_admin.entity.vo.job_vo import JobModel

        await JobDao.delete_job_dao(query_db, JobModel(jobId=job_id))

    @classmethod
    async def _request_scheduler_sync(cls) -> None:
        """请求 APScheduler 从数据库同步调度(best-effort)"""
        try:
            from config.get_scheduler import SchedulerUtil

            await SchedulerUtil.request_scheduler_sync()
        except Exception:  # noqa: BLE001 - 调度同步失败不应阻断任务CRUD，下次周期同步会补齐
            pass

    @classmethod
    async def add_task_services(cls, query_db: AsyncSession, page_object: TaskModel) -> CrudResponseModel:
        """新增任务service"""
        page_object.id = uuid.uuid4().hex
        page_object.job_id = None
        try:
            task = await TaskDao.add_task_dao(query_db, page_object)
            # 定时任务：创建 sys_job 调度记录并回填 job_id
            # 注意：用 page_object(已含完整字段)构建 JobModel，避免读取 ORM 对象上
            # 因 server_default 而处于 expired 状态的列(如 remark)触发异步惰性加载报错。
            if page_object.trigger_type == _TRIGGER_CRON:
                if not page_object.crontab:
                    raise ServiceException(message='定时任务必须填写 Cron 表达式')
                task.job_id = await cls._create_schedule(query_db, page_object)
            await query_db.commit()
            await cls._request_scheduler_sync()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_task_services(cls, query_db: AsyncSession, page_object: TaskModel) -> CrudResponseModel:
        """编辑任务service(重建关联的 sys_job 调度记录)"""
        task = await TaskDao.get_task_by_id(query_db, page_object.id)
        if not task or not task.id:
            raise ServiceException(message='任务不存在')
        try:
            # 先移除旧调度
            if task.job_id:
                await cls._remove_schedule(query_db, task.job_id)
                page_object.job_id = None
            # 定时任务重新创建调度
            if page_object.trigger_type == _TRIGGER_CRON:
                if not page_object.crontab:
                    raise ServiceException(message='定时任务必须填写 Cron 表达式')
                page_object.job_id = await cls._create_schedule(query_db, page_object)
            await TaskDao.edit_task_dao(query_db, page_object.model_dump(exclude_unset=True))
            await query_db.commit()
            await cls._request_scheduler_sync()
            return CrudResponseModel(is_success=True, message='修改成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_task_status_services(
        cls, query_db: AsyncSession, page_object: EditTaskStatusModel
    ) -> CrudResponseModel:
        """启用/停用任务service(同步更新关联 sys_job 状态)"""
        task = await TaskDao.get_task_by_id(query_db, page_object.id)
        if not task or not task.id:
            raise ServiceException(message='任务不存在')
        # 先取出需要的值，避免 update 后 ORM 属性 expired 触发异步惰性加载报错
        task_id = task.id
        job_id = task.job_id
        try:
            await TaskDao.edit_task_dao(query_db, {'id': page_object.id, 'status': page_object.status})
            if job_id:
                from module_admin.dao.job_dao import JobDao
                from module_admin.entity.vo.job_vo import JobModel

                sys_status = '0' if page_object.status == _STATUS_ENABLED else '1'
                await JobDao.edit_job_dao(
                    query_db,
                    {'status': sys_status},
                    JobModel(jobId=job_id, jobName=f'TASK_{task_id}', jobGroup=_JOB_GROUP),
                )
            await query_db.commit()
            await cls._request_scheduler_sync()
            return CrudResponseModel(is_success=True, message='操作成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def delete_task_services(cls, query_db: AsyncSession, page_object: DeleteTaskModel) -> CrudResponseModel:
        """删除任务service(同时删除关联的 sys_job 调度记录)"""
        if not page_object.ids:
            raise ServiceException(message='传入任务id为空')
        id_list = [i for i in page_object.ids.split(',') if i]
        try:
            for tid in id_list:
                task = await TaskDao.get_task_by_id(query_db, tid)
                if task and task.built_in == 1:
                    raise ServiceException(message=f'内置任务不可删除: {task.name}')
                if task and task.job_id:
                    await cls._remove_schedule(query_db, task.job_id)
            await TaskDao.delete_task_dao(query_db, id_list)
            await query_db.commit()
            await cls._request_scheduler_sync()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    def get_run_queues(cls) -> list[str]:
        """实时获取当前在线 worker 正在消费的运行队列；无在线 worker 时回退到配置的队列列表。"""
        from config.celery_app import celery_app
        from config.env import CeleryConfig

        live: set[str] = set()
        try:
            active = celery_app.control.inspect(timeout=2).active_queues() or {}
            for queue_list in active.values():
                for q in queue_list:
                    name = q.get('name')
                    if name:
                        live.add(name)
        except Exception:  # noqa: BLE001 - inspect 失败(无 broker/worker)时回退配置
            pass
        if live:
            return sorted(live)
        # 回退：配置的队列列表(至少含默认队列)
        return CeleryConfig.queue_list or [CeleryConfig.celery_default_queue]

    @classmethod
    async def run_task_once_services(cls, query_db: AsyncSession, task_id: str) -> CrudResponseModel:
        """手动执行一次任务(直接投递到 Celery)"""
        task = await TaskDao.get_task_by_id(query_db, task_id)
        if not task or not task.id:
            raise ServiceException(message='任务不存在')
        try:
            from module_task_schedule.dispatch import run_task as dispatch_run_task

            instance_id = dispatch_run_task(task.id)
            return CrudResponseModel(is_success=True, message='已触发执行', result={'instanceId': instance_id})
        except Exception as e:  # noqa: BLE001
            raise ServiceException(message=f'触发执行失败: {e}')
