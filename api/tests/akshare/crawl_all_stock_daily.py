import akshare as ak
from utils.etl_utils import get_writer_model
from utils.common_utils import md5, get_now_time, format_date
from utils.logger.logger import get_logger
logger = get_logger('stock_crawler', 'stock_crawler')


field_map = {
    "代码": "symbol",
    "名称": "name",
    "最高": "high",
    "最低": "low",
    "今开": "open",
    "最新价": "close",
    "成交量": "volume",
    "成交额": "amount",
    "换手率": "turnover",
    "振幅": "amplitude",
    "涨跌幅": "chg",
    "涨跌额": "change_amount"
}
result_field_list = [v for k, v in field_map.items()]
flag, writer = get_writer_model({
    "model_id": "f4f58112235f4625a72f880a373ff697",
    "load_type": "upsert",
    "only_fields": "_id"
})
if not flag:
    logger.exception(f"获取写入模型失败")

stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
stock_zh_a_spot_em_df = stock_zh_a_spot_em_df.rename(columns=field_map)
today_date = format_date(get_now_time(), format='%Y-%m-%d', res_type='datetime')
stock_info_result = []
for k, row in stock_zh_a_spot_em_df.iterrows():
    row = row.to_dict()
    dic = {k: v for k, v in row.items() if k in result_field_list}
    dic['time'] = today_date
    hash_key = f"{dic['symbol']}{dic['time']}"
    dic['_id'] = md5(hash_key)
    stock_info_result.append(dic)
writer.write(stock_info_result)
logger.info(f"数据采集成功，数据量：{len(stock_info_result)}")


