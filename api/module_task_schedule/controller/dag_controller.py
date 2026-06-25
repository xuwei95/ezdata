from typing import Annotated

from fastapi import Path, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_task_schedule.entity.vo.dag_vo import (
    DagCreateReq, DagDraftSaveReq, DagPublishReq, DagRunReq, DagSettingsReq,
)
from module_task_schedule.service.dag_service import DagService
from utils.response_util import ResponseUtil

dag_controller = APIRouterPro(prefix='/task/dag', order_num=12, tags=['任务调度-DAG工作流'], dependencies=[PreAuthDependency()])


@dag_controller.get('/list', summary='DAG 列表', dependencies=[UserInterfaceAuthDependency('task:dag:list')])
async def dag_list(
    request: Request, db: Annotated[AsyncSession, DBSessionDependency()],
    name: Annotated[str | None, Query()] = None,
    pageNum: Annotated[int, Query()] = 1, pageSize: Annotated[int, Query()] = 10,  # noqa: N803
) -> Response:
    return ResponseUtil.success(model_content=await DagService.get_list(db, name, pageNum, pageSize, is_page=True))


@dag_controller.post('', summary='新建 DAG', dependencies=[UserInterfaceAuthDependency('task:dag:edit')])
async def dag_create(
    request: Request, req: DagCreateReq, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    return ResponseUtil.success(data=await DagService.create(db, req, current_user.user.user_name))


@dag_controller.post('/{dag_id}/copy', summary='复制 DAG', dependencies=[UserInterfaceAuthDependency('task:dag:edit')])
async def dag_copy(
    dag_id: Annotated[str, Path()], req: DagCreateReq, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    return ResponseUtil.success(data=await DagService.copy(db, dag_id, req.name, current_user.user.user_name))


@dag_controller.delete('/{ids}', summary='删除 DAG', dependencies=[UserInterfaceAuthDependency('task:dag:edit')])
async def dag_delete(ids: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    r = await DagService.delete(db, ids)
    return ResponseUtil.success(msg=r.message)


@dag_controller.get('/{dag_id}/detail', summary='DAG 本体详情', dependencies=[UserInterfaceAuthDependency('task:dag:list')])
async def dag_detail(dag_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DagService.get_detail(db, dag_id))


@dag_controller.put('/{dag_id}/settings', summary='更新 DAG 本体设置', dependencies=[UserInterfaceAuthDependency('task:dag:edit')])
async def dag_settings(
    dag_id: Annotated[str, Path()], req: DagSettingsReq, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await DagService.update_settings(db, dag_id, req, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


# ---------------- 草稿 ----------------
@dag_controller.get('/{dag_id}/draft', summary='读草稿图', dependencies=[UserInterfaceAuthDependency('task:dag:list')])
async def dag_get_draft(dag_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DagService.get_draft(db, dag_id))


@dag_controller.put('/{dag_id}/draft', summary='存草稿图', dependencies=[UserInterfaceAuthDependency('task:dag:edit')])
async def dag_save_draft(
    dag_id: Annotated[str, Path()], req: DagDraftSaveReq, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await DagService.save_draft(db, dag_id, req.graph, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


# ---------------- 发布 / 版本 / 回滚 ----------------
@dag_controller.post('/{dag_id}/publish', summary='发布', dependencies=[UserInterfaceAuthDependency('task:dag:publish')])
async def dag_publish(
    dag_id: Annotated[str, Path()], req: DagPublishReq, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    return ResponseUtil.success(data=await DagService.publish(db, dag_id, req.remark, current_user.user.user_name))


@dag_controller.get('/{dag_id}/versions', summary='版本列表', dependencies=[UserInterfaceAuthDependency('task:dag:list')])
async def dag_versions(dag_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DagService.list_versions(db, dag_id))


@dag_controller.get('/version/{ver_id}', summary='读某版本图', dependencies=[UserInterfaceAuthDependency('task:dag:list')])
async def dag_version_graph(ver_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DagService.get_version_graph(db, ver_id))


@dag_controller.post('/{dag_id}/rollback/{ver_id}', summary='回滚版本',
                     dependencies=[UserInterfaceAuthDependency('task:dag:publish')])
async def dag_rollback(
    dag_id: Annotated[str, Path()], ver_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    r = await DagService.rollback(db, dag_id, ver_id)
    return ResponseUtil.success(msg=r.message)


# ---------------- 运行 / 监控 ----------------
@dag_controller.post('/{dag_id}/run', summary='正式运行', dependencies=[UserInterfaceAuthDependency('task:dag:run')])
async def dag_run(
    dag_id: Annotated[str, Path()], req: DagRunReq, db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DagService.run(db, dag_id, req.source or 'published'))


@dag_controller.post('/{dag_id}/debug', summary='试运行(跑草稿)', dependencies=[UserInterfaceAuthDependency('task:dag:run')])
async def dag_debug(dag_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DagService.run(db, dag_id, 'draft'))


@dag_controller.get('/run/{run_id}', summary='运行节点状态', dependencies=[UserInterfaceAuthDependency('task:dag:list')])
async def dag_run_status(run_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DagService.run_nodes_status(db, run_id))


@dag_controller.get('/{dag_id}/runs', summary='DAG 运行历史', dependencies=[UserInterfaceAuthDependency('task:dag:list')])
async def dag_runs(dag_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DagService.list_runs(db, dag_id))


@dag_controller.get('/{dag_id}/node/{node_key}/history', summary='节点执行历史',
                    dependencies=[UserInterfaceAuthDependency('task:dag:list')])
async def dag_node_history(
    dag_id: Annotated[str, Path()], node_key: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DagService.node_history(db, dag_id, node_key))


@dag_controller.post('/{dag_id}/node/{node_key}/run', summary='单独运行节点(调试)',
                     dependencies=[UserInterfaceAuthDependency('task:dag:run')])
async def dag_run_node(
    dag_id: Annotated[str, Path()], node_key: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    return ResponseUtil.success(data=await DagService.run_node(db, dag_id, node_key, 'draft'))
