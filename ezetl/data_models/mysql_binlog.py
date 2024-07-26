import random
from ezetl.data_models import DataModel
from ezetl.utils.common_utils import gen_json_response
from pymysqlreplication import BinLogStreamReader
from pymysqlreplication.row_event import (
    DeleteRowsEvent,
    UpdateRowsEvent,
    WriteRowsEvent
)


class MysqlBinlogModel(DataModel):
    '''
    mysql binlog
    '''

    def __init__(self, model_info):
        super().__init__(model_info)
        conn_conf = self._source['conn_conf']
        self.conn_setting = {
            'host': conn_conf['host'],
            'port': conn_conf['port'],
            'user': conn_conf['username'],
            'passwd': conn_conf['password']
        }
        # 监听数据库
        database = conn_conf.get('database_name')
        self.listen_dbs = [database]
        model_conf = self._model['model_conf']
        # 监听数据表
        listen_tables = model_conf.get('listen_tables', '')
        if isinstance(listen_tables, str) and listen_tables != '':
            self.listen_tables = listen_tables.split(',')
        else:
            self.listen_tables = None
        only_events = model_conf.get('only_events', '')
        if isinstance(only_events, str) and only_events != '':
            only_events = only_events.split(',')
        self.only_events = []
        for event in only_events:
            if event == 'delete':
                self.only_events.append(DeleteRowsEvent)
            if event == 'write':
                self.only_events.append(WriteRowsEvent)
            if event == 'update':
                self.only_events.append(UpdateRowsEvent)
        self.read_type = 'latest'  # 默认从最新开始读

    def connect(self):
        '''
        连通性测试
        '''
        try:
            stream = BinLogStreamReader(
                connection_settings=self.conn_setting,
                server_id=random.randint(10000, 99999),  # slave标识，唯一
                freeze_schema=True,
                resume_stream=True,  # 从最新事件开始监听
                blocking=False,  # 阻塞等待后续事件
                only_schemas=self.listen_dbs,  # 要监听的数据库
                only_tables=self.listen_tables,  # 要监听的表
                # 设定只监控写操作：增、删、改
                only_events=self.only_events
            )
            for binlogevent in stream:
                print(binlogevent)
            return True, '连接成功'
        except Exception as e:
            return False, str(e)

    def get_res_fields(self):
        '''
        获取字段列表
        '''
        return None

    def get_search_type_list(self):
        '''
        获取可用高级查询类型
        '''
        return [{
            'name': '读取方式',
            'value': 'read_type',
            "default": f"latest"
        }]

    def get_extract_rules(self):
        '''
        获取可筛选项
        :return:
        '''
        rules = []
        return rules

    def gen_extract_rules(self):
        '''
        解析筛选规则
        :return:
        '''
        rules = [i for i in self.extract_rules if i['rule'] == 'read_type']
        if rules != []:
            i = rules[0]
            if i['value'] == 'earliest':
                self.read_type = 'earliest'
            else:
                self.read_type = 'latest'

    def read_page(self, page=1, pagesize=20):
        '''
        分页读取数据
        :return:
        '''
        stream = BinLogStreamReader(
            connection_settings=self.conn_setting,
            server_id=random.randint(10000, 99999),  # slave标识，唯一
            freeze_schema=True,
            resume_stream=False,  # 预览和分页查询模式，从最开始获取一条数据就返回
            blocking=True,  # 阻塞等待后续事件
            only_schemas=self.listen_dbs,  # 要监听的数据库
            only_tables=self.listen_tables,  # 要监听的表
            # 设定只监控写操作：增、删、改
            only_events=self.only_events
        )
        for binlogevent in stream:
            for row in binlogevent.rows:
                event = {"schema": binlogevent.schema, "table": binlogevent.table}
                if isinstance(binlogevent, DeleteRowsEvent):
                    event["action"] = "delete"
                    event["data"] = row["values"]
                elif isinstance(binlogevent, UpdateRowsEvent):
                    event["action"] = "update"
                    event["data"] = row["after_values"]
                elif isinstance(binlogevent, WriteRowsEvent):
                    event["action"] = "insert"
                    event["data"] = row["values"]
                res_data = {
                    'records': [event],
                    'total': 1
                }
                return True, gen_json_response(data=res_data)

    def read_batch(self):
        '''
        生成器分批读取数据
        :return:
        '''
        self.gen_extract_rules()
        stream = BinLogStreamReader(
            connection_settings=self.conn_setting,
            server_id=random.randint(10000, 99999),  # slave标识，唯一
            freeze_schema=True,
            resume_stream=self.read_type == 'latest',  # 判断是从头开始还是只接受最新数据
            blocking=True,  # 阻塞等待后续事件
            only_schemas=self.listen_dbs,  # 要监听的数据库
            only_tables=self.listen_tables,  # 要监听的表
            # 设定只监控写操作：增、删、改
            only_events=self.only_events
        )
        for binlogevent in stream:
            for row in binlogevent.rows:
                event = {"schema": binlogevent.schema, "table": binlogevent.table}
                if isinstance(binlogevent, DeleteRowsEvent):
                    event["action"] = "delete"
                    event["data"] = row["values"]
                elif isinstance(binlogevent, UpdateRowsEvent):
                    event["action"] = "update"
                    event["data"] = row["after_values"]
                elif isinstance(binlogevent, WriteRowsEvent):
                    event["action"] = "insert"
                    event["data"] = row["values"]
                res_data = {
                    'records': [event],
                    'total': 1
                }
                yield True, gen_json_response(data=res_data)
