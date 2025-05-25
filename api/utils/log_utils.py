from utils.logger.eslogger import get_es_logger
from utils.logger.logger import get_logger
from config import LOG_LEVEL, LOGGER_TYPE, SYS_LOG_INDEX, TASK_LOG_INDEX, INTERFACE_LOG_INDEX


def get_sys_logger():
    sys_log_keys = {
        'api_path': '',
        'parameter': '',
        'user_id': 0,
        'user_name': '',
        'ip': '',
        'duration': 0
    }
    if LOGGER_TYPE == 'es':
        logger = get_es_logger(p_name='system_log', index=SYS_LOG_INDEX, log_level=LOG_LEVEL, **sys_log_keys)
    else:
        logger = get_logger(p_name='system_log', f_name=SYS_LOG_INDEX, log_level=LOG_LEVEL)
    return logger


def get_interface_logger(interface_log_keys={}):
    if LOGGER_TYPE == 'es':
        logger = get_es_logger(p_name='interface_log', index=INTERFACE_LOG_INDEX, log_level=LOG_LEVEL, **interface_log_keys)
    else:
        logger = get_logger(p_name='interface_log', f_name=INTERFACE_LOG_INDEX, log_level=LOG_LEVEL)
    return logger


def get_task_logger(p_name, task_log_keys={}):
    if LOGGER_TYPE == 'es':
        logger = get_es_logger(p_name=p_name, index=TASK_LOG_INDEX, **task_log_keys)
    else:
        # task_uuid = task_log_keys.get('task_uuid')
        # f_name = f"task_{task_uuid}"
        logger = get_logger(p_name=p_name, f_name=TASK_LOG_INDEX, log_level=LOG_LEVEL)
    return logger
