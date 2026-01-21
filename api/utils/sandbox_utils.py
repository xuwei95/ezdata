"""
沙箱API调用工具
"""
import os
import requests
from typing import Dict, Any


def get_sandbox_config() -> Dict[str, Any]:
    """获取沙箱配置"""
    return {
        'enabled': os.environ.get('SAFE_MODE', 'false').lower() == 'true',
        'api_url': os.environ.get('SANDBOX_API_URL', 'http://127.0.0.1:8003'),
        'bearer_key': os.environ.get('SANDBOX_BEARER_KEY', 'default-bearer-key'),
        'timeout': int(os.environ.get('SANDBOX_TIMEOUT', '300'))
    }


def get_logger_config(logger) -> Dict[str, Any]:
    """从logger获取配置信息"""
    logger_config = {}

    # 获取 logger 名称（p_name）
    if hasattr(logger, 'name'):
        logger_config['p_name'] = logger.name

    # 提取额外字段（additional_fields）
    additional_fields = {}
    if hasattr(logger, 'handlers'):
        for handler in logger.handlers:
            # 检查是否是ES handler
            handler_class = handler.__class__.__name__
            if 'CMRES' in handler_class or 'ES' in handler_class or 'Elasticsearch' in handler_class:
                logger_config['type'] = 'elasticsearch'

                # 提取 hosts
                if hasattr(handler, '_client') and hasattr(handler._client, 'transport'):
                    # 从 ES client 提取 hosts
                    try:
                        hosts_list = [str(node) for node in handler._client.transport.hosts]
                        if hosts_list:
                            logger_config['hosts'] = hosts_list[0] if len(hosts_list) == 1 else hosts_list
                    except:
                        pass

                # 提取 index
                if hasattr(handler, '_index_name_func'):
                    try:
                        index = handler._index_name_func()
                        logger_config['index'] = index
                    except:
                        pass

                # 提取额外字段 (es_additional_fields)
                if hasattr(handler, 'es_additional_fields'):
                    additional_fields = handler.es_additional_fields or {}

            elif 'File' in handler_class:
                logger_config['type'] = 'file'
                if hasattr(handler, 'baseFilename'):
                    logger_config['file'] = handler.baseFilename

    # 从环境变量获取ES配置（如果handler中没有获取到）
    if not logger_config.get('type') and os.environ.get('LOGGER_TYPE') == 'es':
        logger_config['type'] = 'elasticsearch'
        logger_config['hosts'] = os.environ.get('ES_HOSTS', '')
        logger_config['index'] = os.environ.get('TASK_LOG_INDEX', 'task_logs')

    # 添加额外字段
    if additional_fields:
        logger_config['additional_fields'] = additional_fields

    return logger_config


def execute_python_in_sandbox(code: str, context: Dict[str, Any], logger, timeout: int = 300) -> Dict[str, Any]:
    """在沙箱中执行Python代码"""
    config = get_sandbox_config()

    if not config['enabled']:
        raise ValueError('Sandbox mode is not enabled')

    logger_config = get_logger_config(logger)

    url = f"{config['api_url']}/python/execute"
    headers = {
        'Authorization': f"Bearer {config['bearer_key']}",
        'Content-Type': 'application/json'
    }

    payload = {
        'code': code,
        'context': context,
        'timeout': timeout or config['timeout'],
        'logger_config': logger_config
    }

    logger.info(f'[SANDBOX] Sending Python code to sandbox: {url}')
    logger.debug(f'[SANDBOX] Payload: {payload}')

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout + 10)
        response.raise_for_status()
        result = response.json()

        logger.info(f'[SANDBOX] Execution completed. Success: {result.get("success")}')

        # 打印输出到logger
        if result.get('output'):
            for line in result['output'].split('\n'):
                if line.strip():
                    logger.info(line)

        # 打印错误到logger
        if result.get('error'):
            logger.error(f'[SANDBOX] Error: {result["error"]}')

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f'[SANDBOX] Failed to connect to sandbox API: {str(e)}')
        raise Exception(f'Sandbox API error: {str(e)}')


def execute_shell_in_sandbox(command: str, logger, timeout: int = 300) -> Dict[str, Any]:
    """在沙箱中执行Shell命令"""
    config = get_sandbox_config()

    if not config['enabled']:
        raise ValueError('Sandbox mode is not enabled')

    logger_config = get_logger_config(logger)

    url = f"{config['api_url']}/shell/execute"
    headers = {
        'Authorization': f"Bearer {config['bearer_key']}",
        'Content-Type': 'application/json'
    }

    payload = {
        'command': command,
        'timeout': timeout or config['timeout'],
        'logger_config': logger_config
    }

    logger.info(f'[SANDBOX] Sending Shell command to sandbox: {url}')
    logger.debug(f'[SANDBOX] Command: {command}')

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout + 10)
        response.raise_for_status()
        result = response.json()

        logger.info(f'[SANDBOX] Execution completed. Success: {result.get("success")}')

        # 打印输出到logger
        if result.get('result') and result['result'].get('output'):
            for line in result['result']['output'].split('\n'):
                if line.strip():
                    logger.info(line)

        # 打印错误到logger
        if result.get('error'):
            logger.error(f'[SANDBOX] Error: {result["error"]}')

        return result

    except requests.exceptions.RequestException as e:
        logger.error(f'[SANDBOX] Failed to connect to sandbox API: {str(e)}')
        raise Exception(f'Sandbox API error: {str(e)}')


def execute_data_in_sandbox(code: str, model_info: dict, timeout: int = 600) -> Dict[str, Any]:
    """在沙箱中执行数据处理代码（用于数据抽取和数据分析）

    Args:
        code: 要执行的Python代码
        model_info: 数据模型信息，用于初始化reader
        timeout: 超时时间（秒）

    Returns:
        包含执行结果的字典
    """
    config = get_sandbox_config()

    if not config['enabled']:
        raise ValueError('Sandbox mode is not enabled')

    url = f"{config['api_url']}/data/execute"
    headers = {
        'Authorization': f"Bearer {config['bearer_key']}",
        'Content-Type': 'application/json'
    }
    # 构建请求payload，config中包含extract_info，sandbox会自行初始化reader
    payload = {
        'code': code,
        'config': {
            'extract_info': model_info
        },
        'timeout': timeout
    }
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=timeout + 50)
        response.raise_for_status()
        result = response.json()
        return result
    except requests.exceptions.RequestException as e:
        raise Exception(f'Sandbox API error: {str(e)}')
