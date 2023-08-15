# coding: utf-8
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from config import LOG_LEVEL

if not os.path.exists('logs'):
    os.mkdir('logs')

logging.basicConfig(format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s')


class LogFileHandler(object):
    def __init__(self, name, log_level=LOG_LEVEL):
        if not name.endswith('.logs'):
            name = name + '.log'
        file_name = os.path.join('logs', name)
        handler = logging.handlers.RotatingFileHandler(file_name, maxBytes=1024*1024*1024, backupCount=3, )
        handler.setFormatter(
            logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s'))
        handler.suffix = "%Y%m%d.task"
        handler.mode = 'a'
        handler.setLevel(log_level)
        print(handler)
        self._handler = handler

    def get_handler(self):
        return self._handler


def get_logger(p_name, f_name, log_level=LOG_LEVEL):
    logger = logging.getLogger(p_name)
    logger.setLevel(log_level)
    logger.addHandler(LogFileHandler(f_name).get_handler())
    return logger


if __name__ == '__main__':
    log = get_logger('test', '1111')
    try:
        1/0
    except Exception as e:
        log.exception(e)
