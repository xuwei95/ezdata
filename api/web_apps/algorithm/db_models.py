'''
算法管理数据模型
'''
from web_apps import db
from models import BaseModel


class Algorithm(BaseModel):
    '''
    算法表
    '''
    __tablename__ = 'algorithm'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    name = db.Column(db.String(200), nullable=True, default='', comment='算法名称')
    code = db.Column(db.String(200), nullable=True, default='', comment='算法编码')
    type = db.Column(db.String(200), nullable=True, default='etl_algorithm', comment='算法类型')
    form_type = db.Column(db.SmallInteger, nullable=True, default=1, comment='表单类型')
    component = db.Column(db.String(500), nullable=True, default='', comment='算法组件')
    params = db.Column(db.Text, nullable=True, default='{}', comment='算法配置')
    status = db.Column(db.SmallInteger, nullable=True, default=0, comment='状态')
    

if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    db.session.flush()
