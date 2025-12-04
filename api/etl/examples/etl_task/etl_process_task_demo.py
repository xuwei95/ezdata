'''
使用任务配置字典分批读取mysql，内置算法聚合统计数据，写入目标kafka数据源
'''
from etl.etl_task import etl_task_process

task_params = {
    'extract': {
        'source': {
            "name": "test",
            "type": "mysql",
            "conn_conf": {
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
            "type": "mysql_table",
            "model_conf": {
                "name": "btc_history",
            },
            "ext_params": {},
            "fields": []
        },
        'extract_info': {
            'batch_size': 1000,
            'extract_rules': []
        }
    },
    'process_rules': [
        {
            "code": "gen_records_list",
            "name": "获取内容列表",
            "rule_dict": {
                "fields": "time,symbol,close"
            }
        },
        {
            "code": "trans_time_format",
            "name": "转换时间格式",
            "rule_dict": {
                "fields": "time",
                "format": "%Y-%m"
            }
        },
        {
            "code": "trans_field_type",
            "name": "转换字段类型",
            "rule_dict": {
                "fields": "close",
                "trans_type": "float"
            }
        },
        {
            "code": "group_agg_count",
            "name": "分组聚合统计",
            "rule_dict": {
                "count_field": "close",
                "group_fields": "time",
                "count_type": "mean"
            }
        },
        {
            "code": "df_to_data",
            "name": "dataframe转回原始数据",
            "rule_dict": {
            }
        }
    ],
    'load': {
        'source': {
            "name": "test",
            "type": "kafka",
            "conn_conf": {
                "bootstrap_servers": "127.0.0.1:9092",
            },
            "ext_params": {}
        },
        'model': {
            "name": "test",
            "type": "kafka_topic",
            "model_conf": {
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
