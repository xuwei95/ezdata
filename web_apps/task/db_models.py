'''
任务模块数据模型
'''
from web_apps import db
from models import BaseModel
from sqlalchemy.dialects.mysql import LONGTEXT
import datetime
from celery import states
from config import CELERY_DEFAULT_QUEUE


class TaskTemplate(BaseModel):
    '''
    任务模版表
    '''
    __tablename__ = 'task_template'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='主键')
    name = db.Column(db.String(200), nullable=True, default='', comment='模版名称')
    code = db.Column(db.String(200), nullable=True, default='', comment='模版编码')
    icon = db.Column(db.String(500), nullable=True, default='https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ', comment='模版图标')
    type = db.Column(db.SmallInteger, nullable=True, default=1, comment='表单类型,1内置组件2动态配置')
    runner_type = db.Column(db.SmallInteger, nullable=True, default=1, comment='执行器类型，1内置执行器2动态代码')
    runner_code = db.Column(db.Text, nullable=True, default='', comment='模版配置')
    component = db.Column(db.String(500), nullable=True, default='', comment='任务组件')
    params = db.Column(db.Text, nullable=True, default='{}', comment='模版配置')
    built_in = db.Column(db.SmallInteger, nullable=True, default=0, comment='是否内置 1是 0不是')
    status = db.Column(db.SmallInteger, nullable=True, default=1, comment='状态')


class Task(BaseModel):
    '''
    任务表
    '''
    __tablename__ = 'task'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='id')
    template_code = db.Column(db.String(200), nullable=True, default='', comment='任务模版编码')
    task_type = db.Column(db.SmallInteger, nullable=True, default=1, comment='任务类型，1普通任务2dag工作流任务')
    run_type = db.Column(db.SmallInteger, nullable=True, default=1, comment='dag运行类型，1分布式2单进程')
    name = db.Column(db.String(100), nullable=True, default='', comment='名称')
    params = db.Column(LONGTEXT, nullable=True, default='{}', comment='参数')
    status = db.Column(db.SmallInteger, nullable=True, default=0, comment='状态')
    built_in = db.Column(db.SmallInteger, nullable=True, default=0, comment='是否内置 1是 0不是')
    trigger_type = db.Column(db.SmallInteger, nullable=True, default=1, comment='触发方式，1单次2定时')
    trigger_date = db.Column(db.String(100), default='[]', comment='触发始末时间')
    crontab = db.Column(db.String(500), nullable=True, default='', comment='定时设置')
    priority = db.Column(db.Integer, default=1, comment='优先级')
    retry = db.Column(db.Integer, default=0, comment='失败重试次数')
    countdown = db.Column(db.Integer, default=0, comment='失败重试间隔')
    run_queue = db.Column(db.String(200), default=CELERY_DEFAULT_QUEUE, comment='运行队列')
    running_id = db.Column(db.String(36), comment='正在运行任务实例ID')
    alert_strategy_ids = db.Column(db.Text, nullable=True, default='', comment='绑定告警策略列表')


class TaskInstance(db.Model):
    '''
    任务实例表
    '''
    __tablename__ = 'task_instance'
    id = db.Column(db.String(36), primary_key=True, nullable=False, default='', comment='id')
    parent_id = db.Column(db.String(36), nullable=True, default='', comment='父任务id')
    task_id = db.Column(db.String(36), nullable=True, default='', comment='任务id')
    node_id = db.Column(db.String(36), nullable=True, default='', comment='dag任务节点id')
    status = db.Column(db.String(50), nullable=True, default='running', comment='状态')
    worker = db.Column(db.String(200), nullable=True, default='', comment='worker')
    retry_num = db.Column(db.Integer, nullable=True, default=0, comment='重试次数')
    progress = db.Column(db.Float, nullable=True, default=0, comment='任务进度')
    start_time = db.Column(db.TIMESTAMP, nullable=True, comment='开始时间')
    end_time = db.Column(db.TIMESTAMP, nullable=True, comment='结束时间')
    closed = db.Column(db.SmallInteger, nullable=True, default=0, comment='是否已关闭')
    result = db.Column(db.Text, nullable=True, default='', comment='执行结果')

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
    from web_apps import app
    with app.app_context():
        db.create_all()
        db.session.commit()
        db.session.flush()
