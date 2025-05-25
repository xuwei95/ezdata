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

        },
        "ext_params": {},
        "fields": []
    },
    'extract_info': {
        'batch_size': 1000,
        'extract_rules': []
    }
}
# flag, reader = get_reader(reader_info)
# print(flag, reader)
# flag, res = reader.connect()
# print(flag, res)
# print(reader.get_res_fields())
# read_data = reader.read_page()
# print(read_data)
# for i in reader.read_batch():
#     print(i)
# load_info = {
#     'source': {
#         "name": "test",
#         "type": "elasticsearch",
#         "conn_conf": {
#             "url": "124.220.54.30:9200",
#             "auth_type": 2,
#             "username": "elastic",
#             "password": "Datacenter123"
#         },
#         "ext_params": {}
#     },
#     'model': {
#         "name": "crypto_info1",
#         "type": "elasticsearch_index"
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
# print(writer.get_res_fields())
field_arr = [
    {'field_name': 'close', 'field_value': 'close', 'type': 'float', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'coin', 'field_value': 'coin', 'type': 'text', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'coin_nickname', 'field_value': 'coin_nickname', 'type': 'text', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'create_time', 'field_value': 'create_time', 'type': 'date', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'high', 'field_value': 'high', 'type': 'float', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'id', 'field_value': 'id', 'type': 'long', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'low', 'field_value': 'low', 'type': 'float', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'open', 'field_value': 'open', 'type': 'float', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'platform', 'field_value': 'platform', 'type': 'text', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'symbol', 'field_value': 'symbol', 'type': 'text', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'time', 'field_value': 'time', 'type': 'date', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'timeframe', 'field_value': 'timeframe', 'type': 'text', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'update_time', 'field_value': 'update_time', 'type': 'date', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''},
    {'field_name': 'volume', 'field_value': 'volume', 'type': 'float', 'length': 0, 'is_primary_key': 0, 'nullable': 1, 'default': ''}
]
# writer.create(field_arr)
# for flag, read_data in reader.read_batch():
#     print(read_data)
#     if read_data['code'] == 200:
#         write_data = read_data['data']['records']
#         writer.write(write_data)