'''
使用代码读取kafka，转换后写入influxdb
'''
from etl.utils import get_reader, get_writer
from etl.utils.common_utils import format_date

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
load_info = {
    'source': {
        "name": "test",
        "type": "influxdb",
        "conn_conf": {
            "host": "127.0.0.1",
            "port": 8086,
            "database": "datacenter",
            "username": "admin",
            "password": "123456"
        },
        "ext_params": {}
    },
    'model': {
        "name": "test",
        "type": "influxdb_table",
        "model_conf": {
            "name": "btc_history",
        },
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
print(writer.get_res_fields())


def transform(dic):
    '''
    转换数据
    :param dic:
    :return:
    '''
    res_dic = {
        'measurement': 'btc_history',
        'tags': {'timeframe': dic['timeframe'], "symbol": dic['symbol']},
        'fields': {
            'open': float(dic['open']),
            'close': float(dic['close']),
            'high': float(dic['high']),
            'low': float(dic['low']),
            'volume': float(dic['volume'])
        },
        'time': format_date(dic['time'], res_type='timestamp') * 1000000000
    }
    return res_dic

for flag, read_data in reader.read_batch():
    if read_data['code'] == 200:
        write_data = read_data['data']['records']
        write_data = [transform(i) for i in write_data]
        flg, res = writer.write(write_data)
        print(flg, res)