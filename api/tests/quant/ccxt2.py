'''
ccxt抓取历史数据
'''
import ccxt
from utils.common_utils import date_to_timestamp, timestamp_to_date, md5
from etl.utils import get_writer
from utils.logger.logger import get_logger
logger = get_logger('ccxt', 'ccxt')
exchange_id = 'okx'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'hostname': 'okx.com',
    'timeout': 30000,
    'enableRateLimit': True,
    # 'proxies': {
    #     'https': "http://127.0.0.1:7890",
    #     'http': "http://127.0.0.1:7890"
    # }
})
symbol_dict = {
    '1M': 86400*30,
    '1w': 86400*7,
    '1d': 86400,
    '4h': 3600*4,
    '1h': 3600,
    '15m': 900,
    '5m': 300,
    '1m': 60
}
pagesize = 100


def fetch_coin_history(symbol, start_time, end_time, timeframe):
    '''
    获取行情历史数据
    '''
    symbol_second = symbol_dict[timeframe]
    start_time = date_to_timestamp(start_time)
    end_time = date_to_timestamp(end_time)
    fetch_seconds = end_time - start_time
    fetch_pages = fetch_seconds // (symbol_second * pagesize) + 1
    coin = symbol.split('/')[0]
    data_li = []
    for page in range(fetch_pages):
        logger.info(f"{timestamp_to_date(start_time)}---{page}/{fetch_pages}")
        since = start_time * 1000
        res_li = exchange.fetchOHLCV(symbol=symbol, timeframe=timeframe, since=since)
        for ohlcv in res_li:
            dic = {
                'platform': exchange_id,
                'time': timestamp_to_date(ohlcv[0] / 1000),
                'coin': coin,
                'symbol': symbol,
                'coin_nickname': f'{coin},{coin.lower()}',
                'timeframe': timeframe,
                'open':  ohlcv[1],
                'high': ohlcv[2],
                'low': ohlcv[3],
                'close': ohlcv[4],
                'volume': ohlcv[5]
            }
            dic['_id'] = md5(f"{exchange_id}{symbol}{timeframe}{dic['time']}")
            data_li.append(dic)
        start_time += pagesize * symbol_second
    return data_li


start_time = '2023-01-01'
end_time = '2023-05-20'
symbol_list = ['LTC/USDT']
writer_info = {
        'model_id': 'ae017d42afc145abb4380833d84518ec',
        'load_info': {
            'load_type': 'upsert',
            'only_fields': ['_id']
        }
    }
flag, writer = get_writer(writer_info)
logger.info(writer)
for symbol in symbol_list:
    timeframe = '4h'
    writer_info = {
        'model_id': 'ae017d42afc145abb4380833d84518ec',
        'load_info': {
            'load_type': 'upsert',
            'only_fields': ['_id']
        }
    }
    data_li = fetch_coin_history(symbol, start_time, end_time, timeframe)
    logger.info(data_li[-1])
    logger.info(len(data_li))
    writer.write(data_li)