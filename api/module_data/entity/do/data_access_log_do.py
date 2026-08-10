from datetime import datetime

from sqlalchemy import JSON, BigInteger, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class DataAccessLog(Base):
    """数据访问审计:谁在何时查了哪个数据源/表、语句是什么、返回多少行。

    不套 TenantMixin(异步批量写入器在后台线程刷盘,无请求上下文无法自动盖章/过滤);
    tenant_id 在请求线程入队时显式捕获并落列,读取时按需手动按租户过滤。
    """

    __tablename__ = 'data_access_log'
    __table_args__ = {'comment': '数据访问审计日志'}

    access_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment='主键')
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True, comment='租户ID')
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, comment='访问用户ID')
    user_name: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True, comment='访问用户名')
    datasource_code: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True, comment='数据源编码')
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True, comment='数据源类型')
    model_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment='数据模型ID(如有)')
    object_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, comment='目标表/索引/集合')
    access_type: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment='query/search/aggregate/preview/api'
    )
    statement: Mapped[str | None] = mapped_column(Text, nullable=True, comment='原始查询语句/DSL/参数')
    filters: Mapped[dict | list | None] = mapped_column(JSON, nullable=True, comment='结构化过滤条件')
    result_rows: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='返回行数')
    exec_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='执行耗时(ms)')
    success: Mapped[int | None] = mapped_column(SmallInteger, nullable=True, server_default='1', comment='1成功0失败')
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True, comment='失败原因')
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True, comment='链路追踪ID')
    request_path: Mapped[str | None] = mapped_column(String(255), nullable=True, comment='HTTP 路径')
    source: Mapped[str | None] = mapped_column(String(20), nullable=True, server_default='web', comment='web/api/agent/task')
    access_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, index=True, comment='访问时间')
