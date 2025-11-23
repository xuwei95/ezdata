'''
数据管理相关任务
'''
import json
from celery_app import celery_app
from web_apps.datasource.db_models import DataSource
from web_apps.datamodel.db_models import DataModel
from web_apps import db, app
from utils.log_utils import get_task_logger
from utils.common_utils import gen_uuid, parse_json
from utils.etl_utils import get_reader_model
from web_apps.rag.services.rag_service import train_datamodel, train_document
# from utils.task_util import get_task_instance, update_task_instance, set_task_running_id, set_task_instance_running, set_task_instance_failed, set_task_instance_retry
# from tasks.task_runners import runner_dict, DynamicTaskRunner
# from web_apps.alert.strategys.task_alert_strategys import handle_task_fail_alert


@celery_app.task(bind=True)
def self_gen_datasource_model(self, datasource_id):
    '''
    针对数据源自动创建模型
    :return:
    '''
    with app.app_context():
        uuid = self.request.id if self.request.id else gen_uuid()
        worker = self.request.hostname if self.request.hostname else ''
        logger = get_task_logger(p_name='self_gen_datasource_model', task_log_keys={'task_uuid': uuid})
        logger.info(f'任务开始，任务id:{uuid}, 执行worker:{worker}')
        try:
            datasource_obj = db.session.query(DataSource).filter(DataSource.id == datasource_id).first()
            model_info = {
                'source': {
                    "name": "",
                    "type": datasource_obj.type,
                    "conn_conf": parse_json(datasource_obj.conn_conf),
                    "ext_params": {}
                },
                'model': {},
                'extract_info': {
                    'batch_size': 1,
                    'extract_rules': []
                }
            }
            flag, reader = get_reader_model(model_info)
            if flag:
                flag, res = reader.connect()
            if not flag:
                logger.info('数据源连接失败')
                return
            model_list = reader.gen_models()
            for model in model_list:
                exist_objs = db.session.query(DataModel).filter(DataModel.datasource_id == datasource_id,
                                                                DataModel.del_flag == 0,
                                                                DataModel.type == model['type']).all()
                exist_objs = [i for i in exist_objs if parse_json(i.model_conf)['name'] == model['model_conf']['name']]
                if exist_objs == []:
                    model_obj = DataModel(
                        id=gen_uuid(),
                        name=model['model_conf']['name'],
                        datasource_id=datasource_id,
                        type=model['type'],
                        status=1,
                        model_conf=json.dumps(model['model_conf'], ensure_ascii=False),
                        can_interface=1,
                        create_by='system',
                        description="数据源自动建模创建模型"
                    )
                    db.session.add(model_obj)
                    db.session.commit()
                    db.session.flush()
                    logger.info(f"数据源自动建模创建模型{model}成功，模型id为{model_obj.id}")
        except Exception as e:
            logger.exception(e)


@celery_app.task(bind=True)
def self_train_rag_data(self, _id, metadata=None, train_type='document'):
    '''
    rag训练文档
    :return:
    '''
    if metadata is None:
        metadata = {}
    with app.app_context():
        uuid = self.request.id if self.request.id else gen_uuid()
        worker = self.request.hostname if self.request.hostname else ''
        logger = get_task_logger(p_name='self_train_rag_data', task_log_keys={'task_uuid': uuid})
        logger.info(f'任务开始，任务id:{uuid}, 执行worker:{worker}')
        try:
            if train_type == 'document':
                train_document(_id, metadata=metadata)
            else:
                train_datamodel(_id, metadata=metadata)
        except Exception as e:
            logger.exception(e)


if __name__ == '__main__':
    a = self_gen_datasource_model('fdf0938c7d5a44eca94ba093cc8be6c8')


