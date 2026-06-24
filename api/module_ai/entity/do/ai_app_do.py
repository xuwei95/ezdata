from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String, Text

from config.database import Base, TenantMixin


class AiApp(Base, TenantMixin):
    """
    AI应用表(打包的助手配置:人设 + 绑定工具/知识库 + 参数 + 交互)
    """

    __tablename__ = 'ai_app'
    __table_args__ = {'comment': 'AI应用表'}

    app_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='应用主键')
    name = Column(String(100), nullable=False, comment='应用名称')
    icon = Column(String(500), nullable=True, comment='应用图标')
    description = Column(String(500), nullable=True, comment='应用描述')
    app_type = Column(String(50), nullable=True, comment='应用类型/分类')
    status = Column(CHAR(1), server_default='0', comment='状态: 0发布 1草稿')
    config = Column(Text, nullable=True, comment='应用配置JSON(prompt/绑定工具知识库/参数等)')
    user_id = Column(BigInteger, nullable=True, comment='用户ID')
    dept_id = Column(BigInteger, nullable=True, comment='部门ID')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now(), comment='创建时间')
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now(), comment='更新时间')
    remark = Column(String(500), nullable=True, comment='备注')
