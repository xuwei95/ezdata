from etl.utils import get_reader

reader_info = {
    'source': {
        "type": "file",
        "conn_conf": {
            "path":  "../data/btc_history.csv",
        },
    },
    'model': {
        "name": "test",
        "type": "file_table",
        "model_conf": {},
        "fields": []
    },
    'extract_info': {
        'batch_size': 10,
        'extract_rules': {'equal[]': 'setosa'}
    }
}

flag, reader = get_reader(reader_info)
print(flag, reader)
flag, res = reader.connect()
print(flag, res)
print(reader.get_res_fields())
flag, read_data = reader.read_page()
print(flag, read_data)
for flag, i in reader.read_batch():
    print(flag, i)
