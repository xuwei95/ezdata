from datetime import datetime

from sqlalchemy import JSON, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base, TenantMixin


class DataSource(Base, TenantMixin):
    """数据源表(一个连接)。"""

    __tablename__ = 'data_source'
    __table_args__ = {'comment': '数据源表'}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='主键')
    name: Mapped[str | None] = mapped_column(String(200), nullable=True, server_default="''", comment='名称')
    code: Mapped[str | None] = mapped_column(String(200), nullable=True, server_default="''", comment='编码(稳定引用)')
    source_type: Mapped[str | None] = mapped_column(String(50), nullable=True, comment='源类型,如 mysql/elasticsearch')
    family: Mapped[str | None] = mapped_column(String(50), nullable=True, comment='源族,如 rdbms/search/vector')
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment='非密钥连接参数(JSON)')
    secrets: Mapped[str | None] = mapped_column(Text, nullable=True, comment='密钥(AES 加密)')
    status: Mapped[str | None] = mapped_column(
        String(20), nullable=True, server_default='untested', comment='状态 untested/ok/failed'
    )
    last_test_at: Mapped[datetime | None] = mapped_column(nullable=True, comment='最后测试时间')
    remark: Mapped[str | None] = mapped_column(Text, nullable=True, comment='备注/业务上下文(供取数 AI 读取)')
    create_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='创建时间')
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='更新时间')


class DataModel(Base, TenantMixin):
    """数据模型表(源里的某张表/集合/索引)。"""

    __tablename__ = 'data_model'
    __table_args__ = {'comment': '数据模型表'}

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='主键')
    name: Mapped[str | None] = mapped_column(String(200), nullable=True, server_default="''", comment='名称')
    code: Mapped[str | None] = mapped_column(String(200), nullable=True, server_default="''", comment='编码')
    datasource_code: Mapped[str | None] = mapped_column(String(200), nullable=True, comment='引用的数据源编码')
    kind: Mapped[str | None] = mapped_column(
        String(50), nullable=True, server_default='table', comment='table/collection/index/topic/custom_query'
    )
    object_name: Mapped[str | None] = mapped_column(String(200), nullable=True, comment='表/索引/集合名')
    db_schema: Mapped[str | None] = mapped_column(
        String(200), nullable=True, server_default="''", comment='schema/库名'
    )
    fields: Mapped[list | None] = mapped_column(JSON, nullable=True, comment='字段结构(introspect 缓存)')
    default_filters: Mapped[list | None] = mapped_column(JSON, nullable=True, comment='默认过滤条件')
    auth: Mapped[str | None] = mapped_column(
        String(200), nullable=True, server_default='query,extract', comment='授权位 query/extract/api/write(逗号)'
    )
    status: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, server_default='1', comment='状态 1启用 0停用'
    )
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, server_default="''", comment='备注')
    create_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='创建时间')
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='更新时间')


class DataAnalysisTemplate(Base, TenantMixin):
    """数据分析模板:保存一次「取数 + 图表配置」,可复用/复现(后续大屏 widget 的原子)。"""

    __tablename__ = 'data_analysis_template'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, comment='主键')
    name: Mapped[str | None] = mapped_column(String(200), nullable=True, server_default="''", comment='模板名称')
    model_id: Mapped[str | None] = mapped_column(String(36), nullable=True, comment='数据模型ID')
    model_name: Mapped[str | None] = mapped_column(String(200), nullable=True, comment='数据模型名(冗余,展示用)')
    query: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment='取数配置 {type,native/filters/question}')
    chart_spec: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment='图表配置(EchartsBuilder cfg:type/x/ys/series/sort/style)')
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True, server_default="''", comment='备注')
    create_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='创建者')
    create_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='创建时间')
    update_by: Mapped[str | None] = mapped_column(String(64), nullable=True, server_default="''", comment='更新者')
    update_time: Mapped[datetime | None] = mapped_column(default=datetime.now, nullable=True, comment='更新时间')
