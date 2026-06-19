from typing import Annotated

from fastapi import Path, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from common.aspect.db_seesion import DBSessionDependency
from common.aspect.interface_auth import UserInterfaceAuthDependency
from common.aspect.pre_auth import CurrentUserDependency, PreAuthDependency
from common.router import APIRouterPro
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_rag.entity.vo.rag_vo import (
    ChunkSaveReq, ChunkStarReq, DatasetCreateReq, DatasetUpdateReq, DocumentCreateReq, RetrievalReq,
)
from module_rag.service.chunk_service import ChunkService
from module_rag.service.dataset_service import DatasetService
from module_rag.service.document_service import DocumentService
from module_rag.service.retrieval_service import RetrievalService
from module_rag.vector_store.factory import supported_backends
from utils.response_util import ResponseUtil

rag_controller = APIRouterPro(prefix='/rag', order_num=13, tags=['知识库'], dependencies=[PreAuthDependency()])


# ---------------- 知识库 ----------------
@rag_controller.get('/dataset/list', summary='知识库列表', dependencies=[UserInterfaceAuthDependency('rag:dataset:list')])
async def dataset_list(
    request: Request, db: Annotated[AsyncSession, DBSessionDependency()],
    name: Annotated[str | None, Query()] = None,
    pageNum: Annotated[int, Query()] = 1, pageSize: Annotated[int, Query()] = 10,  # noqa: N803
) -> Response:
    return ResponseUtil.success(model_content=await DatasetService.get_list(db, name, pageNum, pageSize, is_page=True))


@rag_controller.post('/dataset', summary='新建知识库', dependencies=[UserInterfaceAuthDependency('rag:dataset:edit')])
async def dataset_create(
    request: Request, req: DatasetCreateReq, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    return ResponseUtil.success(data=await DatasetService.create(db, req, current_user.user.user_name))


@rag_controller.get('/dataset/{ds_id}', summary='知识库详情', dependencies=[UserInterfaceAuthDependency('rag:dataset:list')])
async def dataset_detail(ds_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DatasetService.get_detail(db, ds_id))


@rag_controller.put('/dataset/{ds_id}', summary='编辑知识库', dependencies=[UserInterfaceAuthDependency('rag:dataset:edit')])
async def dataset_update(
    ds_id: Annotated[str, Path()], req: DatasetUpdateReq, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    r = await DatasetService.update(db, ds_id, req, current_user.user.user_name)
    return ResponseUtil.success(msg=r.message)


@rag_controller.delete('/dataset/{ids}', summary='删除知识库', dependencies=[UserInterfaceAuthDependency('rag:dataset:edit')])
async def dataset_delete(ids: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    r = await DatasetService.delete(db, ids)
    return ResponseUtil.success(msg=r.message)


# ---------------- 文档 ----------------
@rag_controller.get('/document/list', summary='文档列表', dependencies=[UserInterfaceAuthDependency('rag:dataset:list')])
async def document_list(
    request: Request, db: Annotated[AsyncSession, DBSessionDependency()],
    datasetId: Annotated[str, Query()],  # noqa: N803
    name: Annotated[str | None, Query()] = None,
    pageNum: Annotated[int, Query()] = 1, pageSize: Annotated[int, Query()] = 10,  # noqa: N803
) -> Response:
    return ResponseUtil.success(
        model_content=await DocumentService.get_list(db, datasetId, name, pageNum, pageSize, is_page=True))


@rag_controller.post('/document', summary='新建文档', dependencies=[UserInterfaceAuthDependency('rag:dataset:edit')])
async def document_create(
    request: Request, req: DocumentCreateReq, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    return ResponseUtil.success(data=await DocumentService.create(db, req, current_user.user.user_name))


@rag_controller.delete('/document/{ids}', summary='删除文档', dependencies=[UserInterfaceAuthDependency('rag:dataset:edit')])
async def document_delete(ids: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    r = await DocumentService.delete(db, ids)
    return ResponseUtil.success(msg=r.message)


@rag_controller.post('/document/{doc_id}/train', summary='训练文档', dependencies=[UserInterfaceAuthDependency('rag:dataset:edit')])
async def document_train(doc_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    r = await DocumentService.train(db, doc_id)
    return ResponseUtil.success(msg=r.message)


@rag_controller.get('/document/{doc_id}/status', summary='文档训练状态', dependencies=[UserInterfaceAuthDependency('rag:dataset:list')])
async def document_status(doc_id: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await DocumentService.status(db, doc_id))


# ---------------- 分段 / QA ----------------
@rag_controller.get('/chunk/list', summary='分段列表', dependencies=[UserInterfaceAuthDependency('rag:dataset:list')])
async def chunk_list(
    request: Request, db: Annotated[AsyncSession, DBSessionDependency()],
    datasetId: Annotated[str, Query()],  # noqa: N803
    documentId: Annotated[str | None, Query()] = None,  # noqa: N803
    pageNum: Annotated[int, Query()] = 1, pageSize: Annotated[int, Query()] = 10,  # noqa: N803
) -> Response:
    return ResponseUtil.success(
        model_content=await ChunkService.get_list(db, datasetId, documentId, pageNum, pageSize, is_page=True))


@rag_controller.post('/chunk', summary='新增/编辑分段', dependencies=[UserInterfaceAuthDependency('rag:dataset:edit')])
async def chunk_save(
    request: Request, req: ChunkSaveReq, db: Annotated[AsyncSession, DBSessionDependency()],
    current_user: Annotated[CurrentUserModel, CurrentUserDependency()],
) -> Response:
    return ResponseUtil.success(data=await ChunkService.save(db, req, current_user.user.user_name))


@rag_controller.delete('/chunk/{ids}', summary='删除分段', dependencies=[UserInterfaceAuthDependency('rag:dataset:edit')])
async def chunk_delete(ids: Annotated[str, Path()], db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    r = await ChunkService.delete(db, ids)
    return ResponseUtil.success(msg=r.message)


@rag_controller.post('/chunk/{chunk_id}/star', summary='分段标星', dependencies=[UserInterfaceAuthDependency('rag:dataset:edit')])
async def chunk_star(
    chunk_id: Annotated[str, Path()], req: ChunkStarReq, db: Annotated[AsyncSession, DBSessionDependency()],
) -> Response:
    r = await ChunkService.star(db, chunk_id, req.star_flag)
    return ResponseUtil.success(msg=r.message)


# ---------------- 召回 / 杂项 ----------------
@rag_controller.post('/retrieval', summary='召回测试', dependencies=[UserInterfaceAuthDependency('rag:retrieval')])
async def retrieval(request: Request, req: RetrievalReq, db: Annotated[AsyncSession, DBSessionDependency()]) -> Response:
    return ResponseUtil.success(data=await RetrievalService.search(req))


@rag_controller.get('/vector/backends', summary='支持的向量后端', dependencies=[UserInterfaceAuthDependency('rag:dataset:list')])
async def vector_backends(request: Request) -> Response:
    return ResponseUtil.success(data=supported_backends())
