# coding: utf-8
"""
HTTP 数据模型
支持 HTTP API 调用和 HTML 页面获取
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from etl.data_models import DataModel
from utils.common_utils import trans_rule_value, gen_json_response, parse_json, request_url
from utils.common_utils import df_to_list
import logging

logger = logging.getLogger(__name__)


class BaseHttpModel(DataModel):
    """
    HTTP 基础模型
    """

    def __init__(self, model_info):
        super().__init__(model_info)
        self.conn_conf = self._source.get('conn_conf', {})
        self.model_conf = self._model.get('model_conf', {})
        self.url = self.conn_conf.get('url')
        self.method = self.conn_conf.get('method', 'GET').upper()
        self.headers = parse_json(self.conn_conf.get('headers', '{}'))

        # 处理timeout参数
        try:
            timeout_val = self.conn_conf.get('timeout', 60)
            self.timeout = int(timeout_val) if timeout_val else 60
        except (ValueError, TypeError) as e:
            logger.warning(f"timeout参数转换失败: {e}, 使用默认值60")
            self.timeout = 60

        self.req_body = parse_json(self.conn_conf.get('req_body', '{}'))
        self.req_params = {}
        self.auth_types = self.model_conf.get('auth_type', '').split(',')
        self.response = None

    @staticmethod
    def get_connection_args():
        """
        获取连接参数定义
        """
        return {
            'url': {
                'type': 'string',
                'required': True,
                'description': 'HTTP请求地址',
                'example': 'https://api.example.com/data'
            },
            'method': {
                'type': 'select',
                'required': False,
                'description': 'HTTP请求方法',
                'default': 'GET',
                'componentProps': {
                    'options': [
                        {'label': 'GET', 'value': 'get'},
                        {'label': 'POST', 'value': 'post'},
                        {'label': 'PUT', 'value': 'put'},
                        {'label': 'DELETE', 'value': 'delete'},
                    ]
                }
            },
            'headers': {
                'type': 'string',
                'required': False,
                'description': 'HTTP请求头',
                'default': 'application/json',
            },
            'req_body': {
                'type': 'object',
                'required': False,
                'description': '请求体（JSON格式，POST/PUT等方法使用）',
                'default': '{}',
            },
            'timeout': {
                'type': 'number',
                'required': False,
                'description': '请求超时时间（秒）',
                'default': 60,
                'example': 60
            }
        }

    @classmethod
    def get_form_config(cls):
        """
        获取基础模型配置表单schema
        """
        return [
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

    def get_search_type_list(self):
        """
        获取可用高级查询类型
        """
        return [
            {
                'name': '请求参数',
                'value': 'req_body',
                'default': str(self.req_body)
            }
        ]

    def connect(self):
        """
        连通性测试
        """
        try:
            # 检查是否有自定义请求体
            body_rules = [i for i in self.extract_rules if
                         i.get('field') == 'search_text' and i.get('rule') == 'req_body' and i.get('value')]
            if body_rules:
                req_body = parse_json(body_rules[0]['value'])
                if req_body is not None:
                    if self.method == 'GET':
                        self.req_params = req_body
                    else:
                        self.req_body = req_body

            self.response = request_url(
                method=self.method,
                url=self.url,
                headers=self.headers,
                params=self.req_params,
                data=self.req_body,
                timeout=self.timeout
            )

            if self.response.status_code >= 400:
                return False, f'HTTP错误: {self.response.status_code}'

            return True, '连接成功'
        except Exception as e:
            logger.error(f"HTTP连接失败: {e}")
            return False, str(e)[:100]

    def get_info_prompt(self, model_prompt=''):
        """
        获取使用提示及元数据信息
        """
        try:
            self.connect()
            response_preview = self.response.text[:1000] if self.response else 'No response'
            info_prompt = f"""
一个HTTP读取封装类
# 使用示例：
实例化此类的reader对象，读取结果：
res_text = reader.response.text

# DataSource type:
http
# MetaData:
URL: {self.url}
Method: {self.method}
Response preview: {response_preview}
            """
            return info_prompt
        except Exception as e:
            logger.error(f"获取HTTP元数据失败: {e}")
            return "HTTP Model"

    def gen_models(self):
        """
        生成子数据模型
        """
        model_list = []
        try:
            if not self.response:
                self.connect()

            # 尝试解析为JSON
            try:
                parse_json(self.response.text)
                _type = 'json'
            except:
                _type = 'html'

            dic = {
                'type': f'http_{_type}',
                'model_conf': {
                    'name': f'http_{_type}',
                    'auth_type': 'query,extract'
                }
            }
            model_list.append(dic)
        except Exception as e:
            logger.error(f"生成子模型失败: {e}")

        return model_list

    def disconnect(self):
        """
        断开连接
        """
        self.response = None

    def __del__(self):
        self.disconnect()


class HttpApiModel(BaseHttpModel):
    """
    HTTP API 模型
    用于处理返回JSON数据的HTTP API
    """

    def __init__(self, model_info):
        super().__init__(model_info)

    @classmethod
    def get_form_config(cls):
        """
        获取API模型的配置表单schema
        """
        return [
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

    def get_res_fields(self):
        """
        获取字段列表
        """
        try:
            if not self.response:
                flag, msg = self.connect()
                if not flag:
                    return []

            result = parse_json(self.response.text)
            if isinstance(result, list) and result:
                sample = result[0]
            elif isinstance(result, dict):
                sample = result
            else:
                return []

            fields = []
            if isinstance(sample, dict):
                for key in sample.keys():
                    fields.append({'field_name': key, 'field_value': key})

            return fields
        except Exception as e:
            logger.warning(f"获取字段列表失败: {e}")
            return []

    def query(self, **kwargs):
        """
        执行查询
        """
        flag, msg = self.connect()
        if not flag:
            raise RuntimeError(f'连接失败: {msg}')

        try:
            result = parse_json(self.response.text)
            return result
        except Exception as e:
            raise RuntimeError(f'解析响应失败: {e}')

    def read_page(self, page=1, pagesize=20):
        """
        分页读取数据
        """
        flag, err = self.connect()
        if not flag:
            return False, err

        try:
            result = parse_json(self.response.text)
            if isinstance(result, list):
                total = len(result)
                data_li = result
            else:
                total = 1
                data_li = [result]

            res_data = {
                'records': data_li,
                'total': total,
                'pagination': False  # 禁用分页
            }
            return True, gen_json_response(data=res_data)
        except Exception as e:
            logger.error(f"读取HTTP API数据失败: {e}")
            return False, str(e)[:200]

    def read_batch(self):
        """
        生成器分批读取数据
        """
        flag, result = self.read_page()
        yield flag, result


class HttpHtmlModel(BaseHttpModel):
    """
    HTTP HTML 模型
    用于获取HTML页面内容
    """

    def __init__(self, model_info):
        super().__init__(model_info)

    @classmethod
    def get_form_config(cls):
        """
        获取HTML模型的配置表单schema
        """
        return [
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

    def get_res_fields(self):
        """
        获取字段列表
        """
        return [
            {'field_name': 'html', 'field_value': 'html'},
            {'field_name': 'status_code', 'field_value': 'status_code'},
            {'field_name': 'content_type', 'field_value': 'content_type'}
        ]

    def query(self, **kwargs):
        """
        执行查询
        """
        flag, msg = self.connect()
        if not flag:
            raise RuntimeError(f'连接失败: {msg}')

        return {
            'html': self.response.text,
            'status_code': self.response.status_code,
            'content_type': self.response.headers.get('Content-Type', '')
        }

    def read_page(self, page=1, pagesize=20):
        """
        分页读取数据
        """
        flag, err = self.connect()
        if not flag:
            return False, err

        try:
            result = {
                'html': self.response.text,
                'status_code': self.response.status_code,
                'content_type': self.response.headers.get('Content-Type', ''),
                'url': self.url
            }
            res_data = {
                'records': [result],
                'total': 1,
                'pagination': False  # 禁用分页
            }
            return True, gen_json_response(data=res_data)
        except Exception as e:
            logger.error(f"读取HTTP HTML数据失败: {e}")
            return False, str(e)[:200]

    def read_batch(self):
        """
        生成器分批读取数据
        """
        flag, result = self.read_page()
        yield flag, result
