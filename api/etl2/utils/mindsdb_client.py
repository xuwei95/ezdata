"""
独立的 Integrations 客户端

这个模块提供了一个独立的接口来使用 MindsDB integrations，无需依赖 MindsDB 的完整系统。
可以用于连接数据源、获取表信息、执行查询等操作。

使用示例:
    from standalone_client import IntegrationsClient
    
    # 创建客户端
    client = IntegrationsClient()
    
    # 连接到 PostgreSQL
    handler = client.create_handler(
        handler_type='postgres',
        connection_data={
            'host': 'localhost',
            'port': 5432,
            'user': 'postgres',
            'password': 'password',
            'database': 'mydb'
        }
    )
    
    # 检查连接
    status = handler.check_connection()
    print(f"连接状态: {status.success}")
    
    # 获取所有表
    tables = handler.get_tables()
    print(f"表列表: {tables.data_frame}")
    
    # 执行查询
    result = handler.native_query("SELECT * FROM users LIMIT 10")
    print(f"查询结果: {result.data_frame}")
    
    # 获取表的列信息
    columns = handler.get_columns('users')
    print(f"列信息: {columns.data_frame}")
    
    # 断开连接
    handler.disconnect()
"""

import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, Optional, List
import pandas as pd
from mindsdb.integrations.libs.base import BaseHandler, DatabaseHandler
from mindsdb.integrations.libs.response import HandlerResponse, HandlerStatusResponse, RESPONSE_TYPE
from mindsdb_sql_parser.ast.base import ASTNode
from mindsdb.utilities import log

logger = log.getLogger(__name__)


class IntegrationsClient:
    """
    独立的 Integrations 客户端
    
    提供直接使用 MindsDB integrations 的接口，无需依赖 MindsDB 的完整系统。
    """
    
    def __init__(self, handlers_base_path: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            handlers_base_path: handlers 的基础路径，默认为 mindsdb.integrations.handlers
        """
        if handlers_base_path is None:
            import mindsdb.integrations.handlers as handlers_module
            self.handlers_base_path = handlers_module.__path__[0]
        else:
            self.handlers_base_path = handlers_base_path
        
        self._handler_cache = {}
    
    def list_available_handlers(self) -> List[str]:
        """
        列出所有可用的 handler

        Returns:
            可用的 handler 名称列表
        """
        handlers_path = Path(self.handlers_base_path)
        handlers = []

        for handler_dir in handlers_path.iterdir():
            if handler_dir.is_dir() and not handler_dir.name.startswith('__'):
                # 检查是否有 __init__.py
                init_file = handler_dir / '__init__.py'
                if init_file.exists():
                    handlers.append(handler_dir.name)

        return sorted(handlers)

    def get_handler_type(self, handler_name: str) -> Optional[str]:
        """
        获取 handler 的类型（DATA 或 ML）

        Args:
            handler_name: handler 名称或文件夹名

        Returns:
            'DATA', 'ML' 或 None（如果无法确定）
        """
        try:
            handler_module = self._import_handler(handler_name)
            handler_type = getattr(handler_module, 'type', None)
            return handler_type
        except Exception as e:
            logger.warning(f"无法获取 handler '{handler_name}' 的类型: {e}")
            return None

    def list_data_handlers(self) -> List[str]:
        """
        列出所有 DATA 类型的 handler（可读写的数据源）

        Returns:
            DATA 类型 handler 名称列表
        """
        all_handlers = self.list_available_handlers()
        data_handlers = []

        for handler_name in all_handlers:
            handler_type = self.get_handler_type(handler_name)
            # 只包含 DATA 类型，排除 ML 类型
            if handler_type == 'data':
                data_handlers.append(handler_name)

        return sorted(data_handlers)

    def list_ml_handlers(self) -> List[str]:
        """
        列出所有 ML 类型的 handler（机器学习模型，不可读）

        Returns:
            ML 类型 handler 名称列表
        """
        all_handlers = self.list_available_handlers()
        ml_handlers = []

        for handler_name in all_handlers:
            handler_type = self.get_handler_type(handler_name)
            # 只包含 ML 类型
            if handler_type == 'ml':
                ml_handlers.append(handler_name)

        return sorted(ml_handlers)
    
    def get_handler_info(self, handler_type: str) -> Dict[str, Any]:
        """
        获取 handler 的信息
        
        Args:
            handler_type: handler 类型名称（如 'postgres', 'mysql' 等）
        
        Returns:
            handler 信息字典，包含 connection_args, description 等
        """
        try:
            handler_module = self._import_handler(handler_type)
            info = {
                'name': getattr(handler_module, 'name', handler_type),
                'title': getattr(handler_module, 'title', handler_type),
                'description': getattr(handler_module, 'description', ''),
                'version': getattr(handler_module, 'version', ''),
                'connection_args': getattr(handler_module, 'connection_args', {}),
                'connection_args_example': getattr(handler_module, 'connection_args_example', {}),
                'import_error': getattr(handler_module, 'import_error', None),
            }
            return info
        except Exception as e:
            logger.error(f"获取 handler 信息失败: {e}")
            return {'error': str(e)}
    
    def _find_handler_folder(self, handler_name: str) -> Optional[str]:
        """
        根据 handler 名称查找对应的文件夹名
        
        Args:
            handler_name: handler 名称（如 'mysql', 'postgres' 等）
        
        Returns:
            文件夹名（如 'mysql_handler', 'postgres_handler' 等），如果未找到则返回 None
        """
        handlers_path = Path(self.handlers_base_path)
        
        # 首先尝试直接匹配文件夹名
        if (handlers_path / handler_name).exists():
            return handler_name
        
        # 尝试匹配 handler_name + '_handler'
        folder_name = f"{handler_name}_handler"
        if (handlers_path / folder_name).exists():
            return folder_name
        
        # 遍历所有文件夹，查找匹配的 name
        for handler_dir in handlers_path.iterdir():
            if handler_dir.is_dir() and not handler_dir.name.startswith('__'):
                init_file = handler_dir / '__init__.py'
                if init_file.exists():
                    try:
                        # 尝试读取 __init__.py 中的 name
                        code = init_file.read_text()
                        # 简单查找 name = "xxx" 或 name = 'xxx'
                        import re
                        match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', code)
                        if match and match.group(1) == handler_name:
                            return handler_dir.name
                    except Exception:
                        pass
        
        return None
    
    def _import_handler(self, handler_type: str):
        """
        导入 handler 模块
        
        Args:
            handler_type: handler 类型名称（可以是文件夹名或 handler 的 name）
        
        Returns:
            handler 模块
        """
        if handler_type in self._handler_cache:
            return self._handler_cache[handler_type]
        
        # 首先尝试直接导入
        try:
            module_name = f"mindsdb.integrations.handlers.{handler_type}"
            handler_module = importlib.import_module(module_name)
            self._handler_cache[handler_type] = handler_module
            return handler_module
        except ImportError:
            # 如果直接导入失败，尝试查找对应的文件夹
            folder_name = self._find_handler_folder(handler_type)
            if folder_name:
                try:
                    module_name = f"mindsdb.integrations.handlers.{folder_name}"
                    handler_module = importlib.import_module(module_name)
                    self._handler_cache[handler_type] = handler_module
                    return handler_module
                except ImportError as e:
                    raise ImportError(f"无法导入 handler '{handler_type}' (尝试了文件夹 '{folder_name}'): {e}")
            else:
                raise ImportError(f"无法找到 handler '{handler_type}'")
    
    def create_handler(
        self,
        handler_type: str,
        connection_data: Dict[str, Any],
        name: Optional[str] = None,
        **kwargs
    ) -> BaseHandler:
        """
        创建并初始化一个 handler 实例
        
        Args:
            handler_type: handler 类型名称（可以是文件夹名如 'postgres_handler'，或 handler 的 name 如 'postgres'）
            connection_data: 连接数据字典，包含连接所需的所有参数
            name: handler 名称，默认为 handler 的 name 属性
            **kwargs: 其他传递给 handler 的参数
        
        Returns:
            BaseHandler 实例
        
        Raises:
            ImportError: 如果无法导入 handler
            ValueError: 如果 handler 类不存在或无法实例化
        """
        
        # 导入 handler 模块
        handler_module = self._import_handler(handler_type)
        
        # 检查是否有 import_error
        if hasattr(handler_module, 'import_error') and handler_module.import_error is not None:
            raise ImportError(
                f"Handler '{handler_type}' 导入失败: {handler_module.import_error}"
            )
        
        # 获取 Handler 类
        if not hasattr(handler_module, 'Handler') or handler_module.Handler is None:
            raise ValueError(f"Handler '{handler_type}' 没有定义 Handler 类")
        
        HandlerClass = handler_module.Handler
        
        # 检查 Handler 类是否是 BaseHandler 的子类
        if not issubclass(HandlerClass, BaseHandler):
            raise ValueError(
                f"Handler '{handler_type}' 的 Handler 类不是 BaseHandler 的子类"
            )
        
        # 如果没有指定 name，使用 handler 的 name 属性
        if name is None:
            name = getattr(handler_module, 'name', handler_type)
        
        # 准备初始化参数
        # 大多数 handler 需要 connection_data 参数
        init_kwargs = {
            'name': name,
            'connection_data': connection_data,
            **kwargs
        }
        
        # 检查 Handler 类的 __init__ 签名
        sig = inspect.signature(HandlerClass.__init__)
        params = sig.parameters
        
        # 如果 Handler 不接受 connection_data，尝试其他参数名
        if 'connection_data' not in params:
            # 有些 handler 可能使用其他参数名
            if 'connection_args' in params:
                init_kwargs['connection_args'] = connection_data
                del init_kwargs['connection_data']
            elif 'args' in params:
                init_kwargs['args'] = connection_data
                del init_kwargs['connection_data']
        
        # 创建 handler 实例
        try:
            handler = HandlerClass(**init_kwargs)
            return handler
        except Exception as e:
            raise ValueError(f"无法创建 handler 实例: {e}")
    
    def test_connection(
        self,
        handler_type: str,
        connection_data: Dict[str, Any],
        **kwargs
    ) -> HandlerStatusResponse:
        """
        测试连接是否成功
        
        Args:
            handler_type: handler 类型名称
            connection_data: 连接数据字典
            **kwargs: 其他传递给 handler 的参数
        
        Returns:
            HandlerStatusResponse 对象，包含连接状态信息
        """
        handler = self.create_handler(handler_type, connection_data, **kwargs)
        try:
            # 尝试连接
            handler.connect()
            # 检查连接
            status = handler.check_connection()
            return status
        except Exception as e:
            return HandlerStatusResponse(
                success=False,
                error_message=f"连接失败: {str(e)}"
            )
        finally:
            # 断开连接
            try:
                handler.disconnect()
            except:
                pass


class StandaloneHandler:
    """
    Handler 的独立包装类，提供更友好的接口
    """
    
    def __init__(self, handler: BaseHandler):
        """
        初始化包装类
        
        Args:
            handler: BaseHandler 实例
        """
        self._handler = handler
    
    def connect(self) -> bool:
        """
        连接到数据源
        
        Returns:
            连接是否成功
        """
        try:
            result = self._handler.connect()
            if result is None:
                # 如果 connect() 返回 None，检查 is_connected 状态
                return self._handler.is_connected
            return bool(result)
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False
    
    def disconnect(self) -> None:
        """
        断开连接
        """
        try:
            self._handler.disconnect()
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
    
    def check_connection(self) -> Dict[str, Any]:
        """
        检查连接状态
        
        Returns:
            包含连接状态的字典
        """
        try:
            status = self._handler.check_connection()
            return {
                'success': status.success,
                'error_message': status.error_message,
                'redirect_url': getattr(status, 'redirect_url', None),
            }
        except Exception as e:
            return {
                'success': False,
                'error_message': str(e),
            }
    
    def native_query(self, query: str, params: Optional[List] = None) -> pd.DataFrame:
        """
        执行原生查询
        
        Args:
            query: 查询字符串（SQL 或其他原生格式）
            params: 查询参数（可选）
        
        Returns:
            pandas DataFrame，包含查询结果
        
        Raises:
            Exception: 如果查询失败
        """
        try:
            if params is not None:
                # 如果 handler 支持 params 参数
                if 'params' in inspect.signature(self._handler.native_query).parameters:
                    response = self._handler.native_query(query, params=params)
                else:
                    response = self._handler.native_query(query)
            else:
                response = self._handler.native_query(query)
            
            if response.resp_type == RESPONSE_TYPE.ERROR:
                raise Exception(
                    f"查询失败: {response.error_message}"
                )
            
            if response.resp_type == RESPONSE_TYPE.TABLE:
                return response.data_frame
            elif response.resp_type == RESPONSE_TYPE.OK:
                # 返回空 DataFrame，但包含受影响的行数
                return pd.DataFrame({
                    'affected_rows': [response.affected_rows or 0]
                })
            else:
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            raise
    
    def query(self, query: ASTNode) -> pd.DataFrame:
        """
        执行 AST 查询
        
        Args:
            query: ASTNode 对象（SQL 解析后的抽象语法树）
        
        Returns:
            pandas DataFrame，包含查询结果
        
        Raises:
            Exception: 如果查询失败
        """
        try:
            response = self._handler.query(query)
            
            if response.resp_type == RESPONSE_TYPE.ERROR:
                raise Exception(
                    f"查询失败: {response.error_message}"
                )
            
            if response.resp_type == RESPONSE_TYPE.TABLE:
                return response.data_frame
            elif response.resp_type == RESPONSE_TYPE.OK:
                return pd.DataFrame({
                    'affected_rows': [response.affected_rows or 0]
                })
            else:
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            raise
    
    def get_tables(self) -> pd.DataFrame:
        """
        获取所有表的信息
        
        Returns:
            pandas DataFrame，包含表信息（至少包含 TABLE_NAME 列）
        """
        try:
            response = self._handler.get_tables()
            
            if response.resp_type == RESPONSE_TYPE.ERROR:
                raise Exception(
                    f"获取表信息失败: {response.error_message}"
                )
            
            if response.resp_type == RESPONSE_TYPE.TABLE:
                return response.data_frame
            else:
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"获取表信息失败: {e}")
            raise
    
    def get_columns(self, table_name: str) -> pd.DataFrame:
        """
        获取指定表的列信息
        
        Args:
            table_name: 表名
        
        Returns:
            pandas DataFrame，包含列信息（至少包含 COLUMN_NAME 列）
        """
        try:
            response = self._handler.get_columns(table_name)
            if response.resp_type == RESPONSE_TYPE.ERROR:
                raise Exception(
                    f"获取列信息失败: {response.error_message}"
                )
            
            if response.resp_type == RESPONSE_TYPE.TABLE:
                return response.data_frame
            else:
                return pd.DataFrame()
        except Exception as e:
            logger.error(f"获取列信息失败: {e}")
            raise

    def meta_get_columns(self, table_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        获取表的列元数据信息（更详细的列信息）

        Args:
            table_names: 表名列表，如果为 None 则获取所有表的列信息

        Returns:
            pandas DataFrame，包含列元数据信息：
            - TABLE_NAME (str): 表名
            - COLUMN_NAME (str): 列名
            - DATA_TYPE (str): 数据类型
            - COLUMN_DESCRIPTION (str): 列描述（可选）
            - IS_NULLABLE (bool): 是否可为空（可选）
            - COLUMN_DEFAULT (str): 默认值（可选）
        """
        try:
            # 检查 handler 是否有 meta_get_columns 方法
            if hasattr(self._handler, 'meta_get_columns'):
                response = self._handler.meta_get_columns(table_names)
                if response.resp_type == RESPONSE_TYPE.ERROR:
                    raise Exception(
                        f"获取列元数据信息失败: {response.error_message}"
                    )

                if response.resp_type == RESPONSE_TYPE.TABLE:
                    return response.data_frame
                else:
                    return pd.DataFrame()
            else:
                # 如果 handler 不支持 meta_get_columns，回退到逐个获取列信息
                logger.warning(f"Handler 不支持 meta_get_columns 方法，使用 get_columns 回退")

                # 如果没有指定表名，先获取所有表
                if table_names is None:
                    tables_df = self.get_tables()
                    if tables_df.empty:
                        return pd.DataFrame()

                    # 找到表名列
                    table_col = None
                    for col in ['TABLE_NAME', 'table_name', 'name', 'Name']:
                        if col in tables_df.columns:
                            table_col = col
                            break

                    if table_col:
                        table_names = tables_df[table_col].tolist()
                    else:
                        return pd.DataFrame()

                # 逐个获取表的列信息并合并
                all_columns = []
                for table_name in table_names:
                    try:
                        columns_df = self.get_columns(str(table_name))
                        if not columns_df.empty:
                            # 确保有 TABLE_NAME 列
                            if 'TABLE_NAME' not in columns_df.columns:
                                columns_df['TABLE_NAME'] = str(table_name)
                            all_columns.append(columns_df)
                    except Exception as e:
                        logger.warning(f"获取表 {table_name} 的列信息失败: {e}")
                        continue

                if all_columns:
                    return pd.concat(all_columns, ignore_index=True)
                else:
                    return pd.DataFrame()

        except Exception as e:
            logger.error(f"获取列元数据信息失败: {e}")
            raise
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


# 便捷函数
def create_handler(
    handler_type: str,
    connection_data: Dict[str, Any],
    name: Optional[str] = None,
    **kwargs
) -> StandaloneHandler:
    """
    创建并返回一个独立的 handler 包装实例
    
    Args:
        handler_type: handler 类型名称
        connection_data: 连接数据字典
        name: handler 名称
        **kwargs: 其他参数
    
    Returns:
        StandaloneHandler 实例
    """
    client = IntegrationsClient()
    handler = client.create_handler(handler_type, connection_data, name, **kwargs)
    return StandaloneHandler(handler)

