'''
数据源管理数据模型
'''
from web_apps import db
from models import BaseModel


class DataSource(BaseModel):
    '''
    数据源表
    '''
    __tablename__ = 'datasource'
    id = db.Column(db.String(36), primary_key=True, nullable=False, comment='ID')
    name = db.Column(db.String(200), nullable=False, default='', comment='名称')
    type = db.Column(db.String(200), nullable=False, default='mysql', comment='类型')
    conn_conf = db.Column(db.Text, nullable=False, default='{}', comment='连接配置')
    status = db.Column(db.Integer, nullable=True, default=0, comment='状态')
    ext_params = db.Column(db.Text, nullable=True, default='{}', comment='额外参数')


if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    db.session.flush()
