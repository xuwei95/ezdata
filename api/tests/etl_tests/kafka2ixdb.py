from etl.utils import get_reader, get_writer

reader_info = {
    'source': {
        "name": "test",
        "type": "kafka",
        "conn_conf": {
            "bootstrap_servers": "192.168.220.9:9092",
        },
        "ext_params": {}
    },
    'model': {
        "name": "test2",
        "type": "kafka_topic",
        "model_conf": {
            "name": "test2",
            "group_id": "3242342"
        },
        "ext_params": {},
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
# for i in reader.read_batch():
#     print(i)
load_info = {
    'source': {
        "name": "test",
        "type": "influxdb",
        "conn_conf": {
            "host": "124.220.54.30",
            "port": 8086,
            "database": "datacenter",
            "username": "admin",
            "password": "Datacenter123"
        },
        "ext_params": {}
    },
    'model': {
        "name": "test",
        "type": "influxdb_table",
        "model_conf": {
            "name": "test",
        },
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
print(writer.get_res_fields())
for flag, read_data in reader.read_batch():
    print(read_data)
    # if read_data['code'] == 200:
    #     write_data = read_data['data']['records']
    #     writer.write(write_data)