from etl import get_reader, get_writer

reader_info = {
    'source': {
        "name": "test",
        "type": "mysql",
        "conn_conf": {
          "user": "root",
          "password": "ezdata123",
          "database": "ezdata",
          "host": "127.0.0.1",
          "port": 3306
        },
        "ext_params": {}
    },
    'model': {
        "name": "sys_dict",
        "type": "mysql_table",
        "model_conf": {
            "name": "sys_dict",
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
for i in reader.read_batch():
    print(i)
