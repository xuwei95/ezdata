'''
数据模型模块
'''
from web_apps import db
from models import BaseModel


class DataModel(BaseModel):
    '''
    数据模型表
    '''
    __tablename__ = 'datamodel'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    name = db.Column(db.String(200), nullable=False, default='', comment='名称')
    datasource_id = db.Column(db.String(36), nullable=True, default='', comment='数据源id')
    type = db.Column(db.String(200), nullable=True, default='', comment='类型')
    status = db.Column(db.SmallInteger, nullable=False, default=0, comment='模型状态 0未建立，1已建立')
    model_conf = db.Column(db.Text, nullable=True, default='{}', comment='模型配置')
    can_interface = db.Column(db.SmallInteger, nullable=True, default=1, comment='是否可封装查询接口')
    depart_list = db.Column(db.Text, default='[]', comment='关联部门列表')
    ext_params = db.Column(db.Text, nullable=True, default='{}', comment='额外参数')


class DataModelField(BaseModel):
    '''
    数据模型字段表
    '''
    __tablename__ = 'datamodel_field'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    datamodel_id = db.Column(db.String(36), nullable=True, default='', comment='所属数据模型')
    field_name = db.Column(db.String(200), nullable=True, default='', comment='字段名')
    field_value = db.Column(db.String(200), nullable=True, default='', comment='字段值')
    ext_params = db.Column(db.Text, nullable=True, default='{}', comment='拓展字段')
    is_sync = db.Column(db.SmallInteger, nullable=True, default=0, comment='是否同步')


class DataInterface(BaseModel):
    '''
    数据接口表
    '''
    __tablename__ = 'data_interface'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    datamodel_id = db.Column(db.String(36), nullable=False, default='', index=True, comment='所属数据模型id')
    name = db.Column(db.String(200), nullable=False, default='', comment='接口名称')
    api_key = db.Column(db.String(36), nullable=False, default='', index=True, comment='api_key')
    valid_fields = db.Column(db.Text, default="['*']", comment='允许访问字段')
    valid_time = db.Column(db.BIGINT, default=0, comment='有效期限')
    apply_user_id = db.Column(db.Integer, comment='申请人id')
    apply_user = db.Column(db.String(100), comment='申请人')
    apply_caption = db.Column(db.Text, default="", comment='申请说明')
    apply_time = db.Column(db.BIGINT, comment='申请时间')
    apply_time_length = db.Column(db.String(50), default='forever', comment='申请时长')
    review_user_id = db.Column(db.Integer, comment='审核人id')
    review_user = db.Column(db.String(100), comment='审核人')
    review_caption = db.Column(db.Text, default="", comment='审核说明')
    review_time = db.Column(db.BIGINT, comment='审核时间')
    review_time_length = db.Column(db.String(50), default='forever', comment='授权时长')
    status = db.Column(db.SmallInteger, nullable=False, default=1, comment='状态0禁用1启用')


if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    db.session.flush()
