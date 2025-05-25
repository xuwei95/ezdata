from etl.utils import get_reader, get_writer

reader_info = {
    'source': {
        "name": "test",
        "type": "mysql",
        "conn_conf": {
            "host": "127.0.0.1",
            "port": 3306,
            "username": "root",
            "password": "ezdata123",
            "database_name": "ezdata"
        },
        "ext_params": {}
    },
    'model': {
        "name": "test",
        "type": "mysql_binlog",
        "model_conf": {
            "listen_tables": ['alert'],
            "only_events": ["write", "update", "delete"]
        },
        "ext_params": {},
        "fields": []
    },
    'extract_info': {
        'batch_size': 1,
        'extract_rules': {"read_type[search_text]": 'latest'}
    }
}
flag, reader = get_reader(reader_info)
print(flag, reader)
flag, res = reader.connect()
print(flag, res)
flag, res = reader.read_page()
print(flag, res)
for flag, res in reader.read_batch():
    print(flag, res)
