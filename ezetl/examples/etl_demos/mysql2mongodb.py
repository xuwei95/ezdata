'''
使用代码读取mysql，转换后写入mingodb
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
        "type": "mongodb",
        "conn_conf": {
            "database_name": "datacenter",
            "host": "127.0.0.1",
            "port": "27017",
            "username": "root",
            "password": "123456",
        },
        "ext_params": {}
    },
    'model': {
        "name": "test",
        "type": "mongodb_collection",
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
_, writer = get_writer(load_info)
print(writer)
flag, res = writer.connect()
print(flag, res)


def transform(dic):
    dic['_id'] = dic['id'][:24]
    dic.pop('id')
    return dic


for flag, read_data in reader.read_batch():
    print(read_data)
    if read_data['code'] == 200:
        write_data = read_data['data']['records']
        write_data = [transform(i) for i in write_data]
        flg, res = writer.write(write_data)
        print(flg, res)
