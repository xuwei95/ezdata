from etl.utils import get_reader, get_writer

reader_info = {
    'source': {
        "name": "test",
        "type": "kafka",
        "conn_conf": {
            "bootstrap_servers": "192.168.220.9:9092",
        },
        "ext_params": {}
    },
    'model': {
        "name": "test",
        "type": "kafka_topic",
        "model_conf": {
            "name": "imonitor_alert",
            "ext_params": {"group_id": "32423"},
        },
        "ext_params": {},
        "fields": []
    },
    'extract_info': {
        'batch_size': 1,
        'extract_rules': {}
    }
}
flag, reader = get_reader(reader_info)
print(flag, reader)
flag, res = reader.connect()
print(flag, res)
flag, res = reader.read_page(1, 20)
print(flag, res)
# for i in reader.read_batch():
#     print(i)