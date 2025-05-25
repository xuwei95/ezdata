from web_apps import db
from models import BaseModel
from sqlalchemy.dialects.mysql import LONGTEXT
from config import DB_TYPE


class ScreenProject(BaseModel):
    '''
    数据大屏
    '''
    __tablename__ = 'screen_project'
    id = db.Column(db.String(36), primary_key=True, comment='主键')
    project_name = db.Column(db.String(255), comment='项目名称')
    index_image = db.Column(db.String(255), default='', comment='首页图片')
    remarks = db.Column(db.String(255), default='', comment='项目介绍')
    state = db.Column(db.SmallInteger, default=-1, comment='项目状态[-1未发布,1发布]')
    if DB_TYPE == 'mysql':
        content = db.Column(LONGTEXT, default='{}', comment='项目内容')
    else:
        content = db.Column(db.TEXT, default='{}', comment='项目内容')


if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    db.session.flush()