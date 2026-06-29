from datetime import datetime

from sqlalchemy import BigInteger, Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class SysUserTenant(Base):
    """用户-租户成员表(一人多租户)。

    ⚠️ 故意不继承 TenantMixin:这是跨租户的控制面映射,绝不能被租户过滤
    (否则在某租户上下文里读不到该用户在其它租户的成员关系)。所有读写在无上下文
    或跨租户场景下进行,调用方自行保证(登录/切换/列表处包 tenant_bypass)。
    租户 = 顶级部门(sys_dept.parent_id=0)的 dept_id。
    """

    __tablename__ = 'sys_user_tenant'
    __table_args__ = (
        UniqueConstraint('user_id', 'tenant_id', name='uk_user_tenant'),
        {'comment': '用户-租户成员表(一人多租户)'},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='主键')
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, comment='用户ID')
    tenant_id: Mapped[int] = mapped_column(BigInteger, index=True, comment='租户ID(顶级部门)')
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, comment='是否默认激活租户')
    create_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='加入时间')
