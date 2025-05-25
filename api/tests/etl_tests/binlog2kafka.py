from etl.utils import get_reader, get_writer

reader_info = {
    'source': {
        "name": "test",
        "type": "mysql",
        "conn_conf": {
            "host": "110.40.157.36",
            "port": 3306,
            "username": "root",
            "password": "naivedata123",
            "database_name": "naivedata"
        },
        "ext_params": {}
    },
    'model': {
        "name": "test",
        "type": "mysql_binlog",
        "model_conf": {
            "listen_tables": ['task', 'task_instance', 'sys_dict', 'sys_dict_item'],
            "only_events": ["write", "update", "delete"]
        },
        "ext_params": {},
        "fields": []
    },
    'extract_info': {
        'batch_size': 1000,
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
        "type": "kafka",
        "conn_conf": {
            "bootstrap_servers": "124.220.54.30:9092",
        },
        "ext_params": {}
    },
    'model': {
        "name": "test",
        "type": "kafka_topic",
        "model_conf": {
            "name": "test",
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
for flag, read_data in reader.read_batch():
    print(read_data)
    if read_data['code'] == 200:
        write_data = read_data['data']['records']
        print(write_data)
        writer.write(write_data)
