from web_apps import db, app
from utils.auth import set_insert_user, set_update_user
from utils.etl_utils import get_reader_model
from utils.common_utils import gen_uuid, md5, parse_json
from web_apps.rag.splitter.text_splitter import RecursiveCharacterTextSplitter
from web_apps.rag.utils import get_vector_index, get_rerank_runner
from web_apps.rag.db_models import Document, Chunk
from web_apps.datamodel.db_models import DataModel
from web_apps.rag.extractor.extract_processor import ExtractProcessor, ExtractSetting


def get_knowledge(question, metadata=None, res_type='text'):
    '''
    根据问题查询知识库知识
    '''
    if metadata is None:
        metadata = {}
    with app.app_context():
        vector_index = get_vector_index()
        if 'score_threshold' in metadata:
            score_threshold = float(metadata['score_threshold'])
        else:
            score_threshold = 0
        k = int(metadata.get('k', 5))
        search_kwargs = {
            'filter': {},
            'score_threshold': score_threshold,
            'k': k
        }
        if 'dataset_id' in metadata:
            search_kwargs['filter']['dataset_id'] = metadata['dataset_id']
        if 'datamodel_id' in metadata:
            search_kwargs['filter']['datamodel_id'] = metadata['datamodel_id']
        kwargs = {
            'search_kwargs': search_kwargs
        }
        if score_threshold > 0:
            kwargs['search_type'] = 'similarity_score_threshold'
        documents = vector_index.search(question, **kwargs)
        if str(metadata.get('rerank')) == '1':
            rerank_runner = get_rerank_runner()
            documents = rerank_runner.run(question, documents, top_n=k,  score_threshold=score_threshold)
        if res_type == 'documents':
            return documents
        if documents == []:
            return ''
        knowledge = '\n'.join([d.page_content for d in documents])
        return knowledge.strip()


def get_star_qa_answer(question, metadata=None):
    '''
    获取知识库中的标记的问题答案
    '''
    if metadata is None:
        metadata = {}
    with app.app_context():
        question = question.strip()
        question_hash = md5(question)
        query = db.session.query(Chunk).filter(Chunk.del_flag == 0).filter(Chunk.question_hash == question_hash)
        if 'datamodel_id' in metadata:
            query = query.filter(Chunk.datamodel_id == metadata['datamodel_id'])
        if 'dataset_id' in metadata:
            query = query.filter(Chunk.datamodel_id == metadata['dataset_id'])
        chunk_obj = query.first()
        if chunk_obj is not None:
            return chunk_obj.answer
    return ''


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
        datamodel_id = metadata.get('datamodel_id')
        datasource_id = metadata.get('datasource_id')
        if datamodel_id is not None:
            datamodel_obj = db.session.query(DataModel).filter(DataModel.id == datamodel_id).first()
            if datamodel_obj:
                datasource_id = datamodel_obj.datasource_id
        document_id = metadata.get('document_id')
        dataset_id = metadata.get('dataset_id')
        if document_id:
            document_obj = db.session.query(Document).filter(Document.id == document_id).first()
            if document_obj:
                dataset_id = document_obj.dataset_id
        query = db.session.query(Chunk).filter(
            Chunk.question_hash == question_hash,
        )
        if datamodel_id:
            query = query.filter(Chunk.datamodel_id == datamodel_id)
        if document_id:
            query = query.filter(Chunk.document_id == document_id)
        chunk_obj = query.first()
        if chunk_obj is None:
            _uuid = gen_uuid()
            chunk_obj = Chunk(
                id=_uuid,
                dataset_id=dataset_id,
                document_id=document_id,
                datasource_id=datasource_id,
                datamodel_id=datamodel_id,
                chunk_type='qa',
                question=question,
                question_hash=question_hash,
            )
            set_insert_user(chunk_obj, metadata.get('user_name'))
        else:
            _uuid = chunk_obj.id
            if chunk_obj.hash == _hash and chunk_obj.del_flag == 0:
                # 发现完全相同问答，不处理
                print('发现完全相同问答，不处理')
                return
            chunk_obj.del_flag = 0
            set_update_user(chunk_obj, metadata.get('user_name'))
        chunk_obj.answer = answer,
        chunk_obj.content = content,
        chunk_obj.hash = _hash,
        chunk_obj.star_flag = metadata.get('star_flag', 0)
        db.session.add(chunk_obj)
        db.session.flush()
        db.session.commit()
        # 加入向量数据库
        vector_index = get_vector_index()
        meta_data = {
            'hash': _hash,
            'datasource_id': datasource_id,
            'datamodel_id': datamodel_id,
            'dataset_id': dataset_id,
            'document_id': document_id,
        }
        vector_index.add_texts([content], metadatas=[meta_data], ids=[_uuid])


def add_chunk(chunk_dict):
    '''
    将chunk加入知识库
    '''
    with app.app_context():
        chunk_type = chunk_dict.get('chunk_type',  'chunk')
        question = chunk_dict.get('question')
        answer = chunk_dict.get('answer')
        if chunk_type == 'qa' and question and answer:
            question = question.strip()
            content = f"问题: {question}\n答案: {answer}"
            question_hash = md5(question)
        else:
            content = chunk_dict.get('content', '')
            question_hash = None
        _hash = md5(content)
        datamodel_id = chunk_dict.get('datamodel_id')
        datasource_id = chunk_dict.get('datasource_id')
        if datamodel_id is not None:
            datamodel_obj = db.session.query(DataModel).filter(DataModel.id == datamodel_id).first()
            if datamodel_obj:
                datasource_id = datamodel_obj.datasource_id
        document_id = chunk_dict.get('document_id')
        dataset_id = chunk_dict.get('dataset_id')
        if document_id:
            document_obj = db.session.query(Document).filter(Document.id == document_id).first()
            if document_obj:
                dataset_id = document_obj.dataset_id
        chunk_obj = None
        if 'id' in chunk_dict:
            chunk_obj = Chunk.query.filter(Chunk.del_flag == 0, Chunk.id == chunk_dict['id']).first()
        if chunk_obj is None:
            _uuid = gen_uuid()
            chunk_obj = Chunk(
                id=_uuid,
            )
            set_insert_user(chunk_obj, chunk_dict.get('user_name'))
        else:
            _uuid = chunk_obj.id
            set_update_user(chunk_obj, chunk_dict.get('user_name'))
        chunk_obj.dataset_id = dataset_id,
        chunk_obj.document_id = document_id,
        chunk_obj.datasource_id = datasource_id,
        chunk_obj.datamodel_id = datamodel_id,
        chunk_obj.chunk_type = chunk_type,
        chunk_obj.question = question,
        chunk_obj.question_hash = question_hash,
        chunk_obj.answer = answer,
        chunk_obj.content = content,
        chunk_obj.hash = _hash,
        chunk_obj.star_flag = chunk_dict.get('star_flag', 0)
        db.session.add(chunk_obj)
        db.session.flush()
        db.session.commit()
        # 加入向量数据库
        vector_index = get_vector_index()
        meta_data = {
            'hash': _hash,
            'datasource_id': datasource_id,
            'datamodel_id': datamodel_id,
            'dataset_id': dataset_id,
            'document_id': document_id,
        }
        vector_index.add_texts([content], metadatas=[meta_data], ids=[_uuid])


def delete_chunk(id):
    '''
    删除知识段
    '''
    with app.app_context():
        vector_index = get_vector_index()
        try:
            vector_index.delete_by_ids([id])
        except Exception as e:
            print(e)


def train_datamodel(datamodel_id, metadata=None, chunk_strategy=None):
    '''
    将数据模型训练加入知识库
    '''
    if chunk_strategy is None:
        chunk_strategy = {'chunk_size': 1024}
    if metadata is None:
        metadata = {}
    with app.app_context():
        datasource_id = metadata.get('datasource_id')
        if datamodel_id is not None:
            datamodel_obj = db.session.query(DataModel).filter(DataModel.id == datamodel_id).first()
            if datamodel_obj:
                datasource_id = datamodel_obj.datasource_id
        flag, reader = get_reader_model({'model_id': datamodel_id})
        info_prompt = reader.get_info_prompt('')
        metadata_text = info_prompt.split('# MetaData:')[1] if '# MetaData:' in info_prompt else info_prompt
        spliter = RecursiveCharacterTextSplitter(separators=['\n\n'], chunk_size=chunk_strategy.get('chunk_size', 1024))
        chunks = spliter.split_text(metadata_text)
        for chunk in chunks:
            content = chunk.strip()
            _hash = md5(content)
            chunk_obj = db.session.query(Chunk).filter(
                Chunk.datamodel_id == datamodel_id,
                Chunk.hash == _hash,
            ).first()
            if chunk_obj is None:
                _uuid = gen_uuid()
                chunk_obj = Chunk(
                    id=_uuid,
                    datasource_id=datasource_id,
                    datamodel_id=datamodel_id,
                    chunk_type='chunk',
                    content=content,
                    hash=_hash
                )
                set_insert_user(chunk_obj, metadata.get('user_name'))
            else:
                _uuid = chunk_obj.id
                chunk_obj.del_flag = 0
                set_update_user(chunk_obj, metadata.get('user_name'))
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
            vector_index.add_texts([content], metadatas=[meta_data], ids=[_uuid])


def train_document(document_id, metadata=None,):
    '''
    将文档训练加入知识库
    '''
    if metadata is None:
        metadata = {}
    with app.app_context():
        datasource_id = metadata.get('datasource_id')
        datamodel_id = metadata.get('datamodel_id')
        if datamodel_id is not None:
            datamodel_obj = db.session.query(DataModel).filter(DataModel.id == datamodel_id).first()
            if datamodel_obj:
                datasource_id = datamodel_obj.datasource_id
        document_obj = db.session.query(Document).filter(Document.id == document_id).first()
        if document_obj is None:
            return
        dataset_id = document_obj.dataset_id
        # 解析文件
        meta_data = parse_json(document_obj.meta_data)
        chunk_strategy = parse_json(document_obj.chunk_strategy)
        setting_args = {}
        if document_obj.document_type == 'upload_file':
            file_name = meta_data.get('upload_file').split('/')[-1]
            setting_args['upload_file'] = file_name
        else:
            setting_args['website_info'] = metadata
        extract_setting = ExtractSetting(
            datasource_type=document_obj.document_type,
            **setting_args
        )
        documents = ExtractProcessor.extract(extract_setting)
        content = '\n'.join([i.page_content for i in documents])
        spliter = RecursiveCharacterTextSplitter(chunk_size=chunk_strategy.get('chunk_size', 1024))
        chunks = spliter.split_text(content)
        position = 1
        for chunk in chunks:
            content = chunk.strip()
            _hash = md5(content)
            chunk_obj = db.session.query(Chunk).filter(
                Chunk.document_id == document_id,
                Chunk.hash == _hash,
            ).first()
            if chunk_obj is None:
                _uuid = gen_uuid()
                chunk_obj = Chunk(
                    id=_uuid,
                    dataset_id=dataset_id,
                    document_id=document_id,
                    datasource_id=datasource_id,
                    datamodel_id=datamodel_id,
                    chunk_type='chunk',
                    content=content,
                    hash=_hash,
                    position=position
                )
                set_insert_user(chunk_obj, metadata.get('user_name'))
            else:
                _uuid = chunk_obj.id
                chunk_obj.del_flag = 0
                chunk_obj.position = position
                set_update_user(chunk_obj, metadata.get('user_name'))
            db.session.add(chunk_obj)
            db.session.flush()
            db.session.commit()
            # 加入向量数据库
            vector_index = get_vector_index()
            meta_data = {
                'hash': _hash,
                'dataset_id': dataset_id,
                'document_id': document_id,
                'datasource_id': datasource_id,
                'datamodel_id': datamodel_id
            }
            vector_index.add_texts([content], metadatas=[meta_data], ids=[_uuid])
            position += 1


if __name__ == '__main__':
    # metadata = {
    #     'user_name': 'admin'
    # }
    # datamodel_id = '8a862fdf980245459ac9ef89734c166f'
    # train_datamodel(datamodel_id, metadata)
    metadata = {
        'rerank': '1',
        'datamodel_id': 'e222b61c62be4d09908a5bc94aebf22d',
    }
    res = get_knowledge('根据数据画出k线图', metadata)
    print(res)
    # metadata = {
    #     'datamodel_id': '8a862fdf980245459ac9ef89734c166f',
    # }
    # res = get_knowledge('字典项最多的字典是哪个', metadata)
    # print(res)
    # delete_chunk('')
    # metadata = {
    #     'user_name': 'system',
    # }
    # train_document('597510855a6f45b68fe196dc9e74126d', metadata)
