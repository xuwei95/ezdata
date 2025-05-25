import pymysql
import os
import time
# 导入MySQL数据库连接配置
from config import DB_HOST, DB_PORT, DB_USER, DB_PWD, DB_NAME, SYS_CONF
from utils.cache_utils import set_key_exp, get_key_value
from utils.common_utils import gen_uuid


# 要检查的数据库名称和表名称
TABLE_NAME = "sys_user"
uuid = gen_uuid()
init_key = 'ezdata_init'
# 加锁，防止其他进程并发初始化
set_key_exp(init_key, uuid, exp_time=60, nx=True)
# SQL文件路径
SQL_FILE = os.path.join(os.path.dirname(__file__), "sql", "ezdata.sql")


def init_db():
    '''
    检查数据库，不存在则新建
    '''
    try:
        # 连接MySQL数据库
        cnx = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PWD)
        # 创建游标对象
        cursor = cnx.cursor()
        # 检查数据库是否存在，如果不存在则创建数据库
        cursor.execute("SHOW DATABASES")
        databases = [database[0] for database in cursor]
        if DB_NAME not in databases:
            init_value = get_key_value(init_key)
            if init_value is not None and init_value.decode() == uuid:
                cursor.execute(f"CREATE DATABASE {DB_NAME}  CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
                print(f'创建数据库{DB_NAME}')
        # 关闭连接
        cursor.close()
        cnx.close()
        return True
    except Exception as e:
        print(f"初始化数据库异常{e}")
        return False


def init_tables():
    '''
    初始化表和数据
    '''
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PWD,
            database=DB_NAME
        )
        # 创建游标对象
        cursor = connection.cursor()
        # 检查是否存在 sys_user 表
        table_exists_query = f"SHOW TABLES LIKE '{TABLE_NAME}'"
        cursor.execute(table_exists_query)
        result = cursor.fetchone()
        if not result:
            print('开始执行初始化sql')
            init_value = get_key_value(init_key)
            if init_value is not None and init_value.decode() == uuid:
                print('执行初始化sql')
                # 读取SQL文件内容
                with open(SQL_FILE, "r", encoding="utf-8") as file:
                    sql_script = file.read()
                # 执行SQL脚本
                for query in sql_script.split(';\n'):
                    print(query)
                    if query and query.strip() != '':
                        cursor.execute(query)
                connection.commit()
        # 关闭连接
        cursor.close()
        connection.close()
        return True
    except Exception as e:
        print(f"初始化表和数据异常{e}")
        return False


def check_storge():
    try:
        if SYS_CONF.get('STORAGE_TYPE') == 's3':
            bucket_name = SYS_CONF.get('S3_BUCKET_NAME')
            from utils.storage_utils import storage
            s3_client = storage.storage_runner.client
            try:
                s3_client.head_bucket(Bucket=bucket_name)
            except:
                s3_client.create_bucket(Bucket=bucket_name)
    except Exception as e:
        print(f"初始化存储异常{e}")
        return False
    return True


if __name__ == '__main__':
    retry_num = 3
    retry = 1
    flag = True
    while retry < retry_num:
        flag = init_db() and flag
        flag = init_tables() and flag
        flag = check_storge() and flag
        if flag:
            break
        time.sleep(5)
        retry += 1
        print(f"第{retry}次初始化")
