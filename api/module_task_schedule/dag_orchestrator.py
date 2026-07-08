"""
DAG 事件驱动编排器(运行在 Celery worker / 同步会话)

- start_dag_run:建 DAG run 实例,锁定要跑的图版本(发布版不可变=快照)
- advance_dag :行锁 + 幂等;找"上游全完成且自身未派发"的节点 → 派发;失败 fail_fast,全完成则成功
- execute_dag_node:执行单个节点(复用 runner 注册表 + 实例生命周期 + 日志)

节点执行走独立 celery 任务 run_dag_node(见 celery_tasks),完成后回调 advance_dag 触发下游。
不改单任务 executor。
"""

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.context import RequestContext
from module_task_schedule.dag_util import build_dag
from module_task_schedule.entity.do.task_do import DagGraph, Task, TaskInstance, TaskTemplate
from module_task_schedule.executor import _upsert_instance
from module_task_schedule.sync_db import get_sync_session_local
from module_task_schedule.task_logger import get_task_logger


def _session() -> Session:
    return get_sync_session_local()()


def _load_graph(db: Session, version_id: str) -> dict:
    g = db.execute(select(DagGraph).where(DagGraph.id == version_id)).scalars().first()
    if not g or not g.graph:
        raise ValueError(f'图版本不存在或为空: {version_id}')
    return json.loads(g.graph)


def _node_map(graph: dict) -> dict[str, dict]:
    return {n['node_key']: n for n in (graph.get('nodes') or [])}


def start_dag_run(dag_run_id: str, dag_task_id: str, source: str, worker: str | None) -> int:
    """建 DAG run 实例,锁定图版本。返回运行模式(1分布式/2单机)。"""
    db = _session()
    tenant_token = None
    try:
        task = db.execute(select(Task).where(Task.id == dag_task_id)).scalars().first()
        if task is None:
            raise ValueError(f'DAG 任务不存在: {dag_task_id}')
        tenant_token = RequestContext.set_current_tenant_id(task.tenant_id)
        run_type = int(task.run_type or 1)
        # 锁定版本
        if source == 'draft':
            ver = (
                db.execute(select(DagGraph).where(DagGraph.dag_task_id == dag_task_id, DagGraph.version == 'draft'))
                .scalars()
                .first()
            )
        else:
            ver = db.execute(select(DagGraph).where(DagGraph.id == task.published_version_id)).scalars().first()
        if ver is None:
            raise ValueError('找不到可运行的图版本')
        _upsert_instance(
            db,
            dag_run_id,
            {
                'task_id': dag_task_id,
                'name': task.name,
                'status': 'STARTED',
                'worker': worker,
                'progress': 0,
                'start_time': datetime.now(),
                'closed': 0,
                'dag_version_id': ver.id,
            },
        )
        return run_type
    finally:
        if tenant_token is not None:
            RequestContext.reset_current_tenant_id(tenant_token)
        db.close()


def _run_node_inline(
    dag_run_id: str, dag_task_id: str, node: dict, worker: str | None, tenant_id: Any
) -> tuple[str, str]:
    """在独立线程 + 独立会话里执行一个节点,返回 (node_key, status)。线程内自带租户上下文。"""
    nk = node['node_key']
    db = _session()
    token = RequestContext.set_current_tenant_id(tenant_id)
    iid = uuid.uuid4().hex
    logger = None
    try:
        _upsert_instance(
            db,
            iid,
            {
                'parent_id': dag_run_id,
                'task_id': dag_task_id,
                'node_id': nk,
                'name': node.get('name') or nk,
                'status': 'STARTED',
                'worker': worker,
                'start_time': datetime.now(),
                'closed': 0,
            },
        )
        db.commit()
        logger = get_task_logger(iid)
        logger.info(f'[单机] 节点开始: {nk}')
        res = _build_and_run_node(db, node, logger)
        _upsert_instance(
            db,
            iid,
            {
                'status': 'SUCCESS',
                'progress': 100,
                'end_time': datetime.now(),
                'result': (str(res)[:500] if res is not None else '执行成功'),
                'closed': 1,
            },
        )
        db.commit()
        return nk, 'SUCCESS'
    except Exception as e:
        try:
            (logger.exception if logger else (lambda *_: None))(str(e))
        except Exception:
            pass
        _upsert_instance(
            db,
            iid,
            {'status': 'FAILURE', 'end_time': datetime.now(), 'result': ' '.join(str(e).split())[:1000], 'closed': 1},
        )
        db.commit()
        return nk, 'FAILURE'
    finally:
        try:
            if logger:
                logger.close()
        except Exception:
            pass
        RequestContext.reset_current_tenant_id(token)
        db.close()


def run_dag_single(dag_run_id: str, worker: str | None) -> None:
    """单机模式:本进程内用线程池并行执行就绪节点(尊重依赖,无需分发到其它 worker)。"""
    from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait

    db = _session()
    tenant_token = None
    try:
        dag_run = db.execute(select(TaskInstance).where(TaskInstance.id == dag_run_id)).scalars().first()
        task = db.execute(select(Task).where(Task.id == dag_run.task_id)).scalars().first()
        tenant_id = task.tenant_id if task else None
        tenant_token = RequestContext.set_current_tenant_id(tenant_id)
        graph = _load_graph(db, dag_run.dag_version_id)
        nodes = _node_map(graph)
        dag = build_dag(graph)

        done: set = set()
        failed: set = set()
        skipped: set = set()
        submitted: set = set()
        aborted = False

        def mark_skip(nk: str) -> None:
            db.add(
                TaskInstance(
                    id=uuid.uuid4().hex,
                    parent_id=dag_run_id,
                    task_id=dag_run.task_id,
                    node_id=nk,
                    name=nodes[nk].get('name') or nk,
                    status='SKIPPED',
                    closed=1,
                    result='上游失败/终止,跳过',
                    end_time=datetime.now(),
                )
            )
            skipped.add(nk)
            db.commit()

        max_workers = max(1, min(8, len(nodes)))
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures: dict = {}

            def schedule() -> None:
                """提交所有"就绪"节点;依赖已失败/跳过的节点标 SKIPPED。"""
                for nk in nodes:
                    if nk in submitted or nk in skipped:
                        continue
                    preds = dag.predecessors(nk)
                    if any(p in failed or p in skipped for p in preds) or aborted:
                        mark_skip(nk)
                    elif all(p in done for p in preds):
                        submitted.add(nk)
                        futures[
                            pool.submit(_run_node_inline, dag_run_id, dag_run.task_id, nodes[nk], worker, tenant_id)
                        ] = nk

            schedule()
            while futures:
                ready, _ = wait(list(futures.keys()), return_when=FIRST_COMPLETED)
                for fut in ready:
                    nk = futures.pop(fut)
                    try:
                        _, status = fut.result()
                    except Exception:
                        status = 'FAILURE'
                    (done if status == 'SUCCESS' else failed).add(nk)
                    if status == 'FAILURE' and (nodes[nk].get('error_policy') or 'fail_fast') == 'fail_fast':
                        aborted = True
                _upsert_instance(db, dag_run_id, {'progress': _progress(done, nodes)})
                db.commit()
                schedule()  # 派发新就绪 / 跳过被阻断的

        # 收尾:仍未终态的(被阻断未提交的)统一标跳过
        for nk in nodes:
            if nk not in done and nk not in failed and nk not in skipped:
                mark_skip(nk)
        _upsert_instance(
            db,
            dag_run_id,
            {
                'status': 'FAILURE' if failed else 'SUCCESS',
                'closed': 1,
                'progress': _progress(done, nodes),
                'end_time': datetime.now(),
                'result': (f'部分失败: {sorted(failed)}' if failed else '成功'),
            },
        )
        db.commit()
    finally:
        if tenant_token is not None:
            RequestContext.reset_current_tenant_id(tenant_token)
        db.close()


def _dispatch_node(db: Session, dag_run: TaskInstance, node: dict, run_queue: str) -> None:
    """为节点预建实例(PENDING,防重)并投递 celery 节点任务。"""
    iid = uuid.uuid4().hex
    db.add(
        TaskInstance(
            id=iid,
            parent_id=dag_run.id,
            task_id=dag_run.task_id,
            node_id=node['node_key'],
            name=node.get('name') or node['node_key'],
            status='PENDING',
            closed=0,
        )
    )
    db.commit()
    from config.celery_app import celery_app

    celery_app.send_task(
        'module_task_schedule.run_dag_node',
        args=[dag_run.id, node['node_key']],
        task_id=iid,
        queue=run_queue or 'default',
    )


def advance_dag(dag_run_id: str) -> None:
    """推进 DAG:行锁 + 幂等。派发就绪节点;失败 fail_fast;全完成则成功。"""
    db = _session()
    tenant_token = None
    try:
        # 行锁,串行化并发推进(菱形依赖多个上游同时完成时防重复派发)
        dag_run = (
            db.execute(select(TaskInstance).where(TaskInstance.id == dag_run_id).with_for_update()).scalars().first()
        )
        if dag_run is None or dag_run.closed == 1:
            db.commit()
            return
        task = db.execute(select(Task).where(Task.id == dag_run.task_id)).scalars().first()
        tenant_token = RequestContext.set_current_tenant_id(task.tenant_id if task else None)
        run_queue = (task.run_queue if task else None) or 'default'

        graph = _load_graph(db, dag_run.dag_version_id)
        nodes = _node_map(graph)
        dag = build_dag(graph)

        insts = db.execute(select(TaskInstance).where(TaskInstance.parent_id == dag_run_id)).scalars().all()
        inst_by_node = {i.node_id: i for i in insts}
        done = {nk for nk, i in inst_by_node.items() if i.status == 'SUCCESS'}
        failed = {nk for nk, i in inst_by_node.items() if i.status == 'FAILURE'}
        skipped = {nk for nk, i in inst_by_node.items() if i.status == 'SKIPPED'}

        def mark_skipped(keys: set, reason: str) -> None:
            for nk in keys:
                if nk not in inst_by_node and nk in nodes:
                    db.add(
                        TaskInstance(
                            id=uuid.uuid4().hex,
                            parent_id=dag_run_id,
                            task_id=dag_run.task_id,
                            node_id=nk,
                            name=nodes[nk].get('name') or nk,
                            status='SKIPPED',
                            closed=1,
                            result=reason,
                            end_time=datetime.now(),
                        )
                    )
                    inst_by_node[nk] = True
                    skipped.add(nk)

        # 失败处理:节点级策略 fail_fast(终止整图)/ continue(只跳过其下游)
        if failed:
            policy_fail_fast = any(
                (nodes.get(nk, {}).get('error_policy') or 'fail_fast') == 'fail_fast' for nk in failed
            )
            if policy_fail_fast:
                mark_skipped(set(nodes) - set(inst_by_node), '上游失败,终止')
                _upsert_instance(
                    db,
                    dag_run_id,
                    {
                        'status': 'FAILURE',
                        'closed': 1,
                        'end_time': datetime.now(),
                        'result': f'节点失败(终止): {sorted(failed)}',
                        'progress': _progress(done, nodes),
                    },
                )
                db.commit()
                return
            # continue:把失败/已跳过节点的全部下游标 SKIPPED,其余分支继续
            blocked = set()
            for nk in failed | skipped:
                blocked |= set(dag.all_downstreams(nk))
            mark_skipped(blocked, '上游失败,跳过')

        # 派发就绪节点(上游全 SUCCESS 且自身未派发/未跳过)
        for nk, node in nodes.items():
            if nk in inst_by_node:
                continue
            if all(p in done for p in dag.predecessors(nk)):
                _dispatch_node(db, dag_run, node, run_queue)

        # 完成判定:所有节点到终态(成功/失败/跳过)
        terminal = done | failed | skipped
        if terminal == set(nodes.keys()):
            _upsert_instance(
                db,
                dag_run_id,
                {
                    'status': 'FAILURE' if failed else 'SUCCESS',
                    'closed': 1,
                    'progress': _progress(done, nodes),
                    'end_time': datetime.now(),
                    'result': (f'部分失败: {sorted(failed)}' if failed else '成功'),
                },
            )
        else:
            _upsert_instance(db, dag_run_id, {'progress': _progress(done, nodes)})
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        if tenant_token is not None:
            RequestContext.reset_current_tenant_id(tenant_token)
        db.close()


def _progress(done: set, nodes: dict) -> float:
    return round(len(done) / len(nodes) * 100, 1) if nodes else 0


def node_retry_conf(dag_run_id: str, node_key: str) -> tuple[int, int]:
    """读节点级重试配置(retry, countdown)。"""
    db = _session()
    try:
        dag_run = db.execute(select(TaskInstance).where(TaskInstance.id == dag_run_id)).scalars().first()
        if not dag_run:
            return 0, 0
        node = _node_map(_load_graph(db, dag_run.dag_version_id)).get(node_key, {})
        return int(node.get('retry') or 0), int(node.get('countdown') or 0)
    finally:
        db.close()


def _build_and_run_node(db: Session, node: dict, logger: Any) -> Any:
    """按节点配置选 runner 并执行,返回结果。"""
    from module_task_schedule.runners.base import get_runner
    from module_task_schedule.runners.dynamic_runner import DynamicRunner

    template_code = node.get('template_code')
    params = node.get('params') or {}
    template = db.execute(select(TaskTemplate).where(TaskTemplate.code == template_code)).scalars().first()
    if template is None:
        raise ValueError(f'任务模板不存在: {template_code}')
    if template.runner_type == 2:
        runner = DynamicRunner(params, logger, context={'runner_code': template.runner_code, 'sandbox': True})
    else:
        runner_cls = get_runner(template_code)
        if runner_cls is None:
            raise ValueError(f'未找到内置执行器: {template_code}')
        runner = runner_cls(params, logger, context={'sandbox': True})
    return runner.run()


def execute_single_node(
    dag_task_id: str, node_key: str, instance_id: str, worker: str | None, source: str = 'draft'
) -> str:
    """单独运行 DAG 的某个节点(调试用,不参与编排)。图取自 draft 或 published。"""
    db = _session()
    tenant_token = None
    try:
        task = db.execute(select(Task).where(Task.id == dag_task_id)).scalars().first()
        if task is None:
            raise ValueError(f'DAG 不存在: {dag_task_id}')
        tenant_token = RequestContext.set_current_tenant_id(task.tenant_id)
        if source == 'published':
            ver = db.execute(select(DagGraph).where(DagGraph.id == task.published_version_id)).scalars().first()
        else:
            ver = (
                db.execute(select(DagGraph).where(DagGraph.dag_task_id == dag_task_id, DagGraph.version == 'draft'))
                .scalars()
                .first()
            )
        if ver is None or not ver.graph:
            raise ValueError('找不到图')
        node = _node_map(json.loads(ver.graph)).get(node_key)
        if node is None:
            raise ValueError(f'节点不存在: {node_key}')
        _upsert_instance(
            db,
            instance_id,
            {
                'task_id': dag_task_id,
                'node_id': node_key,
                'parent_id': 'single',
                'name': (node.get('name') or node_key) + '(单节点)',
                'status': 'STARTED',
                'worker': worker,
                'progress': 0,
                'start_time': datetime.now(),
                'closed': 0,
            },
        )
    except Exception:
        if tenant_token is not None:
            RequestContext.reset_current_tenant_id(tenant_token)
        db.close()
        raise

    logger = get_task_logger(instance_id)
    try:
        logger.info(f'单独运行节点: {node_key}')
        result = _build_and_run_node(db, node, logger)
        summary = str(result)[:500] if result is not None else '执行成功'
        logger.info(f'节点完成: {summary}')
        _upsert_instance(
            db,
            instance_id,
            {'status': 'SUCCESS', 'progress': 100, 'end_time': datetime.now(), 'result': summary, 'closed': 1},
        )
        return summary
    except Exception as e:
        err = ' '.join(str(e).split())[:1000]
        try:
            logger.exception(f'节点失败: {err}')
        except Exception:
            pass
        _upsert_instance(db, instance_id, {'status': 'FAILURE', 'end_time': datetime.now(), 'result': err, 'closed': 1})
        raise
    finally:
        try:
            logger.close()
        except Exception:
            pass
        if tenant_token is not None:
            RequestContext.reset_current_tenant_id(tenant_token)
        db.close()


def execute_dag_node(dag_run_id: str, node_key: str, instance_id: str, worker: str | None, retry_num: int = 0) -> str:
    """执行单个 DAG 节点:复用 runner 注册表 + 实例生命周期 + 日志。失败抛出供 celery 重试。"""
    db = _session()
    tenant_token = None
    try:
        dag_run = db.execute(select(TaskInstance).where(TaskInstance.id == dag_run_id)).scalars().first()
        if dag_run is None:
            raise ValueError(f'DAG run 不存在: {dag_run_id}')
        task = db.execute(select(Task).where(Task.id == dag_run.task_id)).scalars().first()
        tenant_token = RequestContext.set_current_tenant_id(task.tenant_id if task else None)
        node = _node_map(_load_graph(db, dag_run.dag_version_id)).get(node_key)
        if node is None:
            raise ValueError(f'节点不存在: {node_key}')
        _upsert_instance(
            db,
            instance_id,
            {
                'parent_id': dag_run_id,
                'task_id': dag_run.task_id,
                'node_id': node_key,
                'name': node.get('name') or node_key,
                'status': 'STARTED',
                'worker': worker,
                'retry_num': retry_num,
                'progress': 0,
                'start_time': datetime.now(),
                'closed': 0,
            },
        )
    except Exception:
        if tenant_token is not None:
            RequestContext.reset_current_tenant_id(tenant_token)
        db.close()
        raise

    logger = get_task_logger(instance_id)
    try:
        logger.info(f'DAG 节点开始: {node_key}(模板 {node.get("template_code")})')
        result = _build_and_run_node(db, node, logger)
        summary = str(result)[:500] if result is not None else '执行成功'
        logger.info(f'DAG 节点完成: {node_key} -> {summary}')
        _upsert_instance(
            db,
            instance_id,
            {
                'status': 'SUCCESS',
                'progress': 100,
                'end_time': datetime.now(),
                'result': summary,
                'closed': 1,
            },
        )
        return summary
    except Exception as e:
        err = ' '.join(str(e).split())[:1000]
        try:
            logger.exception(f'DAG 节点失败: {node_key} {err}')
        except Exception:
            pass
        _upsert_instance(
            db,
            instance_id,
            {
                'status': 'FAILURE',
                'end_time': datetime.now(),
                'result': err,
                'closed': 1,
            },
        )
        raise
    finally:
        try:
            logger.close()
        except Exception:
            pass
        if tenant_token is not None:
            RequestContext.reset_current_tenant_id(tenant_token)
        db.close()
