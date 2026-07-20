from datetime import datetime

from sqlalchemy import CHAR, BigInteger, Column, DateTime, String, Text

from config.database import Base, TenantMixin
from config.env import DataBaseConfig
from utils.common_util import SqlalchemyUtil


class DataMetric(Base, TenantMixin):
    """指标(语义层):权威口径的业务度量,绑定数据模型 + 度量/维度定义。

    agent 命中指标即用 query_metric 取一致的数(而非自写 SQL/agg)。定义人拍板,LLM 只起草。
    """

    __tablename__ = 'data_metric'
    __table_args__ = {'comment': '指标表(语义层)'}

    metric_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='指标主键')
    name = Column(String(100), nullable=False, comment='指标名')
    code = Column(String(100), nullable=False, comment='指标代码(唯一,供 query_metric 引用)')
    synonyms = Column(String(500), nullable=True, comment='同义词(逗号分隔,提升命中)')
    caliber = Column(Text, nullable=True, comment='口径(权威定义:算什么/含不含/窗口)')
    model_id = Column(String(64), nullable=True, comment='绑定的 data_model.id')
    measure = Column(Text, nullable=True, comment='度量JSON {agg:sum/avg/count/max/min/count_distinct, field}')
    dimensions = Column(Text, nullable=True, comment='允许分组维度JSON [{field,name}]')
    time_field = Column(String(100), nullable=True, comment='时间字段')
    default_grain = Column(String(20), nullable=True, comment='默认时间粒度 day/week/month')
    default_filters = Column(Text, nullable=True, comment='固定口径过滤JSON {field:value|[...]}')
    unit = Column(String(50), nullable=True, comment='单位(亿/%/…)')
    verified_examples = Column(Text, nullable=True, comment='人工审定示例JSON [{question,expect}]')
    status = Column(CHAR(1), server_default='0', comment='状态: 0启用 1停用')
    review_state = Column(String(20), server_default='ok', comment='ok / stale(血缘触发待复核)')
    built_in = Column(CHAR(1), server_default='0', comment='是否内置')
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
