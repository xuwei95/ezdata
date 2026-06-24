from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String

from config.database import Base, TenantMixin


class AiAppToken(Base, TenantMixin):
    """
    AI应用对外访问 API Key 表
    """

    __tablename__ = 'ai_app_token'
    __table_args__ = {'comment': 'AI应用APIKey表'}

    token_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='主键')
    app_id = Column(BigInteger, nullable=False, index=True, comment='所属应用ID')
    api_key = Column(String(64), nullable=False, index=True, comment='API Key')
    name = Column(String(100), nullable=True, comment='名称/用途')
    status = Column(CHAR(1), server_default='0', comment='状态: 0启用 1停用')
    expire_time = Column(DateTime, nullable=True, comment='过期时间(空=永久)')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now(), comment='创建时间')
