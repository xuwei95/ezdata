# Integrations 独立客户端

这个模块提供了一个独立的接口来使用 MindsDB integrations，无需依赖 MindsDB 的完整系统。可以用于连接数据源、获取表信息、执行查询等操作。

## 功能特性

- ✅ 直接创建和初始化 handler
- ✅ 连接数据源（数据库、API 等）
- ✅ 获取数据表信息
- ✅ 执行查询（原生 SQL 或 AST）
- ✅ 获取表的列信息
- ✅ 测试连接
- ✅ 列出所有可用的 handlers
- ✅ 上下文管理器支持

## 快速开始

### 基本使用

```python
from mindsdb.integrations.standalone_client import create_handler

# 创建 PostgreSQL handler
# 注意: handler_type 可以是文件夹名（如 'postgres_handler'）或 handler 的 name（如 'postgres'）
handler = create_handler(
    handler_type='postgres',  # 或 'postgres_handler'
    connection_data={
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'password',
        'database': 'mydb'
    }
)

# 连接
handler.connect()

# 检查连接状态
status = handler.check_connection()
print(f"连接状态: {status}")

# 获取所有表
tables = handler.get_tables()
print(f"表列表: {tables}")

# 执行查询
result = handler.native_query("SELECT * FROM users LIMIT 10")
print(f"查询结果: {result}")

# 获取表的列信息
columns = handler.get_columns('users')
print(f"列信息: {columns}")

# 断开连接
handler.disconnect()
```

### 使用上下文管理器

```python
from mindsdb.integrations.standalone_client import create_handler

handler = create_handler(
    handler_type='postgres',  # 或 'postgres_handler'
    connection_data={
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'password',
        'database': 'mydb'
    }
)

# 使用上下文管理器自动管理连接
with handler:
    tables = handler.get_tables()
    result = handler.native_query("SELECT * FROM users LIMIT 10")
    print(result)
```

### 使用客户端类

```python
from mindsdb.integrations.standalone_client import IntegrationsClient

# 创建客户端
client = IntegrationsClient()

# 列出所有可用的 handlers
handlers = client.list_available_handlers()
print(f"可用的 handlers: {handlers}")

# 获取 handler 信息
info = client.get_handler_info('postgres')  # 或 'postgres_handler'
print(f"Handler 信息: {info}")

# 创建 handler
handler = client.create_handler(
    handler_type='postgres',  # 或 'postgres_handler'
    connection_data={
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'password',
        'database': 'mydb'
    }
)

# 测试连接
status = client.test_connection(
    handler_type='postgres',  # 或 'postgres_handler'
    connection_data={
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'password',
        'database': 'mydb'
    }
)
print(f"连接测试: {status.success}")
```

## API 参考

### IntegrationsClient

主要的客户端类，用于管理 handlers。

#### 方法

- `list_available_handlers() -> List[str]`: 列出所有可用的 handler 名称
- `get_handler_info(handler_type: str) -> Dict[str, Any]`: 获取 handler 的信息
- `create_handler(handler_type: str, connection_data: Dict[str, Any], name: Optional[str] = None, **kwargs) -> BaseHandler`: 创建 handler 实例
- `test_connection(handler_type: str, connection_data: Dict[str, Any], **kwargs) -> HandlerStatusResponse`: 测试连接

### StandaloneHandler

Handler 的独立包装类，提供更友好的接口。

#### 方法

- `connect() -> bool`: 连接到数据源
- `disconnect() -> None`: 断开连接
- `check_connection() -> Dict[str, Any]`: 检查连接状态
- `native_query(query: str, params: Optional[List] = None) -> pd.DataFrame`: 执行原生查询
- `query(query: ASTNode) -> pd.DataFrame`: 执行 AST 查询
- `get_tables() -> pd.DataFrame`: 获取所有表的信息
- `get_columns(table_name: str) -> pd.DataFrame`: 获取指定表的列信息

#### 上下文管理器

`StandaloneHandler` 支持上下文管理器，可以自动管理连接：

```python
with handler:
    # 自动连接
    tables = handler.get_tables()
    # 自动断开连接
```

### 便捷函数

- `create_handler(handler_type: str, connection_data: Dict[str, Any], name: Optional[str] = None, **kwargs) -> StandaloneHandler`: 创建并返回一个独立的 handler 包装实例

## 支持的 Handlers

所有 MindsDB integrations 中的 handlers 都可以使用，包括：

### 数据库 Handlers

- PostgreSQL (`postgres` 或 `postgres_handler`)
- MySQL (`mysql` 或 `mysql_handler`)
- SQLite (`sqlite` 或 `sqlite_handler`)
- MongoDB (`mongodb` 或 `mongodb_handler`)
- Redis (`redis` 或 `redis_handler`)
- 等等...

### API Handlers

- GitHub (`github_handler`)
- Slack (`slack_handler`)
- Twitter (`twitter_handler`)
- 等等...

### 向量数据库 Handlers

- ChromaDB (`chromadb_handler`)
- Pinecone (`pinecone_handler`)
- Weaviate (`weaviate_handler`)
- 等等...

完整列表请使用 `client.list_available_handlers()` 查看。

## 连接参数

每个 handler 的连接参数可能不同。可以使用 `get_handler_info()` 方法查看特定 handler 所需的连接参数：

```python
client = IntegrationsClient()
info = client.get_handler_info('postgres_handler')
print(info['connection_args'])
```

## 示例

更多示例请参考 `standalone_client_example.py` 文件。

## 注意事项

1. **依赖项**: 确保已安装所需的依赖项。某些 handlers 可能需要额外的 Python 包。
2. **连接参数**: 不同 handler 的连接参数可能不同，请参考相应的文档。
3. **错误处理**: 建议使用 try-except 块来处理可能的连接或查询错误。
4. **资源管理**: 使用上下文管理器或确保手动调用 `disconnect()` 来释放资源。

## 常见问题

### Q: 如何知道某个 handler 需要哪些连接参数？

A: 使用 `get_handler_info()` 方法：

```python
client = IntegrationsClient()
info = client.get_handler_info('postgres')  # 或 'postgres_handler'
print(info['connection_args'])
print(info['connection_args_example'])
```

### Q: 如何测试连接是否成功？

A: 使用 `test_connection()` 方法：

```python
client = IntegrationsClient()
status = client.test_connection('postgres', connection_data)  # 或 'postgres_handler'
if status.success:
    print("连接成功")
else:
    print(f"连接失败: {status.error_message}")
```

### Q: 查询返回的是什么格式？

A: 查询返回的是 pandas DataFrame，可以直接使用 pandas 的方法进行处理。

### Q: 如何执行带参数的查询？

A: 使用 `native_query()` 方法的 `params` 参数：

```python
result = handler.native_query(
    "SELECT * FROM users WHERE id = ?",
    params=[(1,)]
)
```

## 许可证

与 MindsDB 主项目相同。

