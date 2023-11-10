import akshare as ak
from utils.etl_utils import get_writer_model
from utils.common_utils import md5, format_date
from utils.logger.logger import get_logger
logger = get_logger('stock_crawler', 'stock_crawler')


def transform_stock_data(stock_data, stock_code, stock_name):
    """
    转换数据
    :param stock_data:
    :return:
    """
    field_map = {
        "日期": "time",
        "最高": "high",
        "最低": "low",
        "开盘": "open",
        "收盘": "close",
        "成交量": "volume",
        "成交额": "amount",
        "换手率": "turnover",
        "振幅": "amplitude",
        "涨跌幅": "chg",
        "涨跌额": "change_amount"
    }
    stock_data = stock_data.rename(columns=field_map)
    stock_data['symbol'] = stock_code
    stock_data['name'] = stock_name
    result_list = []
    for k, row in stock_data.iterrows():
        row = row.to_dict()
        row['time'] = format_date(row['time'], res_type='datetime')
        hash_key = f"{row['symbol']}{row['time']}"
        row['_id'] = md5(hash_key)
        result_list.append(row)
    return result_list


flag, writer = get_writer_model({
    "model_id": "f4f58112235f4625a72f880a373ff697",
    "load_type": "upsert",
    "only_fields": "_id"
})
if not flag:
    logger.exception(f"获取写入模型失败")
# 获取股票代码-名称 map
code_id_dict = {}
stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()
for k, row in stock_zh_a_spot_em_df.iterrows():
    row = row.to_dict()
    code_id_dict[row['代码']] = row['名称']
i = 1
for stock_code in code_id_dict:
    try:
        stock_name = code_id_dict[stock_code]
        if stock_name == 1:
            stock_name = 'unknow'
        stock_data = ak.stock_zh_a_hist(symbol=stock_code, adjust="qfq")
        stock_data = transform_stock_data(stock_data, stock_code, stock_name)
        writer.write(stock_data)
        logger.info(f"{i}/{len(code_id_dict)}, 获取数据成功，股票代码：{stock_code}，数据量：{len(stock_data)}")
    except Exception as e:
        logger.info(f"获取数据失败，{e}")
        logger.exception(e)
    i += 1
