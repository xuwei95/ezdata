from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, SmallInteger, String, Text

from config.database import Base, TenantMixin


class AlertStrategy(Base, TenantMixin):
    """
    告警策略表
    """

    __tablename__ = 'alert_strategy'
    __table_args__ = {'comment': '告警策略表'}

    strategy_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='策略主键')
    strategy_name = Column(String(200), nullable=False, comment='策略名称')
    biz = Column(String(50), nullable=True, server_default='scheduler', comment='业务类型(scheduler等)')
    trigger_conf = Column(Text, nullable=True, comment='触发条件(JSON,含告警等级level等)')
    forward_conf = Column(Text, nullable=True, comment='转发渠道配置(JSON数组)')
    status = Column(SmallInteger, nullable=True, server_default='1', comment='状态(1启用 0停用)')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now, comment='更新时间')
    remark = Column(String(500), nullable=True, server_default="''", comment='备注信息')


class AlertRecord(Base, TenantMixin):
    """
    告警记录表
    """

    __tablename__ = 'alert_record'
    __table_args__ = {'comment': '告警记录表'}

    alert_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='告警主键')
    strategy_id = Column(BigInteger, nullable=True, comment='告警策略id')
    title = Column(String(500), nullable=True, comment='告警标题')
    content = Column(Text, nullable=True, comment='告警内容')
    level = Column(Integer, nullable=True, server_default='0', comment='告警等级')
    status = Column(SmallInteger, nullable=True, server_default='0', comment='告警状态(0未处理 1已处理)')
    biz = Column(String(50), nullable=True, comment='告警业务(scheduler等)')
    source = Column(String(200), nullable=True, comment='告警对象(任务名/实例等)')
    metric = Column(String(100), nullable=True, comment='告警指标(task_fail/task_timeout等)')
    tags = Column(Text, nullable=True, comment='告警标签(JSON,含instance_id/worker/retries等)')
    ext_params = Column(Text, nullable=True, comment='额外参数(JSON)')
    recover_time = Column(DateTime, nullable=True, comment='恢复时间')
    create_time = Column(DateTime, nullable=True, default=datetime.now, comment='创建时间')
