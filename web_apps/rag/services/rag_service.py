from web_apps import db, app
from utils.auth import set_insert_user
from utils.etl_utils import get_reader_model
from utils.common_utils import gen_uuid, md5
from web_apps.rag.splitter.text_splitter import RecursiveCharacterTextSplitter
from web_apps.rag.utils import get_vector_index
from web_apps.rag.db_models import Dataset, Document, Chunk
from web_apps.datamodel.db_models import DataModel


def train_qa_info(question, answer, metadata=None):
    '''
    将问答信息训练加入知识库
    '''
    if metadata is None:
        metadata = {}
    with app.app_context():
        question = question.strip()
        content = f"问题: {question}\n答案: {answer}"
        _hash = md5(content)
        question_hash = md5(question)
        _uuid = gen_uuid()
        datamodel_id = metadata.get('datamodel_id')
        datasource_id = metadata.get('datasource_id')
        if datamodel_id is not None:
            datamodel_obj = db.session.query(DataModel.id == datamodel_id).first()
            if datamodel_obj:
                datasource_id = datamodel_obj.datasource_id
        chunk_obj = Chunk(
            id=_uuid,
            datasource_id=datasource_id,
            datamodel_id=datamodel_id,
            chunk_type='qa',
            question=question,
            question_hash=question_hash,
            answer=answer,
            content=content,
            hash=_hash,
            star_flag=metadata.get('star_flag', 0)
        )
        set_insert_user(chunk_obj, metadata.get('user_name'))
        db.session.add(chunk_obj)
        db.session.flush()
        db.session.commit()
        # 加入向量数据库
        vector_index = get_vector_index()
        meta_data = {
            'uuid': _uuid,
            'hash': _hash,
            'datasource_id': datasource_id,
            'datamodel_id': datamodel_id
        }
        vector_index.add_texts([content], metadatas=[meta_data])


def train_datamodel(datamodel_id, metadata=None):
    '''
    将数据模型训练加入知识库
    '''
    if metadata is None:
        metadata = {}
    with app.app_context():
        datasource_id = metadata.get('datasource_id')
        if datamodel_id is not None:
            datamodel_obj = db.session.query(DataModel.id == datamodel_id).first()
            if datamodel_obj:
                datasource_id = datamodel_obj.datasource_id
        flag, reader = get_reader_model({'model_id': datamodel_id})
        info_prompt = reader.get_info_prompt('')
        metadata_text = info_prompt.split('# MetaData:')[1] if '# MetaData:' in info_prompt else info_prompt
        spliter = RecursiveCharacterTextSplitter(separators=['\n\n'], chunk_size=1024)
        chunks = spliter.split_text(metadata_text)
        for chunk in chunks:
            content = chunk.strip()
            _hash = md5(content)
            chunk_obj = Chunk(
                id=gen_uuid(),
                datasource_id=datasource_id,
                datamodel_id=datamodel_id,
                chunk_type='chunk',
                content=content,
                hash=_hash
            )
            set_insert_user(chunk_obj, metadata.get('user_name'))
            db.session.add(chunk_obj)
            db.session.flush()
            db.session.commit()
            # 加入向量数据库
            vector_index = get_vector_index()
            meta_data = {
                'hash': _hash,
                'datasource_id': datasource_id,
                'datamodel_id': datamodel_id
            }
            vector_index.add_texts([content], metadatas=[meta_data])


if __name__ == '__main__':
    datamodel_id = '8a862fdf980245459ac9ef89734c166f'
    metadata = {
        'datasource_id': '8a862fdf980245459ac9ef89734c166f',
        'user_name': 'admin'
    }
    train_datamodel(datamodel_id, metadata)
