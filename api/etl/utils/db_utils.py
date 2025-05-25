'''
数据库sqlalchemy orm相关工具类
'''
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Text, SmallInteger, DateTime, TIMESTAMP, Float
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine, Table, MetaData
from sshtunnel import SSHTunnelForwarder
Base = declarative_base()


class BaseModel(Base):
    '''
    数据库orm模型基类
    '''
    __abstract__ = True


def transColumn(i, db_type='mysql'):
    '''
    转换表字段，归为统一类型
    '''
    if i['type'].startswith('VARCHAR'):
        i['type'] = 'VARCHAR'
    if db_type == 'clickhouse':
        if i['type'].startswith('FixedString'):
            i['type'] = 'FixedString'
        if i['type'].startswith('Int'):
            i['type'] = 'Int'
        if i['type'].startswith('UInt'):
            i['type'] = 'UInt'
        if i['type'].startswith('Enum'):
            i['type'] = 'Enum'
        if i['type'] == 'FLOAT':
            i['type'] = 'Float'
    return i


def getColumn(i, db_type='mysql'):
    '''
    根据字典获取列参数，组成orm模型字段
    :param i:
    :return:
    '''
    if 'nullable' in i.keys():
        i['nullable'] = i['nullable'] == 1
    else:
        i['nullable'] = True
    if 'is_primary_key' in i:
        i['is_primary_key'] = i['is_primary_key'] == 1
    else:
        i['is_primary_key'] = False
    if 'length' not in i:
        i['length'] = '0'
    if 'type' not in i:
        obj = Column(Text, nullable=True)
    elif i['type'] in ['varchar', 'FixedString']:
        obj = Column(String(i['length']), primary_key=i['is_primary_key'], nullable=i['nullable'])
    elif i['type'] in ['text', 'String']:
        obj = Column(Text, nullable=i['nullable'])
    elif i['type'] == 'longtext':
        if db_type == 'mysql':
            obj = Column(LONGTEXT, nullable=i['nullable'])
        else:
            obj = Column(Text, nullable=i['nullable'])
    elif i['type'] in ['int', 'Int']:
        obj = Column(Integer, primary_key=i['is_primary_key'], nullable=i['nullable'])
    elif i['type'] in ['float', 'Float']:
        obj = Column(Float, nullable=i['nullable'])
    elif i['type'] == 'smallint':
        obj = Column(SmallInteger, nullable=i['nullable'])
    elif i['type'] in ['datetime', 'Date', 'DateTime']:
        obj = Column(DateTime, nullable=i['nullable'])
    elif i['type'] in ['timpstamp']:
        obj = Column(TIMESTAMP, nullable=i['nullable'])
    else:
        obj = Column(Text, nullable=True)
    if 'field_name' in i:
        obj.comment = i['field_name']
    return obj


def create_orm_table(obj_db, params, table_args=None):
    '''
    使用orm创建表
    :return:
    '''
    table_name = params['table_name']
    field_arr = params['field_arr']

    class Model(BaseModel):
        __tablename__ = table_name
        if table_args is not None:
            __table_args__ = table_args

    for i in field_arr:
        setattr(Model, i['field_value'], getColumn(i))
    from sqlalchemy.schema import CreateTable
    print(CreateTable(Model.__table__))
    if table_name not in obj_db.table_names():
        Model.__table__.create(obj_db)
    return Model


def get_database_engine(db_info, res_type='engine'):
    '''
    获取数据库链接引擎
    :param db_obj: 数据库模型
    :return:
    '''
    ENGINE_DICT = {
        'mysql': 'mysql+pymysql',
        'pgsql': 'postgresql+psycopg2',
        'sqlserver': 'mssql+pymssql',
        'oracle': 'oracle+cx_oracle',
        'clickhouse': 'clickhouse',
        'hive': 'hive'
    }
    DB_TYPE = db_info.get('type')
    db_engine_url = None
    if DB_TYPE in ENGINE_DICT:
        DB_USER = db_info.get('username')
        DB_PWD = db_info.get('password', '')
        DB_HOST = db_info.get('host')
        DB_PORT = db_info.get('port')
        DB_NAME = db_info.get('database_name')
        if db_info.get('use_tunnel'):
            ssh_info = db_info.get('ssh_tunnel')
            print(ssh_info)
            ssh_host = ssh_info['ssh_host']
            ssh_port = ssh_info['ssh_port']
            ssh_user = ssh_info['ssh_user']
            ssh_passwd = ssh_info['ssh_passwd']
            server = SSHTunnelForwarder(
                (ssh_host, int(ssh_port)),
                ssh_username=ssh_user,
                ssh_password=ssh_passwd,
                remote_bind_address=(DB_HOST, int(DB_PORT))
            )
            server.start()
            DB_PORT = str(server.local_bind_port)
            # server.close()
        if DB_TYPE == 'hive':
            if DB_PWD == '':
                db_engine_url = f"{ENGINE_DICT[DB_TYPE]}://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            else:
                db_engine_url = f"{ENGINE_DICT[DB_TYPE]}://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?auth=LDAP"
        else:
            db_engine_url = f"{ENGINE_DICT[DB_TYPE]}://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    if res_type == 'engine_url':
        return db_engine_url
    if db_engine_url is not None:
        db_engine = create_engine(db_engine_url)
        return db_engine
    else:
        return None


def get_database_model(table_name, db_engine=None, db_type='mysql'):
    '''
    根据表名反射出database数据库中的表模型
    :param table_name:
    :return:
    '''
    try:
        DBSession = sessionmaker(bind=db_engine)
        session = DBSession()
        if db_type in ['oracle', 'clickhouse', 'hive']:
            metadata = MetaData()
            table = Table(table_name, metadata, autoload_with=db_engine)
            return session, table
        else:
            metadata = MetaData()
            metadata.reflect(db_engine, only=[table_name])
            Base = automap_base(metadata=metadata)  # 从metadata中生成所有的映射关系为Base
            Base.prepare()  # 设置被映射的类和关系
            print(Base.classes)
            model = getattr(Base.classes, table_name)  # 将表映射到类上
            return session, model
    except Exception as e:
        print(e)
        return False, False





