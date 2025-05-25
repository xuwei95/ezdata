'''
告警数据模型
'''
from web_apps import db
from models import BaseModel


class AlertStrategy(BaseModel):
    '''
    告警策略表
    '''
    __tablename__ = 'alert_strategy'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    name = db.Column(db.String(200), nullable=True, default='', comment='策略名称')
    template_code = db.Column(db.String(100), nullable=True, default='', comment='策略模版')
    trigger_conf = db.Column(db.Text, nullable=True, default='{}', comment='触发条件')
    forward_conf = db.Column(db.Text, nullable=True, default='{}', comment='转发条件')
    status = db.Column(db.SmallInteger, nullable=True, default=1, comment='状态')


class Alert(BaseModel):
    '''
    告警表
    '''
    __tablename__ = 'alert'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='id')
    strategy_id = db.Column(db.String(36), nullable=True, default='', comment='告警策略id')
    title = db.Column(db.String(500), nullable=True, default='', comment='告警标题')
    content = db.Column(db.Text, nullable=True, default='', comment='告警内容')
    level = db.Column(db.Integer, nullable=True, default=0, comment='告警等级')
    status = db.Column(db.SmallInteger, nullable=True, default=0, comment='告警状态')
    rule_id = db.Column(db.Text, nullable=True, default='', comment='规则编码')
    rule_name = db.Column(db.Text, nullable=True, default='', comment='规则名称')
    biz = db.Column(db.Text, nullable=True, default='', comment='告警业务')
    source = db.Column(db.Text, nullable=True, default='', comment='告警对象')
    tags = db.Column(db.Text, nullable=True, default='', comment='告警标签')
    metric = db.Column(db.Text, nullable=True, default='', comment='告警指标')
    recover_time = db.Column(db.TIMESTAMP, nullable=True, comment='恢复时间')
    ext_params = db.Column(db.Text, nullable=True, default='{}', comment='额外参数')


if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    db.session.flush()
