from etl import get_reader

reader_info = {
    'source': {
        "name": "test",
        "type": "file",
        "conn_conf": {
            "path": "http://116.63.62.251:9010/scidata/%E6%B5%8B%E8%AF%95_20210922175606.xlsx",
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
# load_info = {
#     'source': {
#         "name": "test",
#         "type": "mysql",
#         "conn_conf": {
#             "host": "110.40.157.36",
#             "port": 3306,
#             "username": "root",
#             "password": "Datacenter123",
#             "database_name": "datacenter_database"
#         },
#         "ext_params": {}
#     },
#     'model': {
#         "name": "crypto_info1",
#         "type": "mysql_table",
#         "model_conf": {
#             "name": "crypto_info1",
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
# field_arr = [{'field_name': '平台', 'field_value': 'platform', 'type': 'VARCHAR', 'length': 32, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '币种', 'field_value': 'coin', 'type': 'VARCHAR', 'length': 32, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '时间级别', 'field_value': 'timeframe', 'type': 'VARCHAR', 'length': 10, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '时间', 'field_value': 'time', 'type': 'DATETIME', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '交易对', 'field_value': 'symbol', 'type': 'VARCHAR', 'length': 32, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '币种别名', 'field_value': 'coin_nickname', 'type': 'TEXT', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '开盘价', 'field_value': 'open', 'type': 'FLOAT', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '收盘价', 'field_value': 'close', 'type': 'FLOAT', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '最高价', 'field_value': 'high', 'type': 'FLOAT', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '最低价', 'field_value': 'low', 'type': 'FLOAT', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '交易量', 'field_value': 'volume', 'type': 'FLOAT', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '修改时间', 'field_value': 'update_time', 'type': 'TIMESTAMP', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': '创建时间', 'field_value': 'create_time', 'type': 'TIMESTAMP', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None}, {'field_name': 'test', 'field_value': 'test', 'type': 'VARCHAR', 'length': 50, 'is_primary_key': False, 'nullable': True, 'default': None}]
# # writer.create(field_arr)
# for flag, read_data in reader.read_batch():
#     print(read_data)
#     if read_data['code'] == 200:
#         write_data = read_data['data']['records']
#         writer.write(write_data)