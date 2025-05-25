from etl.utils import get_reader, get_writer

reader_info = {
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
for i in reader.read_batch():
    print(i)

