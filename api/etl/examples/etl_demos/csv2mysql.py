'''
使用代码读取csv，清洗数据后写入mysql
'''
from etl.utils import get_reader, get_writer
from etl.utils.common_utils import md5

def trans_volume(volume):
    '''
    转换交易量
    :param volume:
    :return:
    '''
    if str(volume).endswith('K'):
        volume = float(volume[:-1]) * 1000
    if str(volume).endswith('M'):
        volume = float(volume[:-1]) * 1000*1000
    if str(volume).endswith('B'):
        volume = float(str(volume)[:-1].replace(',', '')) * 1000 * 1000 * 1000
    if volume == '-':
        volume = 0
    return round(float(volume), 1)


def trans_date(date):
    '''
    转换日期格式
    :return:
    '''
    year = date.split('年')[0]
    month = date.split('年')[1].split('月')[0]
    day = date.split('年')[1].split('月')[1].split('日')[0]
    return "%d-%02d-%02d 00:00:00" % (int(year), int(month), int(day))


def transform(source):
    dic = {
        'time': trans_date(source['日期']),
        'symbol': f'BTC/USD',
        'timeframe': '1d',
        'low': float(str(source['低']).replace(',', '')),
        'high': float(str(source['高']).replace(',', '')),
        'open': float(str(source['开盘']).replace(',', '')),
        'close': float(str(source['收盘']).replace(',', '')),
        'volume': trans_volume(source['交易量'])
    }
    dic['id'] = md5(f"{dic.get('timeframe')}{dic.get('symbol')}{dic.get('time')}")
    return dic


reader_info = {
    'source': {
        "name": "test",
        "type": "file",
        "conn_conf": {
            "path": "../data/btc_history.csv",
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
        'batch_size': 100,
        'extract_rules': []
    }
}
flag, reader = get_reader(reader_info)
print(flag, reader)
flag, res = reader.connect()
print(flag, res)
print(reader.get_res_fields())
load_info = {
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
        "type": "mysql_table",
        "model_conf": {
            "name": "btc_history",
            "auth_type": "create,insert"
        },
        "ext_params": {},
        "fields": []
    },
    'load_info': {
        'load_type': 'insert',
        'only_fields': []
    }
}
_, writer = get_writer(load_info)
print(writer)
flag, res = writer.connect()
print(flag, res)
if not flag:
    field_arr = [
        {'field_name': '时间级别', 'field_value': 'timeframe', 'type': 'VARCHAR', 'length': 10, 'is_primary_key': False, 'nullable': True, 'default': None},
        {'field_name': '时间', 'field_value': 'time', 'type': 'DATETIME', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None},
        {'field_name': '交易对', 'field_value': 'symbol', 'type': 'VARCHAR', 'length': 32, 'is_primary_key': False, 'nullable': True, 'default': None},
        {'field_name': '开盘价', 'field_value': 'open', 'type': 'FLOAT', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None},
        {'field_name': '收盘价', 'field_value': 'close', 'type': 'FLOAT', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None},
        {'field_name': '最高价', 'field_value': 'high', 'type': 'FLOAT', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None},
        {'field_name': '最低价', 'field_value': 'low', 'type': 'FLOAT', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None},
        {'field_name': '交易量', 'field_value': 'volume', 'type': 'FLOAT', 'length': 0, 'is_primary_key': False, 'nullable': True, 'default': None},
    ]
    flag, res = writer.create(field_arr)
    print(flag, res)
for flag, read_data in reader.read_batch():
    if read_data['code'] == 200:
        write_data = read_data['data']['records']
        print(write_data)
        write_data = [transform(i) for i in write_data]
        flg, res = writer.write(write_data)
        print(flg, res)
