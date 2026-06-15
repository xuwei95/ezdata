from datetime import datetime

from sqlalchemy import Float, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class TaskTemplate(Base):
    """
    任务模板表
    """

    __tablename__ = 'task_template'
    __table_args__ = {'comment': '任务模板表'}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='主键')
    name: Mapped[str | None] = mapped_column(String(200), nullable=True, server_default="''", comment='模板名称')
    code: Mapped[str | None] = mapped_column(String(200), nullable=True, server_default="''", comment='模板编码')
    icon: Mapped[str | None] = mapped_column(String(500), nullable=True, server_default="''", comment='模板图标')
    type: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, server_default='1', comment='表单类型,1内置组件2动态配置'
    )
    runner_type: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, server_default='1', comment='执行器类型，1内置执行器2动态代码'
    )
    runner_code: Mapped[str | None] = mapped_column(Text, nullable=True, comment='动态执行器代码')
    component: Mapped[str | None] = mapped_column(String(500), nullable=True, server_default="''", comment='前端组件')
    params: Mapped[str | None] = mapped_column(Text, nullable=True, comment='模板参数schema')
    built_in: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, server_default='0', comment='是否内置 1是 0不是'
    )
    status: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, server_default='1', comment='状态 1启用 0禁用'
    )
    create_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='创建时间')
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='更新时间')
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, server_default="''", comment='备注')


class Task(Base):
    """
    任务表
    """

    __tablename__ = 'task'
    __table_args__ = {'comment': '任务表'}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='主键')
    template_code: Mapped[str | None] = mapped_column(
        String(200), nullable=True, server_default="''", comment='任务模板编码'
    )
    task_type: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, server_default='1', comment='任务类型，1普通任务2dag工作流任务'
    )
    name: Mapped[str | None] = mapped_column(String(100), nullable=True, server_default="''", comment='名称')
    params: Mapped[str | None] = mapped_column(Text, nullable=True, comment='参数')
    status: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, server_default='0', comment='状态 0停用 1启用'
    )
    built_in: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, server_default='0', comment='是否内置 1是 0不是'
    )
    trigger_type: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, server_default='1', comment='触发方式，1单次2定时'
    )
    crontab: Mapped[str | None] = mapped_column(String(500), nullable=True, server_default="''", comment='定时设置')
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default='1', comment='优先级')
    retry: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default='0', comment='失败重试次数')
    countdown: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default='0', comment='失败重试间隔(秒)')
    run_queue: Mapped[str | None] = mapped_column(
        String(200), nullable=True, server_default='default', comment='运行队列'
    )
    running_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment='正在运行任务实例ID')
    job_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='关联的调度任务ID(sys_job)')
    alert_strategy_ids: Mapped[str | None] = mapped_column(
        String(500), nullable=True, server_default="''", comment='绑定的告警策略ID(逗号分隔)'
    )
    create_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='创建时间')
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='更新时间')
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, server_default="''", comment='备注')


class TaskInstance(Base):
    """
    任务实例表
    """

    __tablename__ = 'task_instance'
    __table_args__ = {'comment': '任务实例表'}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='主键(celery task uuid)')
    parent_id: Mapped[str | None] = mapped_column(String(36), nullable=True, server_default="''", comment='父任务id')
    task_id: Mapped[str | None] = mapped_column(String(36), nullable=True, server_default="''", comment='任务id')
    node_id: Mapped[str | None] = mapped_column(String(36), nullable=True, server_default="''", comment='dag节点id')
    name: Mapped[str | None] = mapped_column(String(100), nullable=True, server_default="''", comment='任务名称')
    status: Mapped[str | None] = mapped_column(String(50), nullable=True, server_default='STARTED', comment='状态')
    worker: Mapped[str | None] = mapped_column(String(200), nullable=True, server_default="''", comment='worker')
    retry_num: Mapped[int | None] = mapped_column(Integer, nullable=True, server_default='0', comment='重试次数')
    progress: Mapped[float | None] = mapped_column(Float, nullable=True, server_default='0', comment='任务进度')
    start_time: Mapped[datetime | None] = mapped_column(nullable=True, comment='开始时间')
    end_time: Mapped[datetime | None] = mapped_column(nullable=True, comment='结束时间')
    closed: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, server_default='0', comment='是否已关闭')
    result: Mapped[str | None] = mapped_column(Text, nullable=True, comment='执行结果')


class TaskLog(Base):
    """
    任务执行日志表（task_log_type=db 时使用）
    """

    __tablename__ = 'task_log'
    __table_args__ = {'comment': '任务执行日志表'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment='日志ID')
    task_uuid: Mapped[str | None] = mapped_column(String(36), nullable=True, server_default="''", comment='任务实例ID')
    level: Mapped[str | None] = mapped_column(String(20), nullable=True, server_default='INFO', comment='日志级别')
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment='日志内容')
    create_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='创建时间')
