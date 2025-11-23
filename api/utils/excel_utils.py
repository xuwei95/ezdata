'''
excel处理相关函数
'''
import io
import pandas as pd
from utils.common_utils import get_now_time


def gen_excel_file(gen_dict):
    '''
    生成excel数据导入模板
    :param gen_dict:
    :return:
    '''
    df = pd.DataFrame([gen_dict])
    # 使用字节流存储
    output = io.BytesIO()
    # 保存文件
    df.to_excel(output, index=False)
    # 文件seek位置，从头(0)开始
    output.seek(0)
    filename = "%s.xls" % get_now_time()
    return output, filename
