from etl import get_reader, get_writer

reader_info = {
    'source': {
        "name": "test",
        "type": "elasticsearch",
        "conn_conf": {
          "hosts": "127.0.0.1:9200",
          "user": "admin",
          "password": "password"
        },
        "ext_params": {}
    },
    'model': {
        "name": "test",
        "type": "elasticsearch_table",
        "model_conf": {
            "name": "sys_logs",
            "auth_type": "create,insert"
        }
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
