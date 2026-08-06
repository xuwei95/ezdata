from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, Integer, LargeBinary, String, UniqueConstraint
from sqlalchemy.dialects import mysql

from config.database import Base, TenantMixin
from config.env import DataBaseConfig
from utils.common_util import SqlalchemyUtil


class SysNotice(Base, TenantMixin):
    """
    通知公告表
    """

    __tablename__ = 'sys_notice'
    __table_args__ = {'comment': '通知公告表'}

    notice_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True, comment='公告ID')
    notice_title = Column(String(50), nullable=False, comment='公告标题')
    notice_type = Column(CHAR(1), nullable=False, comment='公告类型（1通知 2公告）')
    notice_content = Column(
        mysql.LONGBLOB if DataBaseConfig.db_type == 'mysql' else LargeBinary,
        nullable=True,
        server_default=SqlalchemyUtil.get_server_default_null(DataBaseConfig.db_type, False),
        comment='公告内容',
    )
    status = Column(CHAR(1), nullable=True, server_default='0', comment='公告状态（0正常 1关闭）')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, comment='创建时间', default=datetime.now())
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, comment='更新时间', default=datetime.now())
    remark = Column(
        String(255),
        nullable=True,
        server_default=SqlalchemyUtil.get_server_default_null(DataBaseConfig.db_type),
        comment='备注',
    )


class SysNoticeRead(Base):
    """
    公告已读记录表

    以 (user_id, notice_id) 唯一约束记录某用户已读某条公告;notice_id 全局唯一,
    故本表无需 TenantMixin(join 到 sys_notice/sys_user 时由全局租户事件过滤)。
    """

    __tablename__ = 'sys_notice_read'
    __table_args__ = (
        UniqueConstraint('user_id', 'notice_id', name='uk_user_notice'),
        {'comment': '公告已读记录表'},
    )

    read_id = Column(
        BigInteger().with_variant(Integer, 'sqlite'),
        primary_key=True,
        nullable=False,
        autoincrement=True,
        comment='已读主键',
    )
    notice_id = Column(Integer, nullable=False, comment='公告ID')
    user_id = Column(BigInteger, nullable=False, comment='用户ID')
    read_time = Column(DateTime, nullable=False, default=datetime.now, comment='阅读时间')


class SysNoticeUser(Base):
    """
    公告收件人表(定向投递)

    某条公告定向给哪些用户;**没有任何行 = 广播(全员可见)**,有行 = 只对这些用户可见。
    非 TenantMixin:notice_id 全局唯一,join sys_notice/sys_user 时随其租户过滤。
    """

    __tablename__ = 'sys_notice_user'
    __table_args__ = (
        UniqueConstraint('notice_id', 'user_id', name='uk_notice_user'),
        {'comment': '公告收件人表'},
    )

    id = Column(
        BigInteger().with_variant(Integer, 'sqlite'),
        primary_key=True,
        nullable=False,
        autoincrement=True,
        comment='主键',
    )
    notice_id = Column(Integer, nullable=False, comment='公告ID')
    user_id = Column(BigInteger, nullable=False, comment='收件人用户ID')
    create_time = Column(DateTime, nullable=False, default=datetime.now, comment='投递时间')
