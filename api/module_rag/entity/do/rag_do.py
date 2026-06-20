from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, SmallInteger, String, Text

from config.database import Base, TenantMixin


class RagDataset(Base, TenantMixin):
    """知识库(数据集)。每个库绑定一个 embedding 模型 + 一个向量后端,建后维度不可改。"""

    __tablename__ = 'rag_dataset'
    __table_args__ = {'comment': 'RAG 知识库'}

    id = Column(String(36), primary_key=True, comment='知识库ID')
    name = Column(String(200), nullable=False, comment='名称')
    description = Column(String(500), nullable=True, comment='描述')
    source_id = Column(String(36), nullable=True, index=True, comment='专属数据源ID(空=普通知识库)')
    embedding_provider = Column(String(50), nullable=True, comment='embedding 提供商')
    embedding_model = Column(String(100), nullable=True, comment='embedding 模型编码')
    embedding_dims = Column(Integer, nullable=True, comment='向量维度')
    vector_backend = Column(String(50), server_default='elasticsearch', comment='向量后端')
    vector_source_id = Column(String(36), nullable=True, comment='向量库 data_source(空=用系统默认ES)')
    index_name = Column(String(200), nullable=True, comment='向量索引/集合名')
    retrieval_config = Column(Text, nullable=True, comment='默认检索参数(JSON)')
    built_in = Column(SmallInteger, server_default='0', comment='是否内置')
    status = Column(SmallInteger, server_default='1', comment='状态 1启用0禁用')
    create_by = Column(String(64), nullable=True, comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')
    remark = Column(String(500), nullable=True, comment='备注')


class RagDocument(Base, TenantMixin):
    """知识库文档。一条文档训练后产出多个分段(rag_chunk)。"""

    __tablename__ = 'rag_document'
    __table_args__ = {'comment': 'RAG 文档'}

    id = Column(String(36), primary_key=True, comment='文档ID')
    dataset_id = Column(String(36), nullable=False, index=True, comment='所属知识库')
    name = Column(String(300), nullable=False, comment='文档名')
    document_type = Column(String(30), server_default='upload_file', comment='来源类型 upload_file/website/text/datamodel')
    file_key = Column(String(500), nullable=True, comment='文件存储 key')
    source = Column(String(1000), nullable=True, comment='来源(URL / datamodel_id 等)')
    meta_data = Column(Text, nullable=True, comment='元数据(JSON)')
    chunk_strategy = Column(Text, nullable=True, comment='切分/清洗策略(JSON)')
    status = Column(SmallInteger, server_default='1', comment='状态 1待训练2训练中3成功4失败')
    chunk_count = Column(Integer, server_default='0', comment='分段数')
    error = Column(String(1000), nullable=True, comment='失败原因')
    create_by = Column(String(64), nullable=True, comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')


class RagChunk(Base, TenantMixin):
    """文本分段 / 问答对。chunk_id 即向量库 _id。"""

    __tablename__ = 'rag_chunk'
    __table_args__ = {'comment': 'RAG 分段'}

    id = Column(String(36), primary_key=True, comment='分段ID(=向量库_id)')
    dataset_id = Column(String(36), nullable=False, index=True, comment='所属知识库')
    document_id = Column(String(36), nullable=False, index=True, comment='所属文档')
    chunk_type = Column(String(10), server_default='chunk', comment='类型 chunk/qa')
    content = Column(Text, nullable=True, comment='正文')
    question = Column(Text, nullable=True, comment='问题(QA)')
    question_hash = Column(String(64), nullable=True, index=True, comment='问题hash(QA精确命中)')
    answer = Column(Text, nullable=True, comment='答案(QA)')
    hash = Column(String(64), nullable=True, comment='正文hash(去重)')
    position = Column(Integer, server_default='0', comment='序号')
    status = Column(SmallInteger, server_default='1', comment='状态 1已索引0未索引')
    star_flag = Column(SmallInteger, server_default='0', comment='标星')
    create_by = Column(String(64), nullable=True, comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')


class RagEmbedding(Base):
    """embedding 缓存(全局,按 hash+model 命中)。省调用 + 向量库丢数时零成本重灌。"""

    __tablename__ = 'rag_embedding'
    __table_args__ = {'comment': 'RAG embedding 缓存'}

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键')
    hash = Column(String(64), nullable=False, index=True, comment='文本hash(md5)')
    model_id = Column(String(150), nullable=False, comment='provider:model')
    dim = Column(Integer, nullable=True, comment='维度')
    vector = Column(Text, nullable=True, comment='向量(JSON数组)')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
