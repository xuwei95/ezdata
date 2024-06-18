'''
llm数据模型
'''
from web_apps import db
from models import BaseModel


class ChatHistory(BaseModel):
    '''
    对话历史表
    '''
    __tablename__ = 'llm_chat_history'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    user_id = db.Column(db.String(200), nullable=True, default='', comment='用户id')
    user_name = db.Column(db.String(100), nullable=True, default='', comment='用户名')
    content = db.Column(db.Text, nullable=True, default='{}', comment='内容')


if __name__ == '__main__':
    from web_apps import app
    with app.app_context():
        db.create_all()
        db.session.commit()
        db.session.flush()