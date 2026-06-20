from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class _Base(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# ---------------- 知识库 ----------------
class DatasetCreateReq(_Base):
    name: str = Field(description='名称')
    description: str | None = Field(default=None, description='描述')
    embedding_provider: str | None = Field(default=None, description='embedding 提供商(空=用系统默认)')
    embedding_model: str | None = Field(default=None, description='embedding 模型(空=用系统默认)')
    vector_backend: str | None = Field(default=None, description='向量后端(空=系统默认 ES)')
    vector_source_id: str | None = Field(default=None, description='向量库 data_source')
    remark: str | None = Field(default=None, description='备注')


class DatasetUpdateReq(_Base):
    name: str = Field(description='名称')
    description: str | None = None
    status: int = Field(default=1, description='1启用0禁用')
    vector_backend: str | None = None
    vector_source_id: str | None = None
    retrieval_config: dict | None = Field(default=None, description='默认检索参数')
    remark: str | None = None


# ---------------- 文档 ----------------
class DocumentCreateReq(_Base):
    dataset_id: str = Field(description='所属知识库')
    name: str = Field(description='文档名')
    document_type: str = Field(default='upload_file', description='upload_file/website/text/datamodel')
    file_key: str | None = Field(default=None, description='文件 key(upload_file)')
    source: str | None = Field(default=None, description='URL / datamodel_id 等')
    text: str | None = Field(default=None, description='直接粘贴的文本(text 类型)')
    chunk_strategy: dict | None = Field(default=None, description='切分策略 chunk_size/chunk_overlap')
    auto_train: bool = Field(default=True, description='创建后是否立即训练')


# ---------------- 分段 / QA ----------------
class ChunkSaveReq(_Base):
    id: str | None = None
    dataset_id: str = Field(description='所属知识库')
    document_id: str | None = Field(default=None, description='所属文档')
    chunk_type: str = Field(default='chunk', description='chunk/qa')
    content: str | None = Field(default=None, description='正文(chunk)')
    question: str | None = Field(default=None, description='问题(qa)')
    answer: str | None = Field(default=None, description='答案(qa)')


class ChunkStarReq(_Base):
    star_flag: int = Field(default=1, description='1标星0取消')


class BulkImportReq(_Base):
    dataset_id: str = Field(description='目标知识库')
    chunk_type: str = Field(default='qa', description='qa/chunk')
    file_key: str = Field(description='已上传文件的 key(CSV/Excel)')


# ---------------- 召回 ----------------
class RetrievalReq(_Base):
    query: str = Field(description='查询文本')
    dataset_ids: list[str] = Field(description='知识库 id 列表')
    top_k: int = Field(default=5, description='返回条数')
    retrieval_type: str = Field(default='hybrid', description='vector/keyword/hybrid')
    score_threshold: float = Field(default=0.0, description='分数阈值')
    rerank: bool = Field(default=False, description='是否重排')
    rerank_score_threshold: float = Field(default=0.0, description='重排分数阈值')


# 出参可用 dict,这里仅占位
class RetrievalRecord(_Base):
    chunk_id: str | None = None
    content: str | None = None
    dataset_id: str | None = None
    document_id: str | None = None
    chunk_type: str | None = None
    score: float | None = None
    extra: Any | None = None
