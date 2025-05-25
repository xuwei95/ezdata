from etl.utils import get_reader

reader_info = {
    'source': {
        "name": "test",
        "type": "file",
        "conn_conf": {
            "path": "http://127.0.0.1:8002/static/btc_history.csv",
        },
        "ext_params": {}
    },
    'model': {
        "name": "test",
        "type": "file_table",
        "model_conf": {},
        "ext_params": {},
        "fields": []
    },
    'extract_info': {
        'batch_size': 1000,
        # 'extract_rules': {'use_cache[cache_size]': 1000}
    }
}

flag, reader = get_reader(reader_info)
print(flag, reader)
flag, res = reader.connect()
print(flag, res)
print(reader.get_res_fields())
read_data = reader.read_page()
print(read_data)
# for i in reader.read_batch():
#     print(i)