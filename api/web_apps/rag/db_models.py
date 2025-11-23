'''
rag模块数据模型
'''
import pickle
from web_apps import db
from models import BaseModel


class Dataset(BaseModel):
    '''
    数据集表
    '''
    __tablename__ = 'rag_dataset'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='id')
    name = db.Column(db.String(200), nullable=True, default='', comment='名称', index=True)
    built_in = db.Column(db.SmallInteger, nullable=True, default=0, comment='是否内置 1是 0不是')
    status = db.Column(db.SmallInteger, nullable=True, default=1, comment='状态( 1为启用 0禁用)', index=True)


class Document(BaseModel):
    '''
    文档表
    '''
    __tablename__ = 'rag_document'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='id')
    dataset_id = db.Column(db.String(36), nullable=True, default='', comment='数据集id', index=True)
    document_type = db.Column(db.String(32), nullable=True, default='', comment='文档类型')
    name = db.Column(db.String(200), nullable=True, default='', comment='名称', index=True)
    status = db.Column(db.SmallInteger, nullable=True, default=1, comment='状态( 1待训练，2训练中，3训练成功，4训练失败)', index=True)
    meta_data = db.Column(db.Text, nullable=True, default='{}', comment='文档元信息')
    chunk_strategy = db.Column(db.Text, nullable=True, default='{}', comment='分段策略')


class Chunk(BaseModel):
    '''
    分段chunk
    '''
    __tablename__ = 'rag_chunk'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    dataset_id = db.Column(db.String(36), nullable=True, default='', comment='数据集id', index=True)
    document_id = db.Column(db.String(36), nullable=True, default='', comment='文档id', index=True)
    datasource_id = db.Column(db.String(36), nullable=True, default='', comment='数据源id', index=True)
    datamodel_id = db.Column(db.String(36), nullable=True, default='', comment='数据模型id', index=True)
    chunk_type = db.Column(db.String(32), nullable=True, default='chunk', comment='类型(chunk：文本分段 qa：问答对)', index=True)
    question = db.Column(db.Text, nullable=True, default='', comment='问题')
    question_hash = db.Column(db.String(32), nullable=True, default='', comment='问题hash', index=True)
    answer = db.Column(db.Text, nullable=True, default='', comment='问题回答')
    content = db.Column(db.Text, nullable=True, default='', comment='内容')
    hash = db.Column(db.String(32), nullable=True, default='', comment='内容hash', index=True)
    position = db.Column(db.Integer, nullable=True, default=1, comment='分段位置')
    status = db.Column(db.SmallInteger, nullable=True, default=1, comment='状态( 1已同步 0未同步)', index=True)
    star_flag = db.Column(db.SmallInteger, default=0, comment='标星状态( 1为标星 0没有标星)', index=True)


class Embedding(db.Model):
    __tablename__ = 'rag_embedding'

    id = db.Column(db.String(36), primary_key=True)
    hash = db.Column(db.String(32), nullable=False, index=True)
    embedding = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.text('CURRENT_TIMESTAMP(0)'))

    def set_embedding(self, embedding_data: list[float]):
        self.embedding = pickle.dumps(embedding_data, protocol=pickle.HIGHEST_PROTOCOL)

    def get_embedding(self) -> list[float]:
        return pickle.loads(self.embedding)


if __name__ == '__main__':
    from web_apps import app
    with app.app_context():
        db.create_all()
        db.session.commit()
        db.session.flush()