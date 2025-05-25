'''
ccxt抓取历史数据
'''
import ccxt
from utils.common_utils import date_to_timestamp, timestamp_to_date

exchange_id = 'okx'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'hostname': 'okx.com',
    'timeout': 30000,
    'enableRateLimit': True,
    'proxies': {
        'https': "http://127.0.0.1:7890",
        'http': "http://127.0.0.1:7890"
    }
})


def fetch_coin_history(symbol, start_time, end_time, timeframe):
    '''
    获取行情历史数据
    '''
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
    symbol_second = symbol_dict[timeframe]
    start_time = date_to_timestamp(start_time)
    end_time = date_to_timestamp(end_time)
    fetch_seconds = end_time - start_time
    fetch_pages = fetch_seconds // (symbol_second * pagesize) + 1
    coin = symbol.split('/')[0]
    print(fetch_pages)
    for page in range(fetch_pages):
        print(timestamp_to_date(start_time))
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
            print(dic)
        print(len(res_li))
        start_time += pagesize * symbol_second


start_time = '2019-01-01'
end_time = '2021-11-20'
symbol = 'LTC/USDT'
timeframe = '1d'
fetch_coin_history(symbol, start_time, end_time, timeframe)