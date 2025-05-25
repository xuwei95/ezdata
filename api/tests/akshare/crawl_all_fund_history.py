import akshare as ak
from utils.etl_utils import get_writer_model
from utils.common_utils import md5, format_date
from utils.logger.logger import get_logger
logger = get_logger('fund_crawler', 'fund_crawler')


def transform_fund_data(fund_data, fund_code, fund_info):
    """
    转换数据
    :param fund_data:
    :return:
    """
    field_map = {
        "净值日期": "time",
        "单位净值": "value",
        "日增长率": "rate",
    }
    fund_data = fund_data.rename(columns=field_map)
    fund_data['code'] = fund_code
    fund_data['name'] = fund_info['name']
    fund_data['fund_type'] = fund_info['fund_type']
    result_list = []
    for k, row in fund_data.iterrows():
        row = row.to_dict()
        row['time'] = format_date(row['time'], format='%Y-%m-%d', res_type='datetime')
        hash_key = f"{row['code']}{str(row['time'])}"
        row['_id'] = md5(hash_key)
        result_list.append(row)
    return result_list


flag, writer = get_writer_model({
    "model_id": "239ecc8d91a84d12a298e22b8c22db58",
    "load_type": "upsert",
    "only_fields": "_id"
})
if not flag:
    logger.exception(f"获取写入模型失败")
# 获取基金代码-信息 map
code_id_dict = {}
fund_name_em_df = ak.fund_name_em()
for k, row in fund_name_em_df.iterrows():
    row = row.to_dict()
    code_id_dict[row['基金代码']] = {
        'name': row['基金简称'],
        'fund_type': row['基金类型']
    }

i = 1
for fund_code in code_id_dict:
    try:
        fund_info = code_id_dict[fund_code]
        df = ak.fund_open_fund_info_em(fund=fund_code, indicator="单位净值走势")
        fund_data = transform_fund_data(df, fund_code, fund_info)
        writer.write(fund_data)
        logger.info(f"{i}/{len(code_id_dict)}, 获取数据成功，基金代码：{fund_code}，数据量：{len(fund_data)}")
    except Exception as e:
        logger.info(f"获取数据失败，{e}")
        logger.exception(e)
    i += 1
