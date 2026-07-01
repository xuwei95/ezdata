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

    @staticmethod
    def _validate_cron(crontab: str) -> None:
        """校验 Cron 表达式合法(fail-fast):非法则直接拒绝,避免坏表达式落库后拖累调度器同步。"""
        from config.get_scheduler import MyCronTrigger  # noqa: PLC0415

        try:
            MyCronTrigger.from_crontab(crontab)
        except Exception as e:  # noqa: BLE001
            raise ServiceException(message=f'Cron 表达式非法: {crontab}({e})') from e

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
                cls._validate_cron(page_object.crontab)
                task.job_id = await cls._create_schedule(query_db, page_object)
            await query_db.commit()
            await cls._request_scheduler_sync()
            return CrudResponseModel(is_success=True, message='新增成功', result={'id': page_object.id})
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
                cls._validate_cron(page_object.crontab)
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

    @classmethod
    async def debug_run_services(cls, query_db: AsyncSession, req: Any) -> CrudResponseModel:
        """调试运行:不落任务实例、不投 Celery。后台执行,日志实时写任务日志库,前端按 taskUuid 流式读取。

        SANDBOX_ENABLED 开则发沙箱(env 空、连接随请求注入),关则本进程真实跑;两者日志都写库,体验同正式任务。
        """
        import asyncio

        from module_data import sandbox_client
        from module_task_schedule.task_logger import is_task_log_viewable

        template_code = req.template_code or ''
        runner_type = req.runner_type or 1
        params = req.params or {}
        task_uuid = f'debug-{uuid.uuid4().hex[:12]}'

        use_sandbox = sandbox_client.enabled()
        # ETL 需在持 db 会话时预解密数据源,随请求注入沙箱(沙箱无凭据);其余任务为空
        datasources = (await cls._resolve_debug_datasources(query_db, params)
                       if use_sandbox and template_code == 'DataIntegrationTask' else {})

        # 后台执行,立即返回 taskUuid;日志由沙箱/本地实时写库,前端流式读取
        asyncio.get_running_loop().run_in_executor(
            None, cls._run_debug, task_uuid, template_code, runner_type, req.runner_code,
            params, datasources, use_sandbox, req.timeout,
        )
        return CrudResponseModel(is_success=True, message='调试已触发',
                                 result={'taskUuid': task_uuid, 'logViewable': is_task_log_viewable()})

    @staticmethod
    async def _resolve_debug_datasources(query_db: AsyncSession, params: dict) -> dict:
        """查 ETL 源/目标数据源并解密 secrets 为明文 dict(沙箱无凭据,连接信息随请求注入)。"""
        import json

        from sqlalchemy import select

        from module_data.entity.do.data_do import DataSource
        from utils.crypto_util import CryptoUtil

        extract = params.get('extract') or {}
        load = params.get('load') or {}
        # 原生抽取用 extract.datasource_code(单个);代码取数用 extract.datasource_codes(列表,get_handler 授权源)。
        # 两者都要注入,否则沙箱里解析不到的数据源会回退查应用库(DB_HOST 缺省 127.0.0.1)→ "Can't connect to MySQL"。
        codes = {c for c in (extract.get('datasource_code'), load.get('datasource_code')) if c}
        codes |= {c for c in (extract.get('datasource_codes') or []) if c}
        out: dict[str, Any] = {}
        for code in codes:
            ds = (await query_db.execute(select(DataSource).where(DataSource.code == code))).scalars().first()
            if ds is None:
                raise ServiceException(message=f'数据源不存在: {code}')
            secrets: dict = {}
            if ds.secrets:
                try:
                    secrets = json.loads(CryptoUtil.decrypt(ds.secrets))
                except Exception:  # noqa: BLE001 解密失败按空密钥处理,由 handler 报连接错误
                    secrets = {}
            out[code] = {'source_type': ds.source_type, 'config': ds.config or {}, 'secrets': secrets}
        return out

    @staticmethod
    def _run_debug(task_uuid: str, template_code: str, runner_type: int, runner_code: str | None,
                   params: dict, datasources: dict, use_sandbox: bool, timeout: int | None) -> None:
        """后台线程:执行调试任务,日志实时写库(沙箱注入连接直写 / 本地 TaskLogger),供前端流式读取。"""
        from module_task_schedule.task_logger import get_task_logger

        if use_sandbox:
            from module_data import sandbox_client

            try:
                sandbox_client.execute_task(template_code, params, runner_type, runner_code,
                                            datasources, task_uuid, timeout)
            except Exception as e:  # noqa: BLE001 沙箱连接失败,写一条错误日志供前端查看
                lg = get_task_logger(task_uuid)
                lg.error(f'[调试] 沙箱调用失败: {e}')
                lg.close()
            return

        # 本地兜底(SANDBOX_ENABLED 关):本进程真实跑,用 TaskLogger 写库
        import contextlib
        import io

        from module_task_schedule.runners.base import get_runner

        logger = get_task_logger(task_uuid)
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
                ctx: dict[str, Any] = {'sandbox': True}
                if runner_type == 2:
                    from module_task_schedule.runners.dynamic_runner import DynamicRunner

                    ctx['runner_code'] = runner_code or ''
                    runner = DynamicRunner(params, logger, context=ctx)
                else:
                    runner_cls = get_runner(template_code)
                    if runner_cls is None:
                        raise ValueError(f'未注册的任务类型: {template_code}')
                    runner = runner_cls(params, logger, context=ctx)
                result = runner.run()
            if out.getvalue().strip():
                logger.info(f'[stdout] {out.getvalue().rstrip()}')
            logger.info(f'[执行成功] 返回值: {result}')
        except Exception as e:  # noqa: BLE001
            logger.exception(f'[执行失败] {type(e).__name__}: {e}')
        finally:
            logger.close()
