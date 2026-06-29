from datetime import datetime

from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base, TenantMixin


class SysUserOauth(Base, TenantMixin):
    """第三方身份绑定表(SSO)。

    一个平台用户(user_id)可绑定多个 provider 的第三方账号;(provider, open_id) 全局唯一。
    首登可据此查到已绑定用户;未绑定且开启自动建号时新建用户并写入本表。
    """

    __tablename__ = 'sys_user_oauth'
    __table_args__ = (
        UniqueConstraint('provider', 'open_id', name='uk_provider_openid'),
        {'comment': '第三方身份绑定表(SSO)'},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='主键')
    user_id: Mapped[int] = mapped_column(BigInteger, index=True, comment='平台用户ID')
    provider: Mapped[str] = mapped_column(String(20), comment='身份提供商:github/...')
    open_id: Mapped[str] = mapped_column(String(255), comment='提供商内用户唯一ID')
    union_id: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='跨应用统一ID(可选)')
    login_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment='第三方登录名/昵称')
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True, comment='第三方头像')
    create_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='绑定时间')
