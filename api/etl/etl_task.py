# -*- coding: utf-8 -*-
"""
ETL 任务类
基于新的注册中心和 MindsDB 适配器
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import logging
from etl.registry import get_reader, get_writer
from etl.transform_algs import transform_alg_dict
from utils.common_utils import gen_json_response, get_res_fields, df_to_list


class EtlTask(object):
    """
    ETL 任务类
    兼容原有 EtlTask 接口，使用新的注册中心
    """

    def __init__(self, task_params):
        self.params = task_params
        self.extract = self.params.get('extract')
        self.extract_info = self.extract.get('extract_info', {})
        self.extract_type = self.extract_info.get('extract_type', 'once')
        self.process_rules = task_params.get('process_rules', [])
        self.load_info = self.params.get('load')
        self.error_list = []

        # 拓展处理算法
        self.transform_alg_dict = transform_alg_dict
        extend_alg_dict = task_params.get('extend_alg_dict', {})
        if isinstance(extend_alg_dict, dict):
            for k, v in extend_alg_dict.items():
                self.transform_alg_dict[k] = v

    def gen_data_models(self):
        '''
        获取读取或写入数据模型
        使用新的注册中心
        '''
        # 获取 reader
        flag, reader = get_reader(self.extract)
        if flag:
            self.reader = reader
        else:
            self.error_list.append(reader)
            self.reader = None

        # 获取 writer
        if self.load_info is not None:
            flag, writer = get_writer(self.load_info)
            if flag:
                self.writer = writer
            else:
                self.writer = None
        else:
            self.writer = None

    def process_batch(self, res_data, run_load=True):
        '''
        迭代生成器批量处理数据
        :param res_data: 输入数据
        :param run_load: 是否执行数据装载
        :return: (success, result_data)
        '''
        # 数据转换
        idx = 1
        context = {}
        for rule in self.process_rules:
            method_code = rule.get('code')
            alg_method = self.transform_alg_dict.get(method_code)
            if not alg_method:
                return False, f'数据转换第{idx}条规则出错：未找到处理函数{method_code}'
            rule_dict = rule.get('rule_dict')
            flag, res_data = alg_method(res_data, rule_dict, context)
            if not flag:
                return False, f'数据转换第{idx}条规则出错：{res_data}'
            idx += 1

        # 数据装载
        if run_load:
            if not self.writer:
                return False, f'数据装载出错：未找到数据装载对象'
            flag, res_data = self.writer.write(res_data)
            if not flag:
                return False, f'数据装载出错：{res_data}'

        return True, res_data

    def process_once(self, page=1, pagesize=20, run_load=True):
        '''
        单次处理数据
        :param page: 读取页数
        :param pagesize: 每页数量
        :param run_load: 是否执行数据装载
        :return: (success, message)
        '''
        # 数据抽取
        flag, res_data = self.reader.read_page(page, pagesize)
        if not flag:
            return False, f"数据抽取出错：{res_data}"

        # 抽取成功，取出其中的数据
        res_data = res_data['data']

        # 数据转换
        idx = 1
        context = {}
        for rule in self.process_rules:
            method_code = rule.get('code')
            rule_dict = rule.get('rule_dict')
            alg_method = self.transform_alg_dict.get(method_code)
            if not alg_method:
                return False, f'数据转换第{idx}条规则出错：未找到处理函数{method_code}'
            flag, res_data = alg_method(res_data, rule_dict, context)
            if not flag:
                return False, f'数据转换第{idx}条规则出错：{res_data}'
            idx += 1

        # 数据装载
        if run_load:
            if not self.writer:
                return False, f'数据装载出错：未找到数据装载对象'
            flag, res_data = self.writer.write(res_data)
            if not flag:
                return False, f'数据装载出错：{res_data}'

        return True, '数据处理完成'

    def preview(self, run_load=False):
        '''
        处理数据预览模式，检查数据抽取转换流程
        :param run_load: 是否执行数据装载
        :return: 预览结果字典
        '''
        if self.error_list != []:
            res_info = {
                'code': 500,
                'msg': f"任务初始化出错：{','.join(self.error_list)}"
            }
            return res_info

        # 数据抽取，抽取最多1000条测试数据
        page_size = self.extract_info.get('batch_size', 1000)
        if page_size > 1000:
            page_size = 1000

        flag, res_data = self.reader.read_page(pagesize=page_size)
        if not flag:
            res_info = {
                'code': 500,
                'msg': f"数据抽取出错：{res_data}"
            }
            return res_info

        # 抽取成功，取出其中的数据
        res_data = res_data['data']

        # 数据转换
        idx = 1
        context = {}
        for rule in self.process_rules:
            method_code = rule.get('code')
            rule_dict = rule.get('rule_dict')
            alg_method = self.transform_alg_dict.get(method_code)
            if not alg_method:
                res_info = {
                    'code': 500,
                    'msg': f'数据转换第{idx}条规则出错：未找到处理函数{method_code}'
                }
                return res_info
            flag, res_data = alg_method(res_data, rule_dict, context)
            if not flag:
                res_info = {
                    'code': 500,
                    'msg': f'数据转换第{idx}条规则出错：{res_data}'
                }
                return res_info
            idx += 1

        # 数据装载（预览模式）
        if run_load:
            if not self.writer:
                res_info = {
                    'code': 500,
                    'msg': f'数据装载出错：未找到数据装载对象'
                }
                return res_info
            flag, res_data = self.writer.write(res_data)
            if not flag:
                res_info = {
                    'code': 500,
                    'msg': f'数据装载出错：{res_data}'
                }
                return res_info

        # 若是dataframe，转回json数据用于前端展示
        flag, res_data = df_to_list(res_data)
        if not flag:
            res_info = {
                'code': 500,
                'msg': f'{res_data}'
            }
            return res_info

        # 获取返回字段
        res_fields = get_res_fields(res_data)

        # 获取数据筛选规则列表
        extract_rules = self.reader.get_extract_rules()
        search_type_list = self.reader.get_search_type_list()

        res_data = {
            'data': res_data,
            'fields': res_fields,
            'extract_rules': extract_rules,
            'search_type_list': search_type_list,
        }

        return gen_json_response(data=res_data)


def etl_task_process(params, run_load=False, logger=None, task_class=None):
    '''
    执行处理任务
    :param params: 任务参数
    :param run_load: 是否执行装载
    :param logger: 日志对象
    :param task_class: 任务类（默认使用 EtlTask2）
    :return: None
    '''
    if logger is None:
        logger = logging.getLogger(__name__)

    if task_class is None:
        task_class = EtlTask

    etl_task = task_class(params)
    etl_task.gen_data_models()

    if etl_task.error_list != []:
        logger.error(f"任务初始化出错：{','.join(etl_task.error_list)}")
        return

    batch_size = etl_task.reader.batch_size
    extract_type = etl_task.extract_type

    if extract_type == 'once':
        # 单次处理
        flag, res_data = etl_task.process_once(pagesize=batch_size, run_load=run_load)
        if not flag:
            logger.error(f'数据处理出错：{res_data}')
        else:
            logger.info('数据处理完成')

    elif extract_type in ['batch', 'flow']:
        # 批量处理
        reader_gen = etl_task.reader.read_batch()
        while reader_gen:
            try:
                flag, res_data = next(reader_gen)
                if not flag:
                    logger.error(f"数据抽取出错：{res_data}")
                    break

                # 抽取成功，取出其中的数据
                res_data = res_data['data']

                # 处理批次数据
                flag, res_data = etl_task.process_batch(res_data, run_load=run_load)
                if not flag:
                    logger.error(f"数据处理出错：{res_data}")
                    break

            except StopIteration:
                logger.info('数据处理完成')
                break
            except Exception as e:
                logger.exception(e)
                break
