from abc import ABC, abstractmethod


class DataModel(ABC):
    default_batch_size = 1000

    def __init__(self, model_info):
        self.model_info = model_info
        self._source = model_info.get('source', {})
        self._model = model_info.get('model', {})
        self._extract_info = model_info.get('extract_info', {})
        self.batch_size = self._extract_info.get('batch_size', 1000)
        self.extract_rules = self._extract_info.get('extract_rules', [])
        self._load_info = model_info.get('load_info', {})

    @abstractmethod
    def connect(self):
        '''
        连接测试
        '''
        pass

    def get_info_prompt(self, model_prompt=''):
        return ""

    def gen_models(self):
        '''
        生成子数据模型
        '''
        return []

    def create(self):
        '''
        创建
        '''
        pass

    def check_field(self):
        '''
        检察字段是否存在且一致
        '''
        pass

    def set_field(self):
        '''
        设置字段
        '''
        pass

    def get_res_fields(self):
        '''
        获取字段列表
        :return:
        '''
        pass

    def get_search_type_list(self):
        '''
        获取可用高级查询类型
        '''
        return []

    def get_extract_rules(self):
        '''
        获取可筛选规则选项
        :return:
        '''
        return []

    def parse_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        pass

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :return:
        '''
        pass

    def read_batch(self):
        '''
        分批读取数据
        :return:
        '''
        pass

    def write(self, res_data):
        '''
        写入数据
        :return:
        '''
        pass

    def update(self):
        '''
        更新数据
        :return:
        '''
        pass

    def delete(self):
        '''
        删除数据
        :return:
        '''
        pass

    def delete_batch(self):
        '''
        批量删除数据
        :return:
        '''
        pass
