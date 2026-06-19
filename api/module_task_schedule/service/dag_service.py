import json
import uuid
from datetime import datetime
from typing import Any

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_task_schedule.dag_util import validate_graph
from module_task_schedule.dao.dag_dao import DagGraphDao
from module_task_schedule.entity.do.task_do import DagGraph, Task, TaskInstance
from utils.page_util import PageUtil

EMPTY_GRAPH = {'nodes': [], 'edges': [], 'viewport': {}}


def _graph_to_dict(do: DagGraph | None) -> dict:
    if not do or not do.graph:
        return dict(EMPTY_GRAPH)
    try:
        return json.loads(do.graph)
    except Exception:
        return dict(EMPTY_GRAPH)


class DagService:
    """DAG 工作流服务:容器 CRUD + 草稿/发布/版本/回滚 + 运行/监控。"""

    # ---------------- 容器(task_type=2)----------------
    @classmethod
    async def get_list(cls, db: AsyncSession, name: str | None, page_num: int, page_size: int, is_page: bool = True) -> Any:
        query = select(Task).where(
            Task.task_type == 2, Task.name.like(f'%{name}%') if name else True
        ).order_by(Task.create_time.desc())
        return await PageUtil.paginate(db, query, page_num, page_size, is_page)

    @classmethod
    async def create(cls, db: AsyncSession, req: Any, operator: str) -> dict:
        try:
            dag_id = uuid.uuid4().hex
            db.add(Task(
                id=dag_id, template_code='', task_type=2, name=req.name, status=1, trigger_type=1,
                run_queue=req.run_queue or 'default', remark=req.remark,
                create_by=operator, create_time=datetime.now(),
            ))
            # 建空草稿
            await DagGraphDao.add(db, {
                'id': uuid.uuid4().hex, 'dag_task_id': dag_id, 'version': 'draft', 'status': 'draft',
                'graph': json.dumps(EMPTY_GRAPH, ensure_ascii=False), 'create_by': operator, 'create_time': datetime.now(),
            })
            await db.commit()
            return {'id': dag_id}
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def get_detail(cls, db: AsyncSession, dag_task_id: str) -> dict:
        t = (await db.execute(select(Task).where(Task.id == dag_task_id))).scalars().first()
        if not t:
            raise ServiceException(message='DAG 不存在')
        return {
            'id': t.id, 'name': t.name, 'status': t.status, 'triggerType': t.trigger_type,
            'crontab': t.crontab, 'runQueue': t.run_queue, 'runType': t.run_type or 1,
            'retry': t.retry, 'countdown': t.countdown, 'remark': t.remark,
            'publishedVersionId': t.published_version_id,
        }

    @classmethod
    async def update_settings(cls, db: AsyncSession, dag_task_id: str, req: Any, operator: str) -> CrudResponseModel:
        """更新 DAG 本体:名称/状态/触发/运行模式/队列/重试,并维护定时调度。"""
        from module_admin.dao.job_dao import JobDao  # noqa: PLC0415
        from module_admin.entity.vo.job_vo import JobModel  # noqa: PLC0415

        t = (await db.execute(select(Task).where(Task.id == dag_task_id))).scalars().first()
        if not t:
            raise ServiceException(message='DAG 不存在')
        if req.trigger_type == 2 and not (req.crontab or '').strip():
            raise ServiceException(message='定时触发必须填写 Cron 表达式')
        try:
            t.name = req.name
            t.status = req.status
            t.trigger_type = req.trigger_type
            t.crontab = req.crontab
            t.run_queue = req.run_queue or 'default'
            t.run_type = req.run_type or 1
            t.retry = req.retry or 0
            t.countdown = req.countdown or 0
            t.remark = req.remark
            t.update_by = operator
            t.update_time = datetime.now()
            old_job_id = t.job_id
            # 重建调度:先删旧 job
            if old_job_id:
                await JobDao.delete_job_dao(db, JobModel(jobId=old_job_id))
                t.job_id = None
            if req.trigger_type == 2:
                job = JobModel(
                    jobName=f'DAG_{dag_task_id}', jobGroup='default', jobExecutor='default',
                    invokeTarget='module_task_schedule.dispatch.run_dag', jobArgs=str(dag_task_id),
                    cronExpression=req.crontab, misfirePolicy='2', concurrent='1',
                    status='0' if req.status == 1 else '1', createBy=operator, remark=req.remark,
                )
                sys_job = await JobDao.add_job_dao(db, job)
                await db.flush()
                t.job_id = sys_job.job_id
            await db.commit()
            try:
                from config.get_scheduler import SchedulerUtil  # noqa: PLC0415
                await SchedulerUtil.request_scheduler_sync()
            except Exception:  # noqa: BLE001
                pass
            return CrudResponseModel(is_success=True, message='保存成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def delete(cls, db: AsyncSession, ids: str) -> CrudResponseModel:
        try:
            for dag_id in [i for i in ids.split(',') if i]:
                await DagGraphDao.remove_by_dag(db, dag_id)
                t = (await db.execute(select(Task).where(Task.id == dag_id))).scalars().first()
                if t:
                    await db.delete(t)
            await db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    # ---------------- 草稿 ----------------
    @classmethod
    async def get_draft(cls, db: AsyncSession, dag_task_id: str) -> dict:
        draft = await DagGraphDao.get_draft(db, dag_task_id)
        return {'graph': _graph_to_dict(draft)}

    @classmethod
    async def save_draft(cls, db: AsyncSession, dag_task_id: str, graph: dict, operator: str) -> CrudResponseModel:
        # 草稿允许"未完成"但不允许成环(有节点时才校验环)
        if (graph.get('nodes') or []) and (graph.get('edges') or []):
            ok, msg = validate_graph(graph)
            if not ok and '环' in msg:
                raise ServiceException(message=f'保存失败:{msg}')
        try:
            draft = await DagGraphDao.get_draft(db, dag_task_id)
            payload = json.dumps(graph, ensure_ascii=False)
            if draft:
                await DagGraphDao.update(db, draft.id, {'graph': payload})
            else:
                await DagGraphDao.add(db, {
                    'id': uuid.uuid4().hex, 'dag_task_id': dag_task_id, 'version': 'draft', 'status': 'draft',
                    'graph': payload, 'create_by': operator, 'create_time': datetime.now(),
                })
            await db.commit()
            return CrudResponseModel(is_success=True, message='草稿已保存')
        except Exception as e:
            await db.rollback()
            raise e

    # ---------------- 发布 / 版本 / 回滚 ----------------
    @classmethod
    async def publish(cls, db: AsyncSession, dag_task_id: str, remark: str | None, operator: str) -> dict:
        draft = await DagGraphDao.get_draft(db, dag_task_id)
        graph = _graph_to_dict(draft)
        ok, msg = validate_graph(graph)
        if not ok:
            raise ServiceException(message=f'发布失败,图不合法:{msg}')
        try:
            version = datetime.now().strftime('%Y%m%d%H%M%S')
            ver_id = uuid.uuid4().hex
            await DagGraphDao.add(db, {
                'id': ver_id, 'dag_task_id': dag_task_id, 'version': version, 'status': 'published',
                'graph': json.dumps(graph, ensure_ascii=False), 'remark': remark,
                'create_by': operator, 'create_time': datetime.now(),
            })
            t = (await db.execute(select(Task).where(Task.id == dag_task_id))).scalars().first()
            if t:
                t.published_version_id = ver_id
            await db.commit()
            return {'version_id': ver_id, 'version': version}
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def list_versions(cls, db: AsyncSession, dag_task_id: str) -> list[dict]:
        t = (await db.execute(select(Task).where(Task.id == dag_task_id))).scalars().first()
        published_id = t.published_version_id if t else None
        out = []
        for v in await DagGraphDao.list_versions(db, dag_task_id):
            out.append({
                'id': v.id, 'version': v.version, 'status': v.status, 'remark': v.remark,
                'createBy': v.create_by, 'createTime': v.create_time,
                'current': v.id == published_id,
            })
        return out

    @classmethod
    async def get_version_graph(cls, db: AsyncSession, version_id: str) -> dict:
        v = await DagGraphDao.get_by_id(db, version_id)
        if not v:
            raise ServiceException(message='版本不存在')
        return {'graph': _graph_to_dict(v), 'version': v.version, 'status': v.status}

    @classmethod
    async def rollback(cls, db: AsyncSession, dag_task_id: str, version_id: str) -> CrudResponseModel:
        v = await DagGraphDao.get_by_id(db, version_id)
        if not v or v.dag_task_id != dag_task_id or v.status != 'published':
            raise ServiceException(message='目标版本无效')
        v_version = v.version  # 捕获到本地,避免 commit 后过期惰性加载
        try:
            t = (await db.execute(select(Task).where(Task.id == dag_task_id))).scalars().first()
            if t:
                t.published_version_id = version_id
            await db.commit()
            return CrudResponseModel(is_success=True, message=f'已回滚到版本 {v_version}')
        except Exception as e:
            await db.rollback()
            raise e

    # ---------------- 运行 / 监控 ----------------
    @classmethod
    async def run(cls, db: AsyncSession, dag_task_id: str, source: str = 'published') -> dict:
        t = (await db.execute(select(Task).where(Task.id == dag_task_id))).scalars().first()
        if not t:
            raise ServiceException(message='DAG 不存在')
        if source == 'published' and not t.published_version_id:
            raise ServiceException(message='尚未发布,无法正式运行(可用试运行跑草稿)')

        from module_task_schedule import dispatch  # noqa: PLC0415
        instance_id = await run_in_threadpool(dispatch.run_dag, dag_task_id, source)
        return {'instanceId': instance_id}

    @classmethod
    async def run_node(cls, db: AsyncSession, dag_task_id: str, node_key: str, source: str = 'draft') -> dict:
        from module_task_schedule import dispatch  # noqa: PLC0415
        instance_id = await run_in_threadpool(dispatch.run_single_node, dag_task_id, node_key, source)
        return {'instanceId': instance_id}

    @classmethod
    async def list_runs(cls, db: AsyncSession, dag_task_id: str, limit: int = 50) -> list[dict]:
        """DAG 运行历史(run 实例:task_id=dag,node_id 空)。"""
        runs = list((await db.execute(
            select(TaskInstance).where(
                TaskInstance.task_id == dag_task_id,
                (TaskInstance.node_id.is_(None)) | (TaskInstance.node_id == ''),
            ).order_by(TaskInstance.start_time.desc()).limit(limit)
        )).scalars().all())
        return [cls._inst_dict(r) for r in runs]

    @classmethod
    async def node_history(cls, db: AsyncSession, dag_task_id: str, node_key: str, limit: int = 50) -> list[dict]:
        """某节点在该 DAG 历次运行中的执行记录。"""
        items = list((await db.execute(
            select(TaskInstance).where(
                TaskInstance.task_id == dag_task_id, TaskInstance.node_id == node_key,
            ).order_by(TaskInstance.start_time.desc()).limit(limit)
        )).scalars().all())
        return [dict(cls._inst_dict(i), runId=i.parent_id) for i in items]

    @classmethod
    async def run_nodes_status(cls, db: AsyncSession, run_id: str) -> dict:
        """一次运行的节点状态(按 parent_id 聚合)+ DAG run 自身。"""
        run = (await db.execute(select(TaskInstance).where(TaskInstance.id == run_id))).scalars().first()
        nodes = list((await db.execute(
            select(TaskInstance).where(TaskInstance.parent_id == run_id).order_by(TaskInstance.start_time)
        )).scalars().all())
        return {
            'run': cls._inst_dict(run) if run else None,
            'nodes': [cls._inst_dict(n) for n in nodes],
        }

    @staticmethod
    def _inst_dict(i: TaskInstance) -> dict:
        return {
            'id': i.id, 'nodeId': i.node_id, 'name': i.name, 'status': i.status, 'worker': i.worker,
            'retryNum': i.retry_num, 'progress': i.progress, 'startTime': i.start_time, 'endTime': i.end_time,
            'closed': i.closed, 'result': i.result,
        }
