from etl.utils import get_reader, get_writer

reader_info = {
    'source': {
        "name": "test",
        "type": "elasticsearch",
        "conn_conf": {
            "url": "110.40.157.36:9200",
            "auth_type": 2,
            "username": "elastic",
            "password": "naivedata123"
        },
        "ext_params": {}
    },
    'model': {
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
read_data = reader.read_page()
print(read_data)
for i in reader.read_batch():
    print(i)
