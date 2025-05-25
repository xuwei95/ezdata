from etl.utils import get_reader, get_writer

reader_info = {
    'source': {
        "name": "test",
        "type": "neo4j",
        "conn_conf": {
            "host": "192.168.220.16",
            "port": 7499,
            "username": "neo4j",
            "password": "123456"
        },
        "ext_params": {}
    },
    'model': {
        "name": "iad_alert",
        "type": "neo4j_graph",
        "model_conf": {
            "name": "iad_alert",
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
print(reader.get_res_fields())
# read_data = reader.read_page()
# print(read_data)
# for i in reader.read_batch():
#     print(i)
load_info = {
    'source': {
        "name": "test",
        "type": "neo4j",
        "conn_conf": {
            "host": "124.220.54.30",
            "port": 7474,
            "username": "neo4j",
            "password": "Datacenter123"
        },
        "ext_params": {}
    },
    'model': {
        "name": "alert",
        "type": "neo4j_graph",
        "model_conf": {
            "name": "alert",
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