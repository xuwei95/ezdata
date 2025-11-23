"""
Integrations 独立客户端使用示例

这个文件展示了如何使用独立的 integrations 客户端来连接数据源、
获取表信息、执行查询等操作。
"""
from mindsdb.integrations.standalone_client import IntegrationsClient, create_handler, StandaloneHandler


def example_basic_usage():
    """基本使用示例"""
    print("=" * 60)
    print("基本使用示例")
    print("=" * 60)
    
    # 创建客户端
    client = IntegrationsClient()
    
    # 列出所有可用的 handler
    handlers = client.list_available_handlers()
    print(f"\n可用的 handlers 数量: {len(handlers)}")
    print(f"前 10 个 handlers: {handlers[:10]}")
    
    # 获取 PostgreSQL handler 的信息
    # 注意: 可以使用文件夹名或 handler 的 name
    postgres_info = client.get_handler_info('newsapi')  # 或 'postgres_handler'
    print(f"\nPostgreSQL handler 信息:")
    print(f"  名称: {postgres_info.get('name')}")
    print(f"  标题: {postgres_info.get('title')}")
    print(f"  连接参数: {list(postgres_info.get('connection_args', {}).keys())}")


def example_postgres_connection():
    """PostgreSQL 连接示例"""
    print("\n" + "=" * 60)
    print("PostgreSQL 连接示例")
    print("=" * 60)
    
    # 连接数据
    connection_data = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'your_password',
        'database': 'your_database'
    }
    
    try:
        # 方式 1: 使用便捷函数
        # 注意: handler_type 可以是文件夹名（如 'postgres_handler'）或 handler 的 name（如 'postgres'）
        handler = create_handler(
            handler_type='postgres',  # 或 'postgres_handler'
            connection_data=connection_data,
            name='my_postgres'
        )
        
        # 连接
        if handler.connect():
            print("\n✓ 连接成功")
            
            # 检查连接状态
            status = handler.check_connection()
            print(f"连接状态: {status}")
            
            # 获取所有表
            tables = handler.get_tables()
            print(f"\n表列表 (共 {len(tables)} 个表):")
            if not tables.empty:
                print(tables.head())
            
            # 如果有表，获取第一个表的列信息
            if not tables.empty:
                first_table = tables.iloc[0]['TABLE_NAME']
                print(f"\n表 '{first_table}' 的列信息:")
                columns = handler.get_columns(first_table)
                if not columns.empty:
                    print(columns.head())
            
            # 执行查询
            print("\n执行查询: SELECT version()")
            result = handler.native_query("SELECT version()")
            print(result)
            
            # 断开连接
            handler.disconnect()
            print("\n✓ 已断开连接")
        else:
            print("\n✗ 连接失败")
    
    except Exception as e:
        print(f"\n✗ 错误: {e}")


def example_mysql_connection():
    """MySQL 连接示例"""
    print("\n" + "=" * 60)
    print("MySQL 连接示例")
    print("=" * 60)
    
    connection_data = {
        "host": "124.220.57.72",
        "port": 3306,
        "database": "ezdata",
        "user": "root",
        "password": "ezdata123"
    }
    
    try:
        # 方式 2: 使用客户端类
        client = IntegrationsClient()
        handler = client.create_handler(
            handler_type='mysql',  # 或 'mysql_handler'
            connection_data=connection_data
        )
        
        # 使用上下文管理器
        with StandaloneHandler(handler) as h:
            # 检查连接
            status = h.check_connection()
            print(f"连接状态: {status}")
            
            # 获取表列表
            tables = h.get_tables()
            print(f"\n表列表 (共 {len(tables)} 个表):")
            if not tables.empty:
                print(tables[['TABLE_NAME']].head())
            
            # 执行查询
            result = h.native_query("SHOW TABLES")
            print(f"\n查询结果:")
            print(result)
    
    except Exception as e:
        print(f"\n✗ 错误: {e}")


def example_sqlite_connection():
    """SQLite 连接示例"""
    print("\n" + "=" * 60)
    print("SQLite 连接示例")
    print("=" * 60)
    
    connection_data = {
        'db_file': 'example.db'  # SQLite 数据库文件路径
    }
    
    try:
        handler = create_handler(
            handler_type='sqlite_handler',
            connection_data=connection_data
        )
        
        with handler:
            # 获取表列表
            tables = handler.get_tables()
            print(f"\n表列表 (共 {len(tables)} 个表):")
            if not tables.empty:
                print(tables)
            
            # 执行查询
            result = handler.native_query("SELECT name FROM sqlite_master WHERE type='table'")
            print(f"\n查询结果:")
            print(result)
    
    except Exception as e:
        print(f"\n✗ 错误: {e}")


def example_test_connection():
    """测试连接示例"""
    print("\n" + "=" * 60)
    print("测试连接示例")
    print("=" * 60)
    
    client = IntegrationsClient()
    
    # 测试 PostgreSQL 连接
    connection_data = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'your_password',
        'database': 'your_database'
    }
    
    status = client.test_connection('postgres', connection_data)  # 或 'postgres_handler'
    print(f"连接测试结果:")
    print(f"  成功: {status.success}")
    if not status.success:
        print(f"  错误: {status.error_message}")


if __name__ == '__main__':
    # 运行示例
    example_basic_usage()
    
    # 注意: 以下示例需要实际的数据库连接，请根据实际情况修改连接参数
    # example_postgres_connection()
    # example_mysql_connection()
    # example_sqlite_connection()
    # example_test_connection()

