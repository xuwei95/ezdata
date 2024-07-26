import json
from ezetl.data_models import DataModel
from ezetl.utils.common_utils import trans_rule_value, gen_json_response, parse_json
import inspect
import pandas as pd


class CCxtModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)
        model_conf = self._model.get('model_conf', {})
        self.exchange_id = model_conf.get('exchange_id', '')
        self.ext_params = parse_json(self._model.get('ext_params'), {})
        self.method = model_conf.get('method', '')
        self.auth_types = model_conf.get('auth_type', '').split(',')

    def connect(self):
        '''
        连通性测试
        '''
        try:
            import ccxt
            if self.exchange_id != '':
                exchange_class = getattr(ccxt, self.exchange_id)
                self.exchange = exchange_class(self.ext_params)
                self.fetch_function = getattr(self.exchange, self.method)
                sig = inspect.signature(self.fetch_function)
                params = sig.parameters
                default_parmas = {}
                for name, param in params.items():
                    _default = param.default
                    if _default is inspect.Parameter.empty:
                        if name == 'symbol':
                            _default = 'BTC/USDT'
                        else:
                            _default = ""
                    print(name, _default)
                    default_parmas[name] = _default
                self.func_params = default_parmas
            return True, '连接成功'
        except Exception as e:
            return False, str(e)

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

    def get_search_type_list(self):
        '''
        获取可用高级查询类型
        '''
        flag, _ = self.connect()
        if not flag:
            return []
        return [{
            'name': '查询参数',
            'value': 'query_params',
            "default": json.dumps(self.func_params, ensure_ascii=False, indent=2)
        }]

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

    def gen_dataframe(self, res_data):
        '''
        将目标数据转换为dataframe
        '''
        if self.method == 'fetch_ohlcv':
            data_li = []
            for ohlcv in res_data:
                dic = {
                    'exchange': self.exchange_id,
                    'time': ohlcv[0],
                    'symbol': self.func_params['symbol'],
                    'timeframe': self.func_params['timeframe'],
                    'open': ohlcv[1],
                    'high': ohlcv[2],
                    'low': ohlcv[3],
                    'close': ohlcv[4],
                    'volume': ohlcv[5]
                }
                data_li.append(dic)
            df = pd.DataFrame(data_li)
        elif self.method == 'load_markets':
            data_li = []
            for symbol, data in res_data.items():
                data['exchange'] = self.exchange_id
                data_li.append(data)
            df = pd.DataFrame(data_li)
        elif self.method in ['fetch_ticker', 'fetch_order_book', 'fetch_status']:
            res_data['exchange'] = self.exchange_id
            data_li = [res_data]
            df = pd.DataFrame(data_li)
        else:
            df = pd.DataFrame(res_data)
        return df

    def gen_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        # 若查询参数中有函数参数，替换函数参数
        params_rules = [i for i in self.extract_rules if i['field'] == 'search_text' and i['rule'] == 'query_params' and i['value']]
        if params_rules != []:
            self.func_params = parse_json(params_rules[0].get('value'), self.func_params)
        # 若请求参数中有函数参数，替换函数参数
        ext_query_params = [i for i in self.extract_rules if i['field'] in self.func_params and i['value']]
        if ext_query_params != []:
            for i in ext_query_params:
                self.func_params[i['field']] = i['value']
        query_params = {}
        for k in self.func_params:
            query_params[k] = trans_rule_value(self.func_params[k])
        try:
            res_data = self.fetch_function(**query_params)
            self.df = self.gen_dataframe(res_data)
        except Exception as e:
            return False, str(e)
        for i in self.extract_rules:
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
        self.df.fillna("", inplace=True)
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
        flag, res_data = self.connect()
        if not flag:
            return False, res_data
        flag, res_data = self.gen_extract_rules()
        if not flag:
            return False, res_data
        total = len(res_data)
        data_li = res_data[(page-1)*pagesize:page*pagesize]
        res_data = {
            'records': data_li,
            'total': total
        }
        return True, gen_json_response(data=res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :param res_type: 返回形式
        :return:
        '''
        flag, res_data = self.connect()
        if not flag:
            return False, res_data
        flag, res_data = self.gen_extract_rules()
        if not flag:
            yield False, res_data
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