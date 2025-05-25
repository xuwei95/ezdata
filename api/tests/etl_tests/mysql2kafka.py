from etl.utils import get_reader, get_writer

reader_info = {
    'source': {
        "name": "test",
        "type": "mysql",
        "conn_conf": {
            "host": "110.40.157.36",
            "port": 3306,
            "username": "root",
            "password": "Datacenter123",
            "database_name": "datacenter_database"
        },
        "ext_params": {}
    },
    'model': {
        "name": "crypto_info",
        "type": "mysql_table",
        "model_conf": {
            "name": "crypto_info",
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
print(reader.get_res_fields())
read_data = reader.read_page()
print(read_data)
# for i in reader.read_batch():
#     print(i)
# load_info = {
#     'source': {
#         "name": "test",
#         "type": "kafka",
#         "conn_conf": {
#             "bootstrap_servers": "192.168.220.9:9092",
#             "group_id": "3242342"
#         },
#         "ext_params": {}
#     },
#     'model': {
#         "name": "crypto_info1",
#         "type": "kafka_topic",
#         "model_conf": {
#             "name": "test2",
#         },
#         "ext_params": {},
#         "fields": []
#     },
#     'load_info': {
#         'load_type': 'insert',
#         'only_fields': []
#     }
# }
# _, writer = get_writer(load_info)
# print(writer)
# flag, res = writer.connect()
# print(flag, res)
# for flag, read_data in reader.read_batch():
#     print(read_data)
#     if read_data['code'] == 200:
#         write_data = read_data['data']['records']
#         print(write_data)
#         writer.write(write_data)