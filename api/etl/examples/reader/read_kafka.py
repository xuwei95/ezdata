from etl.utils import get_reader

reader_info = {
    'source': {
        "name": "test",
        "type": "kafka",
        "conn_conf": {
            "bootstrap_servers": "127.0.0.1:9092",
        },
        "ext_params": {}
    },
    'model': {
        "name": "test",
        "type": "kafka_topic",
        "model_conf": {
            "name": "btc_history",
        },
        "ext_params": {
            "group_id": "111"
        },
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
for i in reader.read_batch():
    print(i)