from datetime import datetime

from sqlalchemy import SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base, TenantMixin


class ApiToken(Base, TenantMixin):
    """通用 API Token 表(apikey 校验)。

    token_type 区分用途(data_api / agent / ...),ref_id 绑定具体资源(空=该用途全部),
    可被任意业务模块复用其 ApiTokenService.validate()。
    """

    __tablename__ = 'api_token'
    __table_args__ = {'comment': '通用 API Token 表'}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='主键')
    name: Mapped[str | None] = mapped_column(String(200), nullable=True, server_default="''", comment='名称')
    token: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True, comment='apikey')
    token_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, server_default='data_api', comment='用途 data_api/agent/...'
    )
    ref_id: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment='绑定的资源(如数据模型 code);空=该 type 全部'
    )
    status: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, server_default='1', comment='1启用 0停用')
    expire_time: Mapped[datetime | None] = mapped_column(nullable=True, comment='过期时间(空=永不)')
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, server_default="''", comment='备注')
    create_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='创建时间')
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='更新时间')
