from web_apps import app
from flask_cors import CORS
# 加载app
from utils.common_utils import import_class
from blueprints import BLUEPRINT_DICT
from utils.log_utils import get_sys_logger
from utils.auth import get_access_info
from flask import request
import time
# 注册应用
for app_name, dic in BLUEPRINT_DICT.items():
    bp = import_class(dic['blueprint'])
    app.register_blueprint(bp, url_prefix=dic['url_prefix'])
sys_logger = get_sys_logger()


@app.before_request
def set_g():
    # 将当前时间戳赋值给app全局变量
    app.g = int(round(time.time() * 1000))


@app.after_request
def write_access_log(response):
    """
    请求接口后写入日志
    :param response:
    :return:
    """
    # 接口日志白名单，不记录系统日志
    white_list = ['/api/data_interface/query']
    if request.path not in white_list:
        access_info = get_access_info()
        duration = round((time.time() * 1000 - app.g) / 1000, 3)  # 计算接口耗时
        access_info['duration'] = duration
        sys_logger.info(access_info)
    return response


CORS(app, supports_credentials=True)  # 跨域支持

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)







