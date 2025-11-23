'''
测试数据模型
'''
from web_apps import db
import datetime


class Test(db.Model):
    '''
    test表
    '''
    __tablename__ = 'test'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    create_by = db.Column(db.String(100), nullable=True, default='', comment='创建者')
    create_time = db.Column(db.TIMESTAMP, nullable=True, server_default=db.text('CURRENT_TIMESTAMP'), comment='创建时间')
    update_by = db.Column(db.String(100), nullable=True, default='', comment='修改者')
    update_time = db.Column(db.TIMESTAMP, nullable=True, server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='修改时间')
    del_flag = db.Column(db.SmallInteger, nullable=True, default=0, comment='软删除标记')
    sort_no = db.Column(db.Float, nullable=True, default=1, comment='排序字段')
    description = db.Column(db.Text, nullable=True, default='', comment='简介描述')
    test = db.Column(db.Text, nullable=True, default='', comment='测试字段')
      
    def to_dict(self, data_type='str'):
        '''
        转为字典
        :return:
        '''
        value = {}
        for column in self.__table__.columns:
            attribute = getattr(self, column.name)
            if isinstance(attribute, datetime.datetime) and data_type == 'str':
                attribute = str(attribute)
            value[column.name] = attribute
        return value
        

if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    db.session.flush()
