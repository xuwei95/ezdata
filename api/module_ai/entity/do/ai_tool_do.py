from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String, Text

from config.database import Base, TenantMixin
from config.env import DataBaseConfig
from utils.common_util import SqlalchemyUtil


class AiTool(Base, TenantMixin):
    """
    AI工具表(MCP 外部工具 + 内置工具)
    """

    __tablename__ = 'ai_tool'
    __table_args__ = {'comment': 'AI工具表'}

    tool_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='工具主键')
    name = Column(String(100), nullable=False, comment='工具名称')
    code = Column(String(100), nullable=False, comment='工具代码(唯一标识)')
    tool_type = Column(String(50), nullable=False, server_default='mcp', comment='工具类型: mcp/builtin')
    description = Column(
        Text,
        nullable=True,
        comment='工具描述',
    )
    args = Column(Text, nullable=True, comment='工具配置JSON')
    status = Column(CHAR(1), server_default='0', comment='状态: 0启用 1停用')
    built_in = Column(CHAR(1), server_default='0', comment='是否内置: 1是(不可删/改code) 0否')
    user_id = Column(BigInteger, nullable=True, comment='用户ID')
    dept_id = Column(BigInteger, nullable=True, comment='部门ID')
    create_by = Column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time = Column(DateTime, nullable=True, default=datetime.now(), comment='创建时间')
    update_by = Column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time = Column(DateTime, nullable=True, default=datetime.now(), comment='更新时间')
    remark = Column(
        String(500),
        nullable=True,
        server_default=SqlalchemyUtil.get_server_default_null(DataBaseConfig.db_type),
        comment='备注',
    )
