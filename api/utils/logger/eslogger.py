# encoding: utf-8
"""
日志操作类
"""
import logging
from utils.logger.eslog import CMRESHandler
from config import ES_CONF, ES_HOSTS,  SYS_LOG_INDEX, LOG_LEVEL
import datetime
import time


def beijing_converter(sec):
    if time.strftime('%z') == "+0800":
        return datetime.datetime.now().timetuple()
    return (datetime.datetime.now() + datetime.timedelta(hours=8)).timetuple()


auth_type = CMRESHandler.AuthType.BASIC_AUTH if ES_CONF.get('http_auth') else CMRESHandler.AuthType.NO_AUTH
auth_details = ES_CONF.get('http_auth') if ES_CONF.get('http_auth') else ('', '')


def get_es_logger(p_name, hosts=ES_HOSTS, index=SYS_LOG_INDEX, auth_type=auth_type, auth_details=auth_details, log_level=LOG_LEVEL, **kwargs):
    """
    example: get_logger('test', [{'host': 'localhost'}], 'test_log_1', **{'event_id': 1000})
    """
    es_enable = kwargs.get('es_enable', True)
    _logger = logging.getLogger(p_name)
    _logger.setLevel(log_level)
    _logger.handlers.clear()
    if es_enable:
        print('es_logger:', p_name, hosts, auth_type, auth_details, index)
        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s')
        formatter.converter = beijing_converter
        _handler = CMRESHandler(hosts=hosts,
                                # 可以配置对应的认证权限
                                auth_type=auth_type,
                                auth_details=auth_details,
                                es_index_name=index,
                                buffer_size=0,
                                # 额外增加环境标识
                                es_additional_fields=kwargs)
        _handler.formatter = formatter
        _logger.addHandler(_handler)
    return _logger


if __name__ == '__main__':
    logger = get_es_logger(p_name='system', index='test_logs', **{'api': '1'})
    logger.info('test1111')
    try:
        s = 1 / 0
    except Exception as e:
        logger.exception(e)

