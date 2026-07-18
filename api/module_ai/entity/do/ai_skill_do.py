from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String, Text

from config.database import Base, TenantMixin
from config.env import DataBaseConfig
from utils.common_util import SqlalchemyUtil


class AiSkill(Base, TenantMixin):
    """
    AI技能表(类 Claude Agent Skills:能力包 = 名称 + 描述 + SKILL.md 正文指令 + 可选打包资源)。

    渐进式披露:agent 平时只见到「名称+描述」清单,任务匹配时才 load_skill 拉取完整正文(content)。
    """

    __tablename__ = 'ai_skill'
    __table_args__ = {'comment': 'AI技能表(Agent Skills 能力包)'}

    skill_id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True, comment='技能主键')
    name = Column(String(100), nullable=False, comment='技能名称')
    code = Column(String(100), nullable=False, comment='技能代码(唯一标识,供 load_skill 引用)')
    description = Column(Text, nullable=True, comment='技能描述(常驻上下文,决定何时被选用)')
    content = Column(Text, nullable=True, comment='技能正文(SKILL.md,按需 load_skill 拉取)')
    resources = Column(Text, nullable=True, comment='附加文件JSON([{name,content}];name 可含 / 表目录)')
    ref_skills = Column(String(500), nullable=True, comment='引用的技能code(逗号分隔,软引用)')
    skill_type = Column(String(20), server_default='process', comment='类型: process流程型(全局) knowledge知识型(按源浮现)')
    datasource_codes = Column(String(500), nullable=True, comment='知识型绑定的数据源code(逗号分隔;为空=不绑)')
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
