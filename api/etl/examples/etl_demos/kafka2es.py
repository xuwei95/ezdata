'''
使用代码读取kafka，写入elasticsearch
'''
from etl import get_reader, get_writer

reader_info = {
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
        "ext_params": {
            "group_id": "111"
        },
        "fields": []
    },
    'extract_info': {
        'batch_size': 1,
        'extract_rules': []
    }
}
flag, reader = get_reader(reader_info)
print(flag, reader)
flag, res = reader.connect()
print(flag, res)
load_info = {
    'source': {
        "name": "test",
        "type": "elasticsearch",
        "conn_conf": {
            "url": "127.0.0.1:9200",
            "auth_type": 2,
            "username": "elastic",
            "password": "elastic"
        },
        "ext_params": {}
    },
    'model': {
        "name": "btc_history",
        "type": "elasticsearch_index",
        "model_conf": {
            "name": "btc_history",
            "auth_type": "create,insert"
        }
    },
    'load_info': {
        'load_type': 'insert',
        'only_fields': []
    }
}
_, writer = get_writer(load_info)
print(writer)
flag, res = writer.connect()
print(flag, res)
if not flag:
    # 不存在，新建
    field_arr = [
        {'field_name': 'close', 'field_value': 'close', 'type': 'float'},
        {'field_name': 'high', 'field_value': 'high', 'type': 'float'},
        {'field_name': 'id', 'field_value': 'id', 'type': 'keyword'},
        {'field_name': 'low', 'field_value': 'low', 'type': 'float'},
        {'field_name': 'open', 'field_value': 'open', 'type': 'float'},
        {'field_name': 'symbol', 'field_value': 'symbol', 'type': 'text'},
        {'field_name': 'time', 'field_value': 'time', 'type': 'text'},
        {'field_name': 'timeframe', 'field_value': 'timeframe', 'type': 'keyword'},
        {'field_name': 'volume', 'field_value': 'volume', 'type': 'float'}
    ]
    flg, res = writer.create(field_arr)
    print(flg, res)
print(writer.get_res_fields())
for flag, read_data in reader.read_batch():
    print(read_data)
    if read_data['code'] == 200:
        write_data = read_data['data']['records']
        # write_data = [i['data'] for i in write_data]
        flg, res = writer.write(write_data)
        print(flg, res)