import json

from etl.data_models import DataModel
from etl.utils.common_utils import trans_rule_value, gen_json_response, parse_json, md5
import pandas as pd
from minio import Minio
import os
import io


class BaseMinioModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        conn_conf = self._source.get('conn_conf', {})
        url = conn_conf.get('url')
        access_key = conn_conf.get('username')
        secret_key = conn_conf.get('password')
        self.bucket = conn_conf.get('bucket')
        self._client = Minio(endpoint=url,
                             access_key=access_key,
                             secret_key=secret_key,
                             secure=False)
        self.df = None

    def connect(self):
        '''
        连通性测试
        '''
        try:
            buckets = self._client.list_buckets()
            if self.bucket in buckets:
                return True, '连接成功'
            else:
                return False, '连接失败'
        except Exception as e:
            return False, str(e)

    def get_info_prompt(self, model_prompt=''):
        '''
        获取使用提示及元数据信息
        '''
        self.connect()
        info_prompt = f"""
一个对象存储读取封装类
# 使用示例：
实例化此类的reader对象，读取转为dataframe：
df = reader.df

# MetaData:
<dataframe>
{self.df.shape[0]}x{self.df.shape[1]}\n{self.df.head(3).to_csv()}
</dataframe>
"""
        return info_prompt


class TableMinioModel(BaseMinioModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        model_conf = self._model['model_conf']
        self.file_name = model_conf.get('name')

    def connect(self):
        '''
        连通性测试
        '''
        flag, res = self.read_page(pagesize=1)
        if flag:
            return True, '连接成功'
        else:
            return False, '连接失败'

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        flag, res_data = self.gen_extract_rules()
        if not flag:
            assert ValueError(res_data)
        res_fields = []
        try:
            for column in self.df.columns:
                dic = {
                    'field_name': column,
                    'field_value': column,
                }
                res_fields.append(dic)
        except Exception as e:
            print(e)
        return res_fields

    def get_df(self, nrows=None):
        '''
        获取pandas df
        '''
        df = None
        try:
            file_obj = self._client.get_object(self.bucket, self.file_name)
            if self.file_name.endswith('.csv'):
                df = pd.read_csv(file_obj, dtype=object, nrows=nrows)
            else:
                df = pd.read_excel(file_obj, dtype=object, nrows=nrows)
            df.fillna("", inplace=True)
        except Exception as e:
            print(e)
        return df

    def get_search_type_list(self):
        '''
        获取可用高级查询类型
        '''
        return []

    def get_extract_rules(self):
        '''
        获取可筛选项
        :return:
        '''
        rules = [{
            'name': '等于',
            'value': 'equal'
          }, {
            'name': '不等于',
            'value': 'f_equal'
          }, {
            'name': '大于',
            'value': 'gt'
          }, {
            'name': '大于等于',
            'value': 'gte'
          }, {
            'name': '小于',
            'value': 'lt'
          }, {
            'name': '小于等于',
            'value': 'lte'
          }
        ]
        return rules

    def gen_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        self.df = self.get_df()
        if self.df is None:
            return False, '文件读取错误'
        for i in self.extract_rules:
            print(i)
            field = i.get('field')
            rule = i.get('rule')
            value = i.get('value')
            value = trans_rule_value(value)
            if field and value:
                if rule in ['equal', 'eq']:
                    self.df = self.df[self.df[field] == value]
                elif rule in ['f_equal', 'neq']:
                    self.df = self.df[self.df[field] != value]
                elif rule == 'gt':
                    self.df = self.df[self.df[field] > value]
                elif rule == 'gte':
                    self.df = self.df[self.df[field] >= value]
                elif rule == 'lt':
                    self.df = self.df[self.df[field] < value]
                elif rule == 'lte':
                    self.df = self.df[self.df[field] <= value]
        data_li = []
        for k, row in self.df.iterrows():
            data_li.append(row.to_dict())
        return True, data_li

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :param page:
        :param pagesize:
        :return:
        '''
        flag, res_data = self.gen_extract_rules()
        if not flag:
            return False, res_data
        total = len(res_data)
        data_li = res_data
        res_data = {
            'records': data_li,
            'total': total,
            'pagination': False  # 禁用分页
        }
        return True, gen_json_response(data=res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :param res_type: 返回形式
        :return:
        '''
        flag, res_data = self.gen_extract_rules()
        if not flag:
            return False, res_data
        total = len(res_data)
        pagesize = self._extract_info.get('batch_size', 1000)
        total_pages = total // pagesize + 1
        n = 0
        while n < total_pages:
            page = n + 1
            n += 1
            result = {
                'records': res_data[(page-1)*pagesize:page*pagesize],
                'total': total
            }
            yield True, gen_json_response(result)

    def write(self, res_data):
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'
        records = []
        if isinstance(res_data, list) and res_data != []:
            records = res_data
        if isinstance(res_data, dict):
            if 'records' in res_data and res_data['records'] != []:
                records = res_data['records']
            else:
                records = [res_data]
        try:
            df = pd.DataFrame(records)
            f = io.BytesIO()
            if self.file_name.endswith('.csv'):
                df.to_csv(f, index=False)
            else:
                df.to_excel(f, index=False)
            content_value = f.getvalue()
            self._client.put_object(self.bucket, self.file_name, content_value)
        except Exception as e:
            return False, f'{str(e)[:100]}'
        return True, res_data


class JsonMinioModel(TableMinioModel):

    def __init__(self, model_info):
        super().__init__(model_info)

    def get_df(self, nrows=None):
        '''
        获取pandas df
        '''
        df = None
        try:
            file_obj = self._client.get_object(self.bucket, self.file_name)
            json_str = file_obj.read().decode()
            json_obj = parse_json(json_str, [])
            if isinstance(json_obj, dict):
                json_obj = [json_obj]
            df = pd.DataFrame(json_obj)
            df.fillna("", inplace=True)
        except Exception as e:
            print(e)
        return df

    def write(self, res_data):
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'
        records = []
        if isinstance(res_data, list) and res_data != []:
            records = res_data
        if isinstance(res_data, dict):
            if 'records' in res_data and res_data['records'] != []:
                records = res_data['records']
            else:
                records = [res_data]
        try:
            content_value = json.dumps(records, ensure_ascii=False).encode()
            self._client.put_object(self.bucket, self.file_name, content_value)
        except Exception as e:
            return False, f'{str(e)[:100]}'
        return True, res_data


class H5MinioModel(TableMinioModel):

    def __init__(self, model_info):
        super().__init__(model_info)

    def get_df(self, nrows=None):
        '''
        获取pandas df
        '''
        df = None
        try:
            file_obj = self._client.get_object(self.bucket, self.file_name)
            if not os.path.exists('tmp'):
                os.mkdir('tmp')
            cache_file_path = os.path.join('tmp', f"{md5(self.bucket + self.file_name)}")
            if not os.path.exists(cache_file_path):
                content_value = file_obj.read()
                cache_file = open(cache_file_path, 'wb')
                cache_file.write(content_value)
                cache_file.close()
            df = pd.read_hdf(cache_file_path)
            df.fillna("", inplace=True)
        except Exception as e:
            print(e)
        return df

    def write(self, res_data):
        self.load_type = self._load_info.get('load_type', '')
        if self.load_type not in ['insert']:
            return False, f'写入类型参数错误,不支持类型{self.load_type}'
        records = []
        if isinstance(res_data, list) and res_data != []:
            records = res_data
        if isinstance(res_data, dict):
            if 'records' in res_data and res_data['records'] != []:
                records = res_data['records']
            else:
                records = [res_data]
        try:
            df = pd.DataFrame(records)
            f = io.BytesIO()
            df.to_hdf(f)
            content_value = f.getvalue()
            self._client.put_object(self.bucket, self.file_name, content_value)
        except Exception as e:
            return False, f'{str(e)[:100]}'
        return True, res_data


