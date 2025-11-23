'''
使用任务配置字典分批读取mysql，内置函数转换数据，写入目标kafka数据源
'''
from etl.etl_task import etl_task_process

task_params = {
    'extract': {
        'source': {
            "name": "test",
            "type": "mysql",  # 数据源类型 mysql
            "conn_conf": {  # mysql链接信息
                "host": "127.0.0.1",
                "port": 3306,
                "username": "root",
                "password": "123456",
                "database_name": "test"
            },
            "ext_params": {}
        },
        'model': {
            "name": "btc_history",
            "type": "mysql_table",  # 数据模型类型 mysql表
            "model_conf": {  # 数据模型信息，表名btc_history
                "name": "btc_history",
            },
            "ext_params": {},
            "fields": []
        },
        'extract_info': {
            'batch_size': 100,  # 每批读取数量
            # 查询过滤条件 close >= 20000 and high < 40000
            # 可简化为字典形式 'extract_rules': {"get[close]": 30000, "lt[high]": 40000}
            'extract_rules': [
                {'field': "close", "rule": "gte", "value": 20000},
                {'field': "high", "rule": "lt", "value": 40000}
            ]
        }
    },
    'process_rules': [  # 转换流程列表及参数
        {
            "code": "gen_records_list",
            "name": "获取内容列表",
            "rule_dict": {
                "fields": "time,symbol,close,high"
            }
        }
    ],
    'load': {
        'source': {
            "name": "test",
            "type": "kafka",  # 数据源类型 kafka
            "conn_conf": {  # kafka 连接信息
                "bootstrap_servers": "127.0.0.1:9092",
            },
            "ext_params": {}
        },
        'model': {
            "name": "test",
            "type": "kafka_topic",  # 数据模型类型 kafka topic
            "model_conf": {  # 模型信息，topic名btc_history
                "name": "btc_history",
            },
            "ext_params": {},
            "fields": []
        },
        'load_info': {
            'load_type': 'insert',
            'only_fields': []
        }
    }
}
etl_task_process(task_params, run_load=True)
