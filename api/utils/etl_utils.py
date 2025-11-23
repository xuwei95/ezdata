#-*- coding:utf-8 -*-
"""
ETL Utils - 使用 ETL2 重构版本
提供向后兼容的接口，使用 ETL2 的注册中心和任务类
"""
from web_apps.datamodel.services.datamodel_service import gen_datasource_model_info, gen_extract_info, gen_load_info
from etl2.registry import get_reader, get_writer, get_registry
from etl2.etl_task import EtlTask
from utils.common_utils import get_res_fields

# 向后兼容的导出
__all__ = [
    'MyEtlTask',
    'get_reader_model',
    'get_writer_model',
    'get_res_fields',
    # ETL2 直接导出
    'get_reader',
    'get_writer',
    'EtlTask',
    'get_registry'
]


class MyEtlTask(EtlTask):

    def __init__(self, task_params):
        super().__init__(task_params)

    def gen_data_models(self):
        '''
        获取读取或写入数据模型
        使用 ETL2 的注册中心
        :return:
        '''
        self.extract_info = self.params.get('extract', {})
        self.extract_type = self.extract_info.get('extract_type', 'once')
        flag, reader = get_reader_model(self.extract_info)
        if flag:
            self.reader = reader
        else:
            self.error_list.append(reader)
            self.reader = None
        if self.load_info is not None:
            flag, writer = get_writer_model(self.load_info)
            if flag:
                self.writer = writer
            else:
                self.writer = None
        else:
            self.writer = None


def get_reader_model(extract_info):
    '''
    获取reader对象
    使用 ETL2 的注册中心
    :return:
    '''
    # 若有数据源ID，查表从系统数据源表获取信息
    if 'datasource_id' in extract_info:
        flag, extract_info = gen_datasource_model_info(extract_info['datasource_id'])
        if not flag:
            return False, extract_info
    # 若有数据模型ID，查表从系统数据模型表获取信息
    if 'model_id' in extract_info:
        flag, extract_info = gen_extract_info(extract_info)
        if not flag:
            return False, extract_info
    try:
        # 使用 ETL2 的注册中心获取 reader
        flag, data_model = get_reader(extract_info)
        return flag, data_model
    except Exception as e:
        return False, str(e)


def get_writer_model(load_info):
    '''
    获取writer对象
    使用 ETL2 的注册中心
    :return:
    '''
    if 'model_id' in load_info:
        # 若有数据模型ID，查表从系统数据模型表获取信息
        flag, load_info = gen_load_info(load_info)
        if not flag:
            return False, load_info
    try:
        # 使用 ETL2 的注册中心获取 writer
        flag, data_model = get_writer(load_info)
        return flag, data_model
    except Exception as e:
        return False, str(e)


