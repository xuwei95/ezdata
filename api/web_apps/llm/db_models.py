'''
llm数据模型
'''
from web_apps import db
from models import BaseModel
from sqlalchemy.dialects.mysql import LONGTEXT
from config import DB_TYPE
import datetime
import json


class Conversation(BaseModel):
    """会话表"""
    __tablename__ = 'llm_conversation'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    user_id = db.Column(db.Integer, nullable=True, comment='用户id')
    app_id = db.Column(db.String(36), nullable=False, default='', index=True, comment='所属对话appid')
    user_name = db.Column(db.String(100), nullable=True, default='', comment='用户名')
    core_memory = db.Column(db.TEXT, default='', comment='核心记忆')
    mode = db.Column(db.String(100), nullable=True, default='console', comment='类型 console-平台， api-接口')


class ChatApp(BaseModel):
    '''
    ai对话应用
    '''
    __tablename__ = 'llm_chat_app'
    id = db.Column(db.String(36), primary_key=True, comment='主键')
    name = db.Column(db.String(255), comment='名称')
    icon = db.Column(db.String(500), default='', comment='图标')
    type = db.Column(db.String(200), nullable=True, default='', comment='类型')
    state = db.Column(db.SmallInteger, default=0, comment='状态[0未发布,1已发布]')
    depart_list = db.Column(db.Text, default='[]', comment='关联部门列表')
    if DB_TYPE == 'mysql':
        chat_config = db.Column(LONGTEXT, default='{}', comment='对话配置')
    else:
        chat_config = db.Column(db.TEXT, default='{}', comment='对话配置')


class ChatAppToken(BaseModel):
    '''
    对话app接口apikey表
    '''
    __tablename__ = 'llm_chat_app_token'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    app_id = db.Column(db.String(36), nullable=False, default='', index=True, comment='所属对话appid')
    api_key = db.Column(db.String(36), nullable=False, default='', index=True, comment='api_key')
    valid_time = db.Column(db.BIGINT, default=0, comment='有效期限')
    apply_user_id = db.Column(db.Integer, comment='申请人id')
    apply_user = db.Column(db.String(100), comment='申请人')
    apply_time = db.Column(db.BIGINT, comment='申请时间')
    apply_time_length = db.Column(db.String(50), default='forever', comment='申请时长')
    status = db.Column(db.SmallInteger, nullable=False, default=1, comment='状态0禁用1启用')

    def to_dict(self, date_type='str'):
        '''
        转为字典
        :return:
        '''
        value = {}
        for column in self.__table__.columns:
            attribute = getattr(self, column.name)
            if isinstance(attribute, datetime.datetime) and date_type == 'str':
                attribute = str(attribute)
            value[column.name] = attribute
        return value

class LLMTool(BaseModel):
    """LLM工具配置表"""
    __tablename__ = 'llm_tools'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    name = db.Column(db.String(255), nullable=False, comment='工具名称')
    code = db.Column(db.String(100), nullable=False, unique=True, comment='工具代码')
    type = db.Column(db.String(50), nullable=False, comment='工具类型: mcp')
    description = db.Column(db.TEXT, default='', comment='工具描述')
    args = db.Column(db.TEXT, default='{}', comment='工具配置JSON')
    status = db.Column(db.SmallInteger, default=1, comment='状态: 0禁用 1启用')

    def to_dict(self):
        '''转为字典'''
        value = {}
        for column in self.__table__.columns:
            attribute = getattr(self, column.name)
            if isinstance(attribute, datetime.datetime):
                attribute = str(attribute)
            # 解析args JSON字段
            if column.name == 'args':
                try:
                    if isinstance(attribute, str):
                        value[column.name] = json.loads(attribute)
                    else:
                        value[column.name] = attribute
                except:
                    value[column.name] = attribute if attribute else {}
            else:
                value[column.name] = attribute
        return value

if __name__ == '__main__':
    from web_apps import app
    with app.app_context():
        db.create_all()
        db.session.commit()
        db.session.flush()