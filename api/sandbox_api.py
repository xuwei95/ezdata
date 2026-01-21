#!/usr/bin/env python3
"""
Sandbox API Service
代码执行沙箱服务 - 支持多种语言执行

端口: 8003
认证: Authorization: Bearer <key>

端点:
- POST /python/execute  - Python代码执行
- POST /shell/execute   - Shell命令执行
- POST /data/execute    - 数据处理执行
"""

import os
import ast
import time
import subprocess
import platform
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from contextlib import redirect_stderr
import io
import logging
import sys
import pandas as pd
from etl.registry import get_reader
from utils.logger.eslog import CMRESHandler
from utils.common_utils import df_to_list
# resource模块仅在Unix/Linux上可用
IS_WINDOWS = platform.system() == 'Windows'
if not IS_WINDOWS:
    import resource
else:
    resource = None

app = Flask(__name__)
CORS(app, origins=["*"])

# 配置
SANDBOX_BEARER_KEY = os.environ.get('SANDBOX_BEARER_KEY', 'default-bearer-key')

# 从环境变量读取允许的模块列表（逗号分割）
DEFAULT_ALLOWED_MODULES = [
    'pandas', 'numpy', 'math', 'datetime', 'json', 'pyecharts',
    're', 'collections', 'itertools', 'operator', 'functools',
    'base64', 'hashlib', 'hmac', 'uuid'
]
allowed_modules_str = os.environ.get('SANDBOX_ALLOWED_MODULES', '')
ALLOWED_MODULES = (
    [m.strip() for m in allowed_modules_str.split(',') if m.strip()]
    if allowed_modules_str else DEFAULT_ALLOWED_MODULES
)

# 从环境变量读取Python危险模式列表（逗号分割）
DEFAULT_DANGEROUS_PATTERNS = [
    'eval', 'exec', 'compile', 'open', 'file', 'input',
    'globals', 'locals', 'dir', 'vars',
    'delattr', 'reload', 'execfile',
    'os.', 'sys.', 'subprocess.', 'socket.', 'urllib.', 'requests.',
    'import os', 'import sys', 'import subprocess', 'import socket',
    'multiprocessing', 'threading', 'ctypes', '__builtin__', 'builtins'
]
dangerous_patterns_str = os.environ.get('SANDBOX_DANGEROUS_PATTERNS', '')
DANGEROUS_PATTERNS = (
    [p.strip() for p in dangerous_patterns_str.split(',') if p.strip()]
    if dangerous_patterns_str else DEFAULT_DANGEROUS_PATTERNS
)

# 从环境变量读取Shell危险命令列表（逗号分割）
DEFAULT_DANGEROUS_COMMANDS = ['rm -rf', 'rm -fr', 'dd if=', 'mkfs', 'format', '>>', '&&', '||', '; ']
dangerous_commands_str = os.environ.get('SANDBOX_DANGEROUS_COMMANDS', '')
DANGEROUS_COMMANDS = (
    [c.strip() for c in dangerous_commands_str.split(',') if c.strip()]
    if dangerous_commands_str else DEFAULT_DANGEROUS_COMMANDS
)


def verify_bearer_token():
    """验证Bearer Token"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False, 'Missing or invalid Authorization header'

    token = auth_header.split(' ')[1]
    if token != SANDBOX_BEARER_KEY:
        return False, 'Invalid bearer token'

    return True, ''


def init_logger(logger_config: dict):
    """
    初始化logger，根据配置返回 ES logger 或普通 logger

    logger_config 格式:
    {
        'type': 'elasticsearch',
        'hosts': 'http://elastic:pass@host:9200',
        'index': 'task_logs',
        'p_name': 'sandbox_task',  # logger名称
        'additional_fields': {      # 额外的ES字段，如task_uuid等
            'task_uuid': 'xxx',
            'worker': 'xxx'
        }
    }
    """

    # 提取参数
    p_name = logger_config.get('p_name', 'sandbox')
    additional_fields = logger_config.get('additional_fields', {})

    # 如果没有配置，返回简单的 logger
    if not logger_config or logger_config.get('type') != 'elasticsearch':
        # 创建一个简单的 logger
        logger = logging.getLogger(p_name)
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        # 添加 console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    # 初始化 ES logger
    try:
        hosts = logger_config.get('hosts', '')
        index = logger_config.get('index', 'sandbox_logs')

        # 解析 hosts
        if isinstance(hosts, str):
            # 如果是字符串，可能包含认证信息 http://user:pass@host:port
            if '@' in hosts:
                # 提取认证信息
                auth_part = hosts.split('@')[0].replace('http://', '').replace('https://', '')
                if ':' in auth_part:
                    username, password = auth_part.split(':')
                    auth_details = (username, password)
                    auth_type = CMRESHandler.AuthType.BASIC_AUTH
                    # 重构 hosts 为列表
                    host_part = hosts.split('@')[1]
                    hosts = [host_part]
                else:
                    auth_type = CMRESHandler.AuthType.NO_AUTH
                    auth_details = ('', '')
                    hosts = [hosts]
            else:
                auth_type = CMRESHandler.AuthType.NO_AUTH
                auth_details = ('', '')
                hosts = [hosts]
        elif isinstance(hosts, list):
            auth_type = CMRESHandler.AuthType.NO_AUTH
            auth_details = ('', '')
        else:
            auth_type = CMRESHandler.AuthType.NO_AUTH
            auth_details = ('', '')
            hosts = []

        # 创建 ES logger，使用 p_name
        logger = logging.getLogger(p_name)
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

        # 合并额外字段和source标识
        es_fields = {
            'source': 'sandbox',
            **additional_fields
        }

        handler = CMRESHandler(
            hosts=hosts,
            auth_type=auth_type,
            auth_details=auth_details,
            es_index_name=index,
            buffer_size=0,
            es_additional_fields=es_fields  # 传入额外字段
        )
        handler.formatter = formatter
        logger.addHandler(handler)

        return logger

    except Exception as e:
        print(f"Failed to initialize ES logger: {e}, using simple logger instead")
        # 如果 ES logger 初始化失败，使用简单 logger
        logger = logging.getLogger(p_name)
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger


def validate_python_code(code: str) -> tuple[bool, str]:
    """验证Python代码安全性"""
    # AST语法检查
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in ALLOWED_MODULES:
                        return False, f"Import '{alias.name}' not allowed"

            if isinstance(node, ast.ImportFrom):
                if node.module:
                    # 提取顶级模块（第一个点之前的部分）
                    top_module = node.module.split('.')[0]
                    if top_module not in ALLOWED_MODULES:
                        return False, f"Import from '{node.module}' not allowed (top module '{top_module}' not in allowed list)"

            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['eval', 'exec', 'compile']:
                        return False, f"Function '{node.func.id}' is not allowed"
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"

    # 模式检查
    for pattern in DANGEROUS_PATTERNS:
        if pattern in code:
            return False, f"Dangerous pattern detected: '{pattern}'"

    return True, "Safe"


def execute_python(code: str, context: dict, timeout: int = 30, logger_config: dict = None) -> dict:
    """执行Python代码"""
    try:
        # 初始化logger
        logger = init_logger(logger_config or {})

        # 资源限制（仅在Unix/Linux上）
        if not IS_WINDOWS and resource:
            resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))

        # 捕获输出
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # 创建执行环境，注入 logger 和 context
        exec_globals = {
            'logger': logger,
            '__builtins__': __builtins__,  # 使用默认的内置函数
            **context
        }

        exec_locals = {}

        # 重定向标准输出到捕获器
        original_stdout = sys.stdout
        sys.stdout = stdout_capture

        try:
            # 执行代码
            with redirect_stderr(stderr_capture):
                exec(code, exec_globals, exec_locals)
        finally:
            # 恢复标准输出
            sys.stdout = original_stdout

        result = exec_locals.get('result', None)
        # 将dataframe类型数据转为列表返回
        if isinstance(result, dict) and 'value' in result and isinstance(result['value'], pd.DataFrame):
            result['value'] = df_to_list(result['value'])
        return {
            'success': True,
            'result': result,
            'output': stdout_capture.getvalue(),
            'error': stderr_capture.getvalue()
        }

    except MemoryError:
        return {'success': False, 'error': 'Memory limit exceeded'}
    except Exception as e:
        return {'success': False, 'error': f'{type(e).__name__}: {str(e)}\n{traceback.format_exc()}'}


def execute_shell(command: str, timeout: int = 30, logger_config: dict = None) -> dict:
    """执行Shell命令，参考 shell_tasks.py 的实现"""
    try:
        # 初始化logger
        logger = init_logger(logger_config or {})

        # 危险命令检查
        for cmd in DANGEROUS_COMMANDS:
            if cmd in command:
                logger.error(f'Dangerous shell command detected: {cmd}')
                return {
                    'success': False,
                    'error': f'Dangerous shell command detected: {cmd}'
                }

        # 执行命令
        logger.info(f'Executing command: {command}')

        # 使用 Popen 执行命令并实时捕获输出
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        start_time = time.time()
        output_lines = []

        # 实时读取输出
        while True:
            line = process.stdout.readline()
            if line == '' and process.poll() is not None:
                break

            if line:
                # 去除换行符并记录到 logger
                clean_line = line.rstrip()
                if clean_line:
                    logger.info(clean_line)
                    output_lines.append(line)

            # 超时检查
            if time.time() - start_time > timeout:
                logger.warning(f'Command timeout after {timeout} seconds, terminating...')
                process.terminate()
                process.wait(timeout=5)
                return {
                    'success': False,
                    'error': f'Command timeout after {timeout} seconds'
                }

        # 等待进程结束
        exit_code = process.wait()

        # 记录执行结果
        if exit_code == 0:
            logger.info(f'Command completed successfully')
        else:
            logger.error(f'Command exited with code {exit_code}')

        return {
            'success': exit_code == 0,
            'result': {
                'exit_code': exit_code,
                'output': ''.join(output_lines)
            },
            'error': None if exit_code == 0 else f'Command exited with code {exit_code}'
        }

    except Exception as e:
        return {'success': False, 'error': f'{type(e).__name__}: {str(e)}\n{traceback.format_exc()}'}


def execute_data(code: str, config: dict, timeout: int = 600) -> dict:
    """执行数据处理代码，根据数据模型配置实例化reader"""
    try:
        # 从配置获取extract_info（用于创建reader）
        extract_info = config.get('extract_info', {})
        # 创建Reader实例
        reader = None
        if extract_info:
            flag, reader = get_reader(extract_info)
            if not flag:
                raise RuntimeError(f'reader初始化失败：{reader}')
        else:
            raise RuntimeError(f'reade信息获取失败')
        # 创建上下文，包含reader
        context = {
            'reader': reader
        }
        # 执行代码
        return execute_python(code, context, timeout)

    except Exception as e:
        return {'success': False, 'error': f'Data execution error: {str(e)}\n{traceback.format_exc()}'}


@app.route('/python/execute', methods=['POST'])
def python_execute():
    """Python代码执行端点"""
    # 验证认证
    valid, msg = verify_bearer_token()
    if not valid:
        return jsonify({'success': False, 'error': msg}), 401

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    code = data.get('code', '')
    context = data.get('context', {})
    timeout = data.get('timeout', 30)
    logger_config = data.get('logger_config', {})

    if not code:
        return jsonify({'success': False, 'error': 'No code provided'}), 400

    # 验证代码
    is_safe, reason = validate_python_code(code)
    if not is_safe:
        return jsonify({'success': False, 'error': f'Code validation failed: {reason}'}), 400

    start_time = time.time()

    try:
        result = execute_python(code, context, timeout, logger_config)
        result['execution_time'] = time.time() - start_time
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Execution error: {str(e)}\n{traceback.format_exc()}',
            'execution_time': time.time() - start_time
        }), 500


@app.route('/shell/execute', methods=['POST'])
def shell_execute():
    """Shell命令执行端点"""
    # 验证认证
    valid, msg = verify_bearer_token()
    if not valid:
        return jsonify({'success': False, 'error': msg}), 401

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    command = data.get('command', '')
    timeout = data.get('timeout', 30)
    logger_config = data.get('logger_config', {})

    if not command:
        return jsonify({'success': False, 'error': 'No command provided'}), 400

    start_time = time.time()

    try:
        result = execute_shell(command, timeout, logger_config)
        result['execution_time'] = time.time() - start_time
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Execution error: {str(e)}\n{traceback.format_exc()}',
            'execution_time': time.time() - start_time
        }), 500


@app.route('/data/execute', methods=['POST'])
def data_execute():
    """数据处理执行端点"""
    # 验证认证
    valid, msg = verify_bearer_token()
    if not valid:
        return jsonify({'success': False, 'error': msg}), 401

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    code = data.get('code', '')
    config = data.get('config', {})
    timeout = data.get('timeout', 60)

    if not code:
        return jsonify({'success': False, 'error': 'No code provided'}), 400

    # 验证代码
    is_safe, reason = validate_python_code(code)
    if not is_safe:
        return jsonify({'success': False, 'error': f'Code validation failed: {reason}'}), 400

    start_time = time.time()

    try:
        result = execute_data(code, config, timeout)
        result['execution_time'] = time.time() - start_time
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Execution error: {str(e)}\n{traceback.format_exc()}',
            'execution_time': time.time() - start_time
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '1.0.0',
        'endpoints': ['/python/execute', '/shell/execute', '/data/execute']
    })


if __name__ == '__main__':
    port = int(os.environ.get('SANDBOX_PORT', 8003))
    debug = os.environ.get('SANDBOX_DEBUG', 'false').lower() == 'true'

    print(f"""
    ╔══════════════════════════════════════╗
    ║         Sandbox API Service          ║
    ╠══════════════════════════════════════╣
    ║  Port: {port:<34}                    ║
    ║  Debug: {debug:<34}                  ║
    ║  Auth: Bearer Token                  ║
    ║  Endpoints:                          ║
    ║    - POST /python/execute            ║
    ║    - POST /shell/execute             ║
    ║    - POST /data/execute              ║
    ╚══════════════════════════════════════╝
    """)

    app.run(host='0.0.0.0', port=port, debug=debug)
