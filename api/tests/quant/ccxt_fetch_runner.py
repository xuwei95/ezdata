'''
ccxt抓取历史数据
'''
import ccxt
from utils.common_utils import timestamp_to_date, md5, trans_rule_value, format_date
from etl.utils import get_writer
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


def run(params, logger):
    '''
    任务执行函数
    :param params: 任务参数
    :param logger: 日志logger
    :return:
    '''
    logger.info(str(params))
    exchange_id = params.get('platform')
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({
        'timeout': 30000,
        'enableRateLimit': True,
        'proxies': {
            'https': "http://127.0.0.1:7890",
            'http': "http://127.0.0.1:7890"
        }
    })
    writer_info = {
        'model_id': params.get('model_id'),
        'load_info': {
            'load_type': 'upsert',
            'only_fields': ['_id']
        }
    }
    flag, writer = get_writer(writer_info)
    if not flag:
        raise ValueError(str(writer))
    start_time = trans_rule_value(params.get('start_time'))
    start_time = format_date(start_time, res_type='timestamp')
    end_time = trans_rule_value(params.get('end_time'))
    end_time = format_date(end_time, res_type='timestamp')
    timeframe = params.get('timeframe')
    symbol_second = symbol_dict[timeframe]
    fetch_seconds = end_time - start_time
    fetch_pages = fetch_seconds // (symbol_second * pagesize) + 1
    symbol = params.get('symbol')
    coin = symbol.split('/')[0]
    data_li = []
    for page in range(fetch_pages):
        logger.info(f"{timestamp_to_date(start_time)}---{page}/{fetch_pages}")
        since = start_time * 1000
        res_li = exchange.fetchOHLCV(symbol=symbol, timeframe=timeframe, since=since)
        for ohlcv in res_li:
            dic = {
                'platform': exchange_id,
                'time': ohlcv[0],
                'coin': coin,
                'symbol': symbol,
                'coin_nickname': f'{coin},{coin.lower()}',
                'timeframe': timeframe,
                'open': ohlcv[1],
                'high': ohlcv[2],
                'low': ohlcv[3],
                'close': ohlcv[4],
                'volume': ohlcv[5]
            }
            dic['_id'] = md5(f"{exchange_id}{symbol}{timeframe}{dic['time']}")
            data_li.append(dic)
        start_time += pagesize * symbol_second
    logger.info(data_li[-1])
    logger.info(len(data_li))
    writer.write(data_li)


if __name__ == '__main__':
    from utils.logger.logger import get_logger
    logger = get_logger('ccxt', 'ccxt')
    params = {
        'platform': 'okx',
        'timeframe': '1m',
        'symbol': 'BTC/USDT',
        'start_time': 'time:-600s',
        'end_time': 'time:0s',
        'model_id': 'ae017d42afc145abb4380833d84518ec'
    }
    run(params, logger)
