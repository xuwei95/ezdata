"""数据目录向量检索(catalog retrieval narrowing)。

把 data_model(表)做 embedding 存入独立索引 `ez_catalog_index`,按当轮问题检索 Top-K 相关表,
替代 build_data_catalog 的全量注入(见 module_ai/docs/catalog-retrieval-narrowing-design.md)。

- 复用 module_rag 的 EmbeddingClient + ES 向量库(EsVectorStore),与用户知识库**物理隔离**。
- 索引 mapping 复用 EsVectorStore.ensure_index:用 dataset_id 存 datasource_code(可过滤 scope),
  meta(enabled:false)存表元信息(object_name/model_name/remark…),按需回读。
- 检索/索引不可用或异常时,上层 build_data_catalog 回退全量目录(永不比现状差)。
"""

from __future__ import annotations

from typing import Any

from config.env import RagConfig, TaskLogConfig
from module_rag.embedding import EmbeddingClient
from module_rag.vector_store.factory import get_vector_store
from utils.log_util import logger

CATALOG_INDEX = 'ez_catalog_index'


def _conn() -> dict[str, Any]:
    """向量库连接:复用 RagConfig(与 module_rag runtime_util._vector_connection 同源)。"""
    hosts = RagConfig.rag_vector_hosts or TaskLogConfig.task_es_hosts or 'http://127.0.0.1:9200'
    c: dict[str, Any] = {'hosts': hosts}
    if RagConfig.rag_vector_api_key:
        c['api_key'] = RagConfig.rag_vector_api_key
    elif RagConfig.rag_vector_user:
        c['user'] = RagConfig.rag_vector_user
        c['password'] = RagConfig.rag_vector_password
    return c


def _embed_client() -> EmbeddingClient:
    return EmbeddingClient(
        RagConfig.embedding_type,
        RagConfig.embedding_model,
        RagConfig.api_key,
        RagConfig.embedding_url or None,
        dims=(RagConfig.embedding_dims or None),
    )


def _store():
    return get_vector_store(RagConfig.rag_vector_backend or 'elasticsearch', _conn(), CATALOG_INDEX)


def _doc_text(sname: str, stype: str, obj: str, mname: str, remark: str) -> str:
    """表的可 embedding 文档:源+表+业务名+备注(备注含字段/口径语义,是主要召回信号)。"""
    head = f'数据源 {sname}({stype}) · 表 {obj}'
    if mname:
        head += f' · 业务名 {mname}'
    return f'{head}\n{remark}' if remark else head


def _cid(tid: str, code: str, obj: str) -> str:
    return f'{tid}:{code}:{obj}'


def _chunk(cid: str, tid: str, code: str, obj: str, mname: str, stype: str, remark: str, vec: list[float]) -> dict:
    return {
        'chunk_id': cid,
        'document_id': cid,
        'chunk_type': 'table',
        'tenant_id': tid,
        'dataset_id': code,  # 复用为 datasource_code,可按 scope 过滤
        'content': _doc_text('', stype, obj, mname, remark),  # content 与 embedding 文档一致(源名略)
        'content_vector': vec,
        'meta': {
            'datasource_code': code,
            'object_name': obj,
            'model_name': mname,
            'source_type': stype,
            'remark': remark,
        },
    }


class CatalogRetrievalService:
    """数据目录索引/检索。"""

    @classmethod
    def available(cls) -> bool:
        """embedding 是否可用(无 key 则整条检索路径不启用,上层回退全量)。"""
        return bool(RagConfig.api_key)

    @classmethod
    def rebuild(cls, tenant_id: Any = None) -> int:
        """(重)建目录索引。tenant_id 为空 → 全量重建(drop 重来);指定则只重建该租户。"""
        from sqlalchemy import select

        from module_data.entity.do.data_do import DataModel, DataSource
        from module_task_schedule.sync_db import get_sync_session_local

        db = get_sync_session_local()()
        try:
            src = {
                r[0]: (r[1], r[2])
                for r in db.execute(select(DataSource.code, DataSource.name, DataSource.source_type)).all()
            }
            rows = [
                r
                for r in db.execute(
                    select(
                        DataModel.datasource_code,
                        DataModel.object_name,
                        DataModel.name,
                        DataModel.remark,
                        DataModel.tenant_id,
                    ).where(DataModel.status == 1)
                ).all()
                if r[1]  # object_name 非空(排除"自定义查询"占位模型)
            ]
        finally:
            db.close()
        if tenant_id is not None:
            rows = [r for r in rows if str(r[4]) == str(tenant_id)]
        if not rows:
            return 0

        client = _embed_client()
        dims = client.dims
        docs, metas = [], []
        for code, obj, mname, remark, tid in rows:
            sname, stype = src.get(code, ('', ''))
            docs.append(_doc_text(sname, stype, obj, mname or '', remark or ''))
            metas.append((code, obj, mname or '', sname, stype, remark or '', str(tid) if tid is not None else ''))
        vecs = client.embed(docs)

        store = _store()
        if tenant_id is None:
            store.drop()  # 全量重建:清空重来(单 _id 覆盖式 add 也能 upsert,但全量 drop 更干净)
        store.ensure_index(dims)
        chunks = [
            _chunk(_cid(tid, code, obj), tid, code, obj, mname, stype, remark, vec)
            for (code, obj, mname, sname, stype, remark, tid), vec in zip(metas, vecs)
        ]
        store.add(chunks)
        logger.info(f'[catalog_index] rebuilt {len(chunks)} tables (tenant={tenant_id})')
        return len(chunks)

    @classmethod
    def sync_model_by_id(cls, model_id: Any) -> None:
        """单模型增量同步(add/edit 提交后调):status=1 且有 object_name → upsert;否则删其索引。失败仅告警。"""
        if not cls.available():
            return
        try:
            from sqlalchemy import select

            from module_data.entity.do.data_do import DataModel, DataSource
            from module_task_schedule.sync_db import get_sync_session_local

            db = get_sync_session_local()()
            try:
                m = db.execute(
                    select(
                        DataModel.datasource_code,
                        DataModel.object_name,
                        DataModel.name,
                        DataModel.remark,
                        DataModel.tenant_id,
                        DataModel.status,
                    ).where(DataModel.id == model_id)
                ).first()
                if not m:
                    return
                code, obj, name, remark, tid, status = m
                sname, stype = '', ''
                if code:
                    s = db.execute(
                        select(DataSource.name, DataSource.source_type).where(DataSource.code == code)
                    ).first()
                    if s:
                        sname, stype = s
            finally:
                db.close()
            tids = str(tid) if tid is not None else ''
            store = _store()
            cid = _cid(tids, code, obj)
            if status == 1 and obj:
                client = _embed_client()
                store.ensure_index(client.dims)
                vec = client.embed_query(_doc_text(sname, stype, obj, name or '', remark or ''))
                store.add([_chunk(cid, tids, code, obj, name or '', stype, remark or '', vec)])
            elif store.index_exists():
                store.delete_by_document(cid)
        except Exception as e:
            logger.warning(f'[catalog_index] sync_model_by_id({model_id}) 失败(不影响保存): {e}')

    @classmethod
    def remove_keys(cls, keys: list[tuple]) -> None:
        """按 (tenant_id, code, object_name) 删索引文档(删除模型前捕获、提交后调)。失败仅告警。"""
        if not cls.available() or not keys:
            return
        try:
            store = _store()
            if not store.index_exists():
                return
            for tid, code, obj in keys:
                store.delete_by_document(_cid(str(tid) if tid is not None else '', code, obj))
        except Exception as e:
            logger.warning(f'[catalog_index] remove_keys 失败: {e}')

    @classmethod
    def sync_datasource(cls, datasource_code: str, tenant_id: Any = None) -> int:
        """同步单个数据源的全部已建模表到索引(upsert;供数据源管理「同步」按钮/worker 调用)。

        已删模型的孤儿索引由删除钩子(remove_keys)处理;此处只 upsert 当前有效模型,
        故快、幂等。首次全量/清孤儿走 rebuild(drop 重建)。
        """
        if not cls.available() or not datasource_code:
            return 0
        from sqlalchemy import select

        from module_data.entity.do.data_do import DataModel, DataSource
        from module_task_schedule.sync_db import get_sync_session_local

        db = get_sync_session_local()()
        try:
            s = db.execute(
                select(DataSource.name, DataSource.source_type).where(DataSource.code == datasource_code)
            ).first()
            sname, stype = (s[0], s[1]) if s else ('', '')
            rows = [
                r
                for r in db.execute(
                    select(DataModel.object_name, DataModel.name, DataModel.remark, DataModel.tenant_id).where(
                        DataModel.datasource_code == datasource_code, DataModel.status == 1
                    )
                ).all()
                if r[0]
            ]
        finally:
            db.close()
        if not rows:
            return 0
        client = _embed_client()
        store = _store()
        store.ensure_index(client.dims)
        docs = [_doc_text(sname, stype, obj, name or '', remark or '') for obj, name, remark, tid in rows]
        vecs = client.embed(docs)
        chunks = []
        for (obj, name, remark, tid), vec in zip(rows, vecs):
            tids = str(tid) if tid is not None else ''
            chunks.append(
                _chunk(_cid(tids, datasource_code, obj), tids, datasource_code, obj, name or '', stype, remark or '', vec)
            )
        store.add(chunks)
        logger.info(f'[catalog_index] synced datasource {datasource_code}: {len(chunks)} tables')
        return len(chunks)

    @classmethod
    def retrieve_tables(
        cls, question: str, scope_codes: list[str] | None = None, tenant_id: Any = None, k: int = 8
    ) -> list[dict]:
        """按问题检索 Top-K 相关表。返回 [{datasource_code,object_name,model_name,source_type,remark,score}]。"""
        client = _embed_client()
        vec = client.embed_query(question)
        filters: list[dict] = []
        if tenant_id is not None:
            # 匹配本租户 或 空租户(全局/超管建的无租户模型),避免漏掉共享模型
            filters.append({'terms': {'tenant_id': [str(tenant_id), '']}})
        if scope_codes:
            filters.append({'terms': {'dataset_id': list(scope_codes)}})
        hits = _store().vector_search(vec, k=k, filters=filters or None)
        out = []
        for h in hits:
            m = h.get('meta') or {}
            out.append(
                {
                    'datasource_code': m.get('datasource_code') or h.get('dataset_id'),
                    'object_name': m.get('object_name'),
                    'model_name': m.get('model_name'),
                    'source_type': m.get('source_type'),
                    'remark': m.get('remark'),
                    'score': h.get('score'),
                }
            )
        return out
