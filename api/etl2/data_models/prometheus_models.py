# coding: utf-8
"""
Prometheus 数据模型
支持 PromQL 查询和 Metric 查询两种模式
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from etl2.data_models import DataModel
from etl.utils.common_utils import trans_rule_value, gen_json_response, format_date
from etl.libs.prometheus import PrometheusClient
from utils.common_utils import df_to_list
import logging

logger = logging.getLogger(__name__)


class BasePromModel(DataModel):
    """
    Prometheus 基础模型
    """

    def __init__(self, model_info):
        super().__init__(model_info)
        self.conn_conf = self._source.get('conn_conf', {})
        self.model_conf = self._model.get('model_conf', {})
        self.url = self.conn_conf.get('url')
        self.auth_types = self.model_conf.get('auth_type', '').split(',')
        self._client = PrometheusClient(**{"url": self.url, 'disable_ssl': True})

    @staticmethod
    def get_connection_args():
        """
        获取连接参数定义
        """
        return {
            'url': {
                'type': 'string',
                'required': True,
                'description': 'Prometheus服务器地址',
                'example': 'http://localhost:9090'
            },
            'disable_ssl': {
                'type': 'boolean',
                'required': False,
                'description': '是否禁用SSL验证',
                'default': True
            },
            'headers': {
                'type': 'object',
                'required': False,
                'description': '自定义HTTP请求头（用于认证等）',
                'example': {'Authorization': 'Bearer token'}
            }
        }

    def connect(self):
        """
        连通性测试
        """
        try:
            self._client.conn_test()
            return True, '连接成功'
        except Exception as e:
            logger.error(f"Prometheus连接失败: {e}")
            return False, str(e)[:100]

    def get_info_prompt(self, model_prompt=''):
        """
        获取使用提示及元数据信息
        """
        try:
            metrics = self._client.get_all_metrics()
            info_prompt = f"""
一个读取Prometheus的模型类，并且提供了一些数据操作的方法
类中部分参数如下:
_client: prometheus_api_client库的PrometheusConnect(**kwargs)
# 使用示例：
实例化此类的reader对象，查询promql数据：
reader._client.query(promql, **query_dict)

# DataSource type:
prometheus
# MetaData:
可用指标数量: {len(metrics) if metrics else 0}
            """
            return info_prompt
        except Exception as e:
            logger.error(f"获取Prometheus元数据失败: {e}")
            return "Prometheus Model"

    def disconnect(self):
        """
        断开连接（Prometheus API客户端通常不需要显式断开）
        """
        pass

    def __del__(self):
        self.disconnect()


class PromMetricModel(BasePromModel):
    """
    Prometheus Metric 模型
    用于查询特定的Prometheus指标
    """

    def __init__(self, model_info):
        super().__init__(model_info)
        self.metric = self.model_conf.get('name')

    @classmethod
    def get_form_config(cls):
        """
        获取Metric模型的配置表单schema
        """
        return [
            {
                'label': '指标名称',
                'field': 'name',
                'required': True,
                'component': 'Input',
                'default': '',
                'placeholder': '例如: node_cpu_seconds_total'
            },
            {
                'label': '允许操作',
                'field': 'auth_type',
                'component': 'JCheckbox',
                'default': 'query,extract',
                'componentProps': {
                    'options': [
                        {'label': '查询', 'value': 'query'},
                        {'label': '数据抽取', 'value': 'extract'}
                    ]
                }
            }
        ]

    def connect(self):
        """
        连通性测试（验证指标是否存在）
        """
        try:
            all_metrics = self._client.get_all_metrics()
            if self.metric in all_metrics:
                return True, '连接成功'
            else:
                return False, '未找到该指标'
        except Exception as e:
            logger.error(f"验证Prometheus指标失败: {e}")
            return False, str(e)[:100]

    def get_res_fields(self):
        """
        获取字段列表
        """
        # Prometheus结果通常包含metric和value字段
        return [
            {'field_name': 'metric', 'field_value': 'metric'},
            {'field_name': 'value', 'field_value': 'value'},
            {'field_name': 'timestamp', 'field_value': 'timestamp'}
        ]

    def get_search_type_list(self):
        """
        获取可用高级查询类型
        """
        return []

    def get_extract_rules(self):
        """
        获取可筛选项
        """
        rules = [
            {
                'name': '开始时间',
                'value': 'start_time',
                'default': ''
            },
            {
                'name': '结束时间',
                'value': 'end_time',
                'default': ''
            },
            {
                'name': '步长',
                'value': 'step',
                'default': ''
            }
        ]
        return rules

    def gen_extract_rules(self):
        """
        解析筛选规则
        """
        try:
            query_dict = {}
            for i in self.extract_rules:
                field = i.get('field')
                rule = i.get('rule')
                value = i.get('value')
                value = trans_rule_value(value)
                if field and value:
                    if rule == 'start_time':
                        start_time = format_date(value, res_type='timestamp')
                        if start_time is not None:
                            query_dict['start_time'] = start_time
                    if rule == 'end_time':
                        end_time = format_date(value, res_type='timestamp')
                        if end_time is not None:
                            query_dict['end_time'] = end_time
                    if rule == 'step':
                        try:
                            query_dict['step'] = float(value)
                        except Exception as e:
                            logger.warning(f"步长转换失败: {e}")

            data_li = self._client.query(self.metric, **query_dict)
            return True, data_li
        except Exception as e:
            logger.error(f"查询Prometheus指标失败: {e}")
            return False, str(e)[:500]

    def query(self, promql=None, **kwargs):
        """
        执行PromQL查询
        """
        if not self._client:
            flag, msg = self.connect()
            if not flag:
                raise RuntimeError(f'连接失败: {msg}')

        if promql is None:
            promql = self.metric

        return self._client.query(promql, **kwargs)

    def read_page(self, page=1, pagesize=20):
        """
        分页读取数据
        """
        flag, res_data = self.gen_extract_rules()
        if not flag:
            return False, res_data

        total = len(res_data)
        data_li = res_data[(page - 1) * pagesize:page * pagesize]
        res_data = {
            'records': data_li,
            'total': total
        }
        return True, gen_json_response(data=res_data)

    def read_batch(self):
        """
        生成器分批读取数据
        """
        flag, res_data = self.gen_extract_rules()
        if not flag:
            yield False, res_data
            return

        total = len(res_data)
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            result = {
                'records': res_data[(page - 1) * pagesize:page * pagesize],
                'total': total
            }
            yield True, gen_json_response(result)


class PromQlModel(BasePromModel):
    """
    Prometheus PromQL 模型
    用于执行自定义的PromQL查询
    """

    def __init__(self, model_info):
        super().__init__(model_info)
        promql = self.model_conf.get('promql', '')
        self.promql = promql
        self.default_promql = promql

    @classmethod
    def get_form_config(cls):
        """
        获取PromQL模型的配置表单schema
        """
        return [
            {
                'label': 'PromQL查询语句',
                'field': 'promql',
                'required': True,
                'component': 'MonacoEditor',
                'default': '',
                'placeholder': '例如: rate(http_requests_total[5m])',
                'componentProps': {
                    'language': 'promql',
                }
            },
            {
                'label': '允许操作',
                'field': 'auth_type',
                'component': 'JCheckbox',
                'default': 'query,extract',
                'componentProps': {
                    'options': [
                        {'label': '查询', 'value': 'query'},
                        {'label': '自定义PromQL', 'value': 'custom_sql'},
                        {'label': '数据抽取', 'value': 'extract'}
                    ]
                }
            }
        ]

    def get_res_fields(self):
        """
        获取字段列表
        """
        # PromQL结果字段通常是动态的
        return [
            {'field_name': 'metric', 'field_value': 'metric'},
            {'field_name': 'value', 'field_value': 'value'},
            {'field_name': 'timestamp', 'field_value': 'timestamp'}
        ]

    def get_search_type_list(self):
        """
        获取可用高级查询类型
        """
        return [
            {
                'name': 'promql',
                'value': 'promql',
                'default': self.promql
            }
        ]

    def get_extract_rules(self):
        """
        获取可筛选项
        """
        rules = [
            {
                'name': '开始时间',
                'value': 'start_time',
                'default': ''
            },
            {
                'name': '结束时间',
                'value': 'end_time',
                'default': ''
            },
            {
                'name': '步长',
                'value': 'step',
                'default': ''
            }
        ]
        return rules

    def gen_extract_rules(self):
        """
        解析筛选规则
        """
        try:
            # 检查是否有自定义PromQL
            rules = [i for i in self.extract_rules if i['field'] == 'search_text' and i['rule'] == 'promql' and i['value']]
            if rules:
                self.promql = rules[0].get('value')

            # 权限检查
            if 'custom_sql' not in self.auth_types and self.promql != self.default_promql:
                return False, '无修改promql权限'

            # 构建查询参数
            query_dict = {}
            for i in self.extract_rules:
                field = i.get('field')
                rule = i.get('rule')
                value = i.get('value')
                value = trans_rule_value(value)
                if field and value:
                    if rule == 'start_time':
                        start_time = format_date(value, res_type='timestamp')
                        if start_time is not None:
                            query_dict['start_time'] = start_time
                    if rule == 'end_time':
                        end_time = format_date(value, res_type='timestamp')
                        if end_time is not None:
                            query_dict['end_time'] = end_time
                    if rule == 'step':
                        try:
                            query_dict['step'] = float(value)
                        except Exception as e:
                            logger.warning(f"步长转换失败: {e}")

            data_li = self._client.query(self.promql, **query_dict)
            return True, data_li
        except Exception as e:
            logger.error(f"执行PromQL查询失败: {e}")
            return False, str(e)[:500]

    def query(self, promql=None, **kwargs):
        """
        执行PromQL查询
        """
        if not self._client:
            flag, msg = self.connect()
            if not flag:
                raise RuntimeError(f'连接失败: {msg}')

        if promql is None:
            promql = self.promql

        return self._client.query(promql, **kwargs)

    def read_page(self, page=1, pagesize=20):
        """
        分页读取数据
        """
        flag, res_data = self.gen_extract_rules()
        if not flag:
            return False, res_data

        total = len(res_data)
        data_li = res_data[(page - 1) * pagesize:page * pagesize]
        res_data = {
            'records': data_li,
            'total': total
        }
        return True, gen_json_response(data=res_data)

    def read_batch(self):
        """
        生成器分批读取数据
        """
        flag, res_data = self.gen_extract_rules()
        if not flag:
            yield False, res_data
            return

        total = len(res_data)
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            result = {
                'records': res_data[(page - 1) * pagesize:page * pagesize],
                'total': total
            }
            yield True, gen_json_response(result)
