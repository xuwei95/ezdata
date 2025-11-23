'''
使用任务配置字典实时监听mysql binlog数据流，写入目标kafka数据源
'''
from etl.etl_task import etl_task_process
task_params = {
    'extract': {
        'source': {
            "name": "任务数据库",
            "type": "mysql",  # 数据源类型 mysql
            "conn_conf": {  # mysql链接信息
                "host": "127.0.0.1",
                "port": 3306,
                "username": "root",
                "password": "123456",
                "database_name": "ezdata"
            },
            "ext_params": {}
        },
        'model': {
            "name": "任务实例表",
            "type": "mysql_binlog",  # 数据模型类型 mysql表
            "model_conf": {  # 数据模型信息，监听task_instance表的写入，更新，删除操作记录
                "listen_tables": ['task_instance'],
                "only_events": ["write", "update", "delete"]
            },
            "ext_params": {},
            "fields": []
        },
        'extract_info': {
            'extract_type': 'flow',  # 处理类型为流式处理
            'batch_size': 1,
            'extract_rules': []
        }
    },
    'process_rules': [  # 转换流程列表及参数
        {
            "code": "gen_records_list",
            "name": "获取内容列表",
            "rule_dict": {
                "fields": ""
            }
        }
    ],
    'load': {
        'source': {
            "name": "测试kafka写入源",
            "type": "kafka",   # 数据源类型 kafka
            "conn_conf": {   # kafka 连接信息
                "bootstrap_servers": "127.0.0.1:9092",
            },
            "ext_params": {}
        },
        'model': {
            "name": "任务实例topic",
            "type": "kafka_topic",  # 数据模型类型 kafka topic
            "model_conf": {  # 模型信息，topic名task_instance
                "name": "task_instance",
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
