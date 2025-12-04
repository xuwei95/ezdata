from etl import get_reader

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
        "type": "mysql_binlog",
        "model_conf": {
            "listen_tables": ['btc_history'],
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
for i in reader.read_batch():
    print(i)
