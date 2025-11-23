'''
使用代码读取csv，清洗数据后写入另一个csv
'''
import pandas as pd
from etl.utils import get_reader
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
data_li = []
for flag, read_data in reader.read_batch():
    print(read_data)
    if read_data['code'] == 200:
        write_data = read_data['data']['records']
        for record in write_data:
            data_li.append(transform(record))
df = pd.DataFrame(data_li)
df.to_csv('btc_history_target.csv', index=False)
