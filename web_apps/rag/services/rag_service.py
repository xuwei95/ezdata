from web_apps import db, app
from utils.auth import set_insert_user, set_update_user
from utils.etl_utils import get_reader_model
from utils.common_utils import gen_uuid, md5, parse_json
from web_apps.rag.splitter.text_splitter import RecursiveCharacterTextSplitter
from web_apps.rag.db_models import Document, Chunk
from web_apps.datamodel.db_models import DataModel
from web_apps.rag.extractor.extract_processor import ExtractProcessor, ExtractSetting
from web_apps.rag.extractor.entity.extract_setting import WebsiteInfo
from web_apps.rag.utils import vector_index, text_index, rerank_runner, VECTOR_STORE_TYPE, TEXT_STORE_TYPE
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy


def add_chunks_to_store(contents, metadatas):
    '''
    添加知识段到存储
    '''
    with app.app_context():
        ids = [i['chunk_id'] for i in metadatas]
        if vector_index is not None:
            vector_index.add_texts(contents, metadatas=metadatas, ids=ids)
        if text_index is not None:
            # 添加全文索引
            text_index.add_texts(contents, metadatas=metadatas, ids=ids)


def delete_chunk(id):
    '''
    从存储中删除知识段
    '''
    with app.app_context():
        try:
            if vector_index is not None:
                # 从向量索引中删除
                vector_index.delete_by_ids([id])
            if text_index is not None:
                # 从全文索引中删除
                text_index.delete_by_ids([id])
        except Exception as e:
            print(e)


def query_knowledge(question, search_kwargs):
    with app.app_context():
        retrieval_type = search_kwargs.get('retrieval_type', 'vector')
        if 'retrieval_type' in search_kwargs:
            search_kwargs.pop('retrieval_type')
        kwargs = {
            'search_kwargs': search_kwargs,
            'search_type': 'similarity_score_threshold'
        }
        documents = []
        if retrieval_type in ['all', 'vector'] and vector_index is not None:
            # 向量检索
            try:
                documents += vector_index.search(question, **kwargs)
            except Exception as e:
                print(e)
        if retrieval_type in ['all', 'keyword'] and text_index is not None:
            # 全文检索
            try:
                documents += text_index.search(question, **kwargs)
            except Exception as e:
                print(e)
        return documents


def get_knowledge(question, metadata=None, res_type='text'):
    '''
    根据问题查询知识库知识
    '''
    if metadata is None:
        metadata = {}
    with app.app_context():
        if 'score_threshold' in metadata:
            score_threshold = float(metadata['score_threshold'])
        else:
            score_threshold = 0
        k = int(metadata.get('k', 5))
        search_kwargs = {
            'filter': {},
            'score_threshold': score_threshold,
            'k': k,
            'retrieval_type': metadata.get('retrieval_type', 'vector')
        }
        datamodel_ids = []
        if 'datamodel_id' in metadata:
            datamodel_ids = metadata['datamodel_id'].split(',') if isinstance(metadata['datamodel_id'], str) else metadata['datamodel_id']
        dataset_ids = []
        if 'dataset_id' in metadata:
            dataset_ids = metadata['dataset_id'].split(',') if isinstance(metadata['dataset_id'], str) else metadata['dataset_id']
        search_kwargs_list = []
        if dataset_ids == [] and datamodel_ids == []:
            search_kwargs_list = [search_kwargs]
        else:
            # 遍历每个条件，组成查询参数
            for dataset_id in dataset_ids:
                _search_kwargs = deepcopy(search_kwargs)
                _search_kwargs['filter']['dataset_id'] = dataset_id
                search_kwargs_list.append(_search_kwargs)
            for datamodel_id in datamodel_ids:
                _search_kwargs = deepcopy(search_kwargs)
                _search_kwargs['filter']['datamodel_id'] = datamodel_id
                search_kwargs_list.append(_search_kwargs)
        if len(search_kwargs_list) <= 1:
            documents = query_knowledge(question, search_kwargs_list[0])
        else:
            # 多线程召回
            documents = []  # 存储所有文档的总列表
            with ThreadPoolExecutor(max_workers=min(len(search_kwargs_list), 8)) as executor:
                # 创建未来任务列表
                future_to_search_kwargs = {executor.submit(query_knowledge, question, kwargs): kwargs for kwargs in
                                           search_kwargs_list}
                # 遍历完成的未来任务
                for future in as_completed(future_to_search_kwargs):
                    result = future.result()  # 获取返回的文档
                    documents.extend(result)  # 将返回的文档添加到总列表中
        # 结果去重
        doc_id = []
        unique_documents = []
        for document in documents:
            _hash = md5(document.page_content)
            if _hash not in doc_id:
                doc_id.append(_hash)
                unique_documents.append(document)
        documents = unique_documents
        if len(documents) > k:
            # 召回数量过多，重排序取 topk
            if str(metadata.get('rerank')) == '1' and rerank_runner is not None:
                # 调用rerank模型重排序
                if 'rerank_score_threshold' in metadata:
                    rerank_score_threshold = float(metadata['rerank_score_threshold'])
                else:
                    rerank_score_threshold = 0
                documents = rerank_runner.run(question, documents, top_n=k,  score_threshold=rerank_score_threshold)
            else:
                # 直接按分数排序
                documents = sorted(documents, key=lambda x: x.metadata.get('score', 0), reverse=True)[:k]
        if res_type == 'documents':
            return documents
        if documents == []:
            return ''
        knowledge = '\n\n'.join([d.page_content for d in documents])
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
        query = db.session.query(Chunk).filter(Chunk.del_flag == 0, Chunk.star_flag == 1).filter(Chunk.question_hash == question_hash)
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
        # 加入检索数据库
        meta_data = {
            'chunk_id': _uuid,
            'datasource_id': datasource_id,
            'datamodel_id': datamodel_id,
            'dataset_id': dataset_id,
            'document_id': document_id,
        }
        add_chunks_to_store([content], metadatas=[meta_data])


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
        # 加入检索数据库
        meta_data = {
            'chunk_id': _uuid,
            'datasource_id': datasource_id,
            'datamodel_id': datamodel_id,
            'dataset_id': dataset_id,
            'document_id': document_id,
        }
        add_chunks_to_store([content], metadatas=[meta_data])


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
            # 加入检索数据库
            meta_data = {
                'chunk_id': _uuid,
                'datasource_id': datasource_id,
                'datamodel_id': datamodel_id
            }
            add_chunks_to_store([content], metadatas=[meta_data])


def train_document(document_id, metadata=None):
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
        # 标记训练中
        document_obj.status = 2
        db.session.add(document_obj)
        db.session.flush()
        db.session.commit()
        try:
            dataset_id = document_obj.dataset_id
            # 解析文件
            meta_data = parse_json(document_obj.meta_data)
            chunk_strategy = parse_json(document_obj.chunk_strategy)
            setting_args = {}
            if document_obj.document_type == 'upload_file':
                file_name = meta_data.get('upload_file').split('/')[-1]
                setting_args['upload_file'] = file_name
            else:
                setting_args['website_info'] = WebsiteInfo(
                    url=meta_data.get('url'),
                    provider=meta_data.get('provider', 'base')
                )
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
                # 加入检索数据库
                meta_data = {
                    'chunk_id': _uuid,
                    'dataset_id': dataset_id,
                    'document_id': document_id,
                    'datasource_id': datasource_id,
                    'datamodel_id': datamodel_id
                }
                add_chunks_to_store([content], metadatas=[meta_data])
                position += 1
            # 标记训练成功
            document_obj.status = 3
            db.session.add(document_obj)
            db.session.flush()
            db.session.commit()
        except Exception as e:
            print(e)
            # 标记训练失败
            document_obj.status = 4
            db.session.add(document_obj)
            db.session.flush()
            db.session.commit()



if __name__ == '__main__':
    # metadata = {
    #     'user_name': 'admin'
    # }
    # datamodel_id = '8a862fdf980245459ac9ef89734c166f'
    # train_datamodel(datamodel_id, metadata)
    # metadata = {
    #     'rerank': '1',
    #     'datamodel_id': 'e222b61c62be4d09908a5bc94aebf22d',
    # }
    # res = get_knowledge('根据数据画出k线图', metadata)
    # print(res)
    # metadata = {
    #     'retrieval_type': 'all',
    #     'dataset_id': '0e0e85ffc5564674b59da8a563d5a2a3',
    #     'datamodel_id': '8a862fdf980245459ac9ef89734c166f',
    # }
    # res = get_knowledge('字典项最多的字典是哪个', metadata)
    # print(res)
    # delete_chunk('')
    metadata = {
        'user_name': 'system',
    }
    train_document('cb5d2213cf4d469c95110332d5755ef9', metadata)
