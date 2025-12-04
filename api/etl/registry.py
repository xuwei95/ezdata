# -*- coding: utf-8 -*-
"""
统一的 Handler 注册中心
整合 MindsDB handlers 和自定义 handlers
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from etl.utils.mindsdb_client import IntegrationsClient
from etl.data_models.mindsdb_sql import MindsDBSqlModel
from etl.data_models.mindsdb_table import MindsDBTableModel

from utils.common_utils import import_class
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 公共注册变量 - 自定义 Handlers
# ============================================================================

# 自定义 handlers 映射（保留特殊数据源）
# 格式: {"source_type:model_type": "handler_class_path"}
CUSTOM_HANDLERS = {
    # AkShare - 金融数据接口（只读）
    'akshare:None': 'etl.data_models.akshare_api.AkShareModel',
    'akshare:akshare_api': 'etl.data_models.akshare_api.AkShareModel',

    # CCXT - 加密货币交易所接口（只读）
    'ccxt:None': 'etl.data_models.ccxt_api.CCxtModel',
    'ccxt:ccxt_api': 'etl.data_models.ccxt_api.CCxtModel',

    # Kafka - 实时流数据（可读可写）
    'kafka:None': 'etl.data_models.kafka_topic.KafkaTopicModel',
    'kafka:kafka_topic': 'etl.data_models.kafka_topic.KafkaTopicModel',

    # MySQL Binlog - CDC 变更数据捕获（只读）
    'mysql:mysql_binlog': 'etl.data_models.mysql_binlog.MysqlBinlogModel',

    # File Handler - 使用localfile模型处理本地文件（只读）
    'file:None': 'etl.data_models.local_file.LocalFileModel',
    'file:file_table': 'etl.data_models.local_file.LocalFileModel',

    # Custom S3 - 支持MinIO等S3兼容存储
    'custom_s3:None': 'etl.data_models.custom_s3.CustomS3Model',
    'custom_s3:custom_s3_table': 'etl.data_models.custom_s3.CustomS3Model',

    # neo4j
    'neo4j:None': 'etl.data_models.neo4j_models.N4jSqlModel',
    'neo4j:sql': 'etl.data_models.neo4j_models.N4jSqlModel',
    'neo4j:neo4j_graph': 'etl.data_models.neo4j_models.N4jGraphModel',

    # Prometheus - 监控指标数据源（只读）
    'prometheus:None': 'etl.data_models.prometheus_models.PromQlModel',
    'prometheus:promql': 'etl.data_models.prometheus_models.PromQlModel',
    'prometheus:metric': 'etl.data_models.prometheus_models.PromMetricModel',

    # HTTP - HTTP API和HTML页面数据源（只读）
    'http:None': 'etl.data_models.http_models.BaseHttpModel',
    'http:http_json': 'etl.data_models.http_models.HttpApiModel',
    'http:http_html': 'etl.data_models.http_models.HttpHtmlModel',

    # Redis - Redis数据库（可读可写）
    'redis:None': 'etl.data_models.redis_models.BaseRedisModel',
    'redis:redis_string': 'etl.data_models.redis_models.RedisStringModel',
    'redis:redis_list': 'etl.data_models.redis_models.RedisListModel',
    'redis:redis_list_stream': 'etl.data_models.redis_models.RedisListStreamModel',
    'redis:redis_map': 'etl.data_models.redis_models.RedisMapModel'
}

# 自定义 handlers 中支持写入的模型
# 格式: {"source_type:model_type"}
WRITABLE_HANDLERS = {
    # Kafka - 支持写入消息
    'kafka:None',
    'kafka:kafka_topic',

    # Redis - 支持写入数据
    'redis:None',
    'redis:redis_string',
    'redis:redis_list',
    'redis:redis_list_stream',
    'redis:redis_map',
}


class HandlerRegistry:
    """
    Handler 注册中心
    负责管理和分发 reader/writer
    """

    def __init__(self):
        self.mindsdb_client = IntegrationsClient()

        # 使用模块级别的公共注册变量
        self.custom_handlers = CUSTOM_HANDLERS
        self.writable_custom_handlers = WRITABLE_HANDLERS

        # 获取所有 MindsDB 支持的 DATA 类型 handlers（排除 ML 类型）
        self.mindsdb_data_handlers = set(self.mindsdb_client.list_data_handlers())

        logger.info(f"注册中心初始化完成: {len(self.mindsdb_data_handlers)} 个 MindsDB DATA handlers, "
                   f"{len(self.custom_handlers)} 个自定义 handlers "
                   f"(其中 {len(self.writable_custom_handlers)} 个可写)")

    def get_reader(self, model_info, extend_model_dict=None):
        """
        获取 reader 对象

        Args:
            model_info: 模型配置信息
            extend_model_dict: 额外的模型映射字典

        Returns:
            (success, reader_instance) 或 (False, error_message)
        """
        if extend_model_dict:
            self.custom_handlers.update(extend_model_dict)

        source_type = model_info['source'].get('type')
        model_type = model_info.get('model', {}).get('type', 'None')
        key = f"{source_type}:{model_type}"

        # 1. 优先使用自定义 handler
        if key in self.custom_handlers:
            return self._create_custom_handler(key, model_info)

        # 2. 尝试使用 source_type:None 的自定义 handler
        default_key = f"{source_type}:None"
        if default_key in self.custom_handlers:
            return self._create_custom_handler(default_key, model_info)

        # 3. 使用 MindsDB handler (适配器)
        if self._is_mindsdb_supported(source_type):
            return self._create_mindsdb_handler(model_info)

        # 4. 未找到对应的 handler
        return False, f'未找到对应reader: {key}'

    def get_writer(self, model_info, extend_model_dict=None):
        """
        获取 writer 对象
        写入操作优先使用自定义 handler，MindsDB 作为备选

        Args:
            model_info: 模型配置信息
            extend_model_dict: 额外的模型映射字典

        Returns:
            (success, writer_instance) 或 (False, error_message)
        """
        if extend_model_dict:
            self.custom_handlers.update(extend_model_dict)

        source_type = model_info['source'].get('type')
        model_type = model_info['model'].get('type')
        key = f"{source_type}:{model_type}"

        # 1. 优先使用自定义 handler（写入通常需要特殊处理）
        if key in self.custom_handlers:
            return self._create_custom_handler(key, model_info)

        # 2. 尝试使用 MindsDB handler (适配器，支持基本的 INSERT/UPDATE)
        if self._is_mindsdb_supported(source_type):
            return self._create_mindsdb_handler(model_info)

        # 3. 未找到对应的 handler
        return False, f'未找到对应的 writer: {key}'

    def _create_custom_handler(self, key, model_info):
        """创建自定义 handler 实例"""
        try:
            model_class = self.custom_handlers[key]
            DataModel = import_class(model_class)
            data_model = DataModel(model_info)
            logger.info(f"使用自定义 handler: {key}")
            return True, data_model
        except Exception as e:
            logger.error(f"创建自定义 handler 失败: {key}, 错误: {e}")
            return False, str(e)

    def _create_mindsdb_handler(self, model_info):
        """创建 MindsDB 适配器实例"""
        try:
            source_type = model_info['source'].get('type')
            model_type = model_info.get('model', {}).get('type', 'None')

            # 根据 model_type 决定使用哪个模型类
            # 如果 model_type 包含 'table'，使用 MindsDBTableModel
            # 否则使用 MindsDBSqlModel
            if 'table' in model_type.lower():
                adapter = MindsDBTableModel(model_info)
                logger.info(f"使用 MindsDB table handler: {source_type} ({model_type})")
            else:
                adapter = MindsDBSqlModel(model_info)
                logger.info(f"使用 MindsDB sql handler: {source_type}")

            return True, adapter
        except Exception as e:
            logger.error(f"创建 MindsDB handler 失败: {e}")
            return False, str(e)

    def _is_mindsdb_supported(self, source_type):
        """
        检查 MindsDB 是否支持该数据源类型（仅检查 DATA 类型，排除 ML 类型）

        Args:
            source_type: 数据源类型（如 mysql, postgres 等）

        Returns:
            bool: 是否支持
        """
        # 直接匹配
        if source_type in self.mindsdb_data_handlers:
            return True

        # 尝试带 _handler 后缀
        if f"{source_type}_handler" in self.mindsdb_data_handlers:
            return True

        return False

    def register_custom_handler(self, key, handler_class):
        """
        注册自定义 handler

        Args:
            key: handler 键值，格式为 "source_type:model_type"
            handler_class: handler 类或类路径字符串
        """
        self.custom_handlers[key] = handler_class
        logger.info(f"注册自定义 handler: {key}")

    def list_available_sources(self):
        """
        列出所有可用的数据源类型（仅包含 DATA 类型，排除 ML 类型）
        """
        custom_sources = set()
        for key in self.custom_handlers.keys():
            source_type = key.split(':')[0]
            custom_sources.add(source_type)
        return {
            'custom': sorted(list(custom_sources)),
            'mindsdb_data': sorted(list(self.mindsdb_data_handlers)),
            'total': len(custom_sources) + len(self.mindsdb_data_handlers)
        }

    def get_handler_info(self, source_type):
        """
        获取指定数据源的 handler 信息

        Args:
            source_type: 数据源类型

        Returns:
            dict: handler 信息
        """
        # 检查自定义 handler
        for key in self.custom_handlers.keys():
            if key.startswith(f"{source_type}:None"):
                handler_class_path = self.custom_handlers[key]
                try:
                    # 导入 handler 类
                    handler_class = import_class(handler_class_path)
                    # 获取连接参数定义
                    connection_args = handler_class.get_connection_args()
                    return {
                        'name': source_type,
                        'type': 'custom',
                        'handler_class': handler_class_path,
                        'connection_args': connection_args
                    }
                except Exception as e:
                    logger.error(f"获取自定义 handler 信息失败: {key}, 错误: {e}")
                    return {
                        'name': source_type,
                        'type': 'custom',
                        'handler_class': handler_class_path,
                        'error': str(e)
                    }
        # 检查是否是 MindsDB handler
        if self._is_mindsdb_supported(source_type):
            try:
                return self.mindsdb_client.get_handler_info(source_type)
            except Exception as e:
                logger.error(f"获取 MindsDB handler 信息失败: {e}")

        return {'error': f'未找到 handler: {source_type}'}

    def get_reader_map(self):
        """
        获取所有可用的 reader 映射（仅包含可读的数据源，排除 ML 类型 handlers）

        Returns:
            dict: reader 映射字典，格式为 {"source_type:model_type": "handler_class_path"}
        """
        reader_map = {}

        # 1. 添加自定义 handlers（所有自定义 handlers 都支持读取）
        reader_map.update(self.custom_handlers)

        # 2. 添加 MindsDB DATA 类型 handlers（排除 ML 类型，只包含可读的数据源）
        for handler_name in self.mindsdb_data_handlers:
            # 清理 handler 名称
            source_type = handler_name.replace('_handler', '')

            # 添加 SQL 类型
            key_sql = f"{source_type}:sql"
            if key_sql not in reader_map:
                reader_map[key_sql] = 'etl.data_models.mindsdb_sql.MindsDBSqlModel'

            # 添加默认类型
            key_none = f"{source_type}:None"
            if key_none not in reader_map:
                reader_map[key_none] = 'etl.data_models.mindsdb_sql.MindsDBSqlModel'

            # 添加 table 类型
            key_table = f"{source_type}:{source_type}_table"
            if key_table not in reader_map:
                reader_map[key_table] = 'etl.data_models.mindsdb_table.MindsDBTableModel'

        return reader_map

    def get_writer_map(self):
        """
        获取所有可用的 writer 映射（仅包含支持写入的模型）

        Returns:
            dict: writer 映射字典，格式为 {"source_type:model_type": "handler_class_path"}
        """
        writer_map = {}

        # 1. 添加自定义 handlers 中支持写入的
        # 只包含 writable_custom_handlers 中定义的可写模型
        for key, handler_class in self.custom_handlers.items():
            if key in self.writable_custom_handlers:
                writer_map[key] = handler_class

        # 2. 添加 MindsDB DATA handlers（table 类型支持写入）
        # 排除 ML 类型 handlers
        for handler_name in self.mindsdb_data_handlers:
            source_type = handler_name.replace('_handler', '')
            # 只添加 table 类型作为 writer
            key_table = f"{source_type}:{source_type}_table"
            if key_table not in writer_map:
                writer_map[key_table] = 'etl.data_models.mindsdb_table.MindsDBTableModel'

        return writer_map

    def get_all_source_names(self):
        """
        获取所有数据源名称（简化版本，仅包含 DATA 类型，排除 ML 类型）

        Returns:
            list: 所有数据源类型名称列表
        """
        sources = set()

        # 添加自定义数据源
        for key in self.custom_handlers.keys():
            source_type = key.split(':')[0]
            sources.add(source_type)

        # 添加 MindsDB DATA 数据源（排除 ML 类型）
        for handler_name in self.mindsdb_data_handlers:
            source_type = handler_name.replace('_handler', '')
            sources.add(source_type)

        return sorted(list(sources))

    def get_sub_models(self, model_info):
        """
        获取数据源的子数据模型

        Args:
            model_info: 模型配置信息

        Returns:
            (success, models_list): 成功标志和子模型列表
        """
        try:
            # 创建 handler 实例
            flag, handler = self.get_reader(model_info)
            if not flag:
                return False, handler  # handler 包含错误信息

            # 检查 handler 是否有 gen_models 方法
            if not hasattr(handler, 'gen_models'):
                return False, f'该数据源不支持生成子模型'

            # 调用 gen_models 方法
            try:
                models = handler.gen_models()
                return True, models
            except Exception as e:
                logger.error(f"生成子模型失败: {e}")
                return False, f'生成子模型失败: {str(e)}'
            finally:
                # 清理资源
                if hasattr(handler, 'disconnect'):
                    try:
                        handler.disconnect()
                    except:
                        pass

        except Exception as e:
            logger.error(f"获取子模型失败: {e}")
            return False, str(e)


# 全局单例
_registry = None


def get_registry():
    """获取全局注册中心实例"""
    global _registry
    if _registry is None:
        _registry = HandlerRegistry()
    return _registry


# 便捷函数
def get_reader(model_info, extend_model_dict=None):
    """获取 reader（便捷函数）"""
    registry = get_registry()
    return registry.get_reader(model_info, extend_model_dict)


def get_writer(model_info, extend_model_dict=None):
    """获取 writer（便捷函数）"""
    registry = get_registry()
    return registry.get_writer(model_info, extend_model_dict)


def get_reader_map():
    """获取所有可用的 reader 映射（便捷函数）"""
    registry = get_registry()
    return registry.get_reader_map()


def get_writer_map():
    """获取所有可用的 writer 映射（便捷函数）"""
    registry = get_registry()
    return registry.get_writer_map()


def get_all_source_names():
    """获取所有数据源名称（便捷函数）"""
    registry = get_registry()
    return registry.get_all_source_names()


def get_sub_models(model_info):
    """获取数据源的子数据模型（便捷函数）"""
    registry = get_registry()
    return registry.get_sub_models(model_info)


# ============================================================================
# 便捷注册函数 - 供外部直接注册自定义 Handler
# ============================================================================

def register_handler(source_type, model_type, handler_class, writable=False):
    """
    注册自定义 handler

    Args:
        source_type: 数据源类型（如 'mysql', 'kafka' 等）
        model_type: 模型类型（如 'table', 'sql', 'binlog' 等，可以为 None）
        handler_class: handler 类的完整路径字符串或类对象
        writable: 是否支持写入，默认 False

    Example:
        >>> register_handler('custom_db', 'table', 'my_module.CustomHandler', writable=True)
        >>> register_handler('custom_api', None, MyApiHandler)
    """
    key = f"{source_type}:{model_type}"

    # 如果传入的是类对象，转换为字符串路径
    if not isinstance(handler_class, str):
        handler_class = f"{handler_class.__module__}.{handler_class.__name__}"

    CUSTOM_HANDLERS[key] = handler_class

    if writable:
        WRITABLE_HANDLERS.add(key)

    logger.info(f"已注册自定义 handler: {key} -> {handler_class} (writable={writable})")


def register_writable(source_type, model_type):
    """
    将已注册的 handler 标记为可写

    Args:
        source_type: 数据源类型
        model_type: 模型类型

    Example:
        >>> register_writable('mysql', 'binlog')
    """
    key = f"{source_type}:{model_type}"
    if key not in CUSTOM_HANDLERS:
        logger.warning(f"Handler {key} 未注册，无法标记为可写")
        return False

    WRITABLE_HANDLERS.add(key)
    logger.info(f"已将 handler 标记为可写: {key}")
    return True


def unregister_handler(source_type, model_type):
    """
    取消注册自定义 handler

    Args:
        source_type: 数据源类型
        model_type: 模型类型

    Returns:
        bool: 是否成功取消注册

    Example:
        >>> unregister_handler('custom_db', 'table')
    """
    key = f"{source_type}:{model_type}"

    removed = False
    if key in CUSTOM_HANDLERS:
        del CUSTOM_HANDLERS[key]
        removed = True

    if key in WRITABLE_HANDLERS:
        WRITABLE_HANDLERS.discard(key)

    if removed:
        logger.info(f"已取消注册 handler: {key}")
    else:
        logger.warning(f"Handler {key} 不存在，无法取消注册")

    return removed


def list_registered_handlers():
    """
    列出所有已注册的自定义 handlers

    Returns:
        dict: 包含所有注册信息的字典
        {
            'handlers': {key: handler_class, ...},
            'writable': [key1, key2, ...],
            'count': int
        }
    """
    return {
        'handlers': dict(CUSTOM_HANDLERS),
        'writable': sorted(list(WRITABLE_HANDLERS)),
        'count': len(CUSTOM_HANDLERS)
    }
