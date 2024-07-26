'''
使用代码读取mysql，转换后写入elasticsearch
'''
from ezetl.utils import get_reader, get_writer

reader_info = {
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
            "auth_type": "create,insert"
        },
        "ext_params": {},
        "fields": []
    },
    'extract_info': {
        'batch_size': 100,
        'extract_rules': []
    }
}
flag, reader = get_reader(reader_info)
print(flag, reader)
flag, res = reader.connect()
print(flag, res)
print(reader.get_res_fields())
read_data = reader.read_page()
print(read_data)
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
        write_data = [i for i in write_data]
        flg, res = writer.write(write_data)
        print(flg, res)