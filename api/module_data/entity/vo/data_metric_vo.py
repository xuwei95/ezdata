from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DataMetricModel(BaseModel):
    """指标 VO。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    metric_id: int | None = Field(default=None, description='主键')
    name: str | None = Field(default=None, description='指标名')
    code: str | None = Field(default=None, description='指标代码(唯一)')
    synonyms: str | None = Field(default=None, description='同义词(逗号分隔)')
    caliber: str | None = Field(default=None, description='口径(权威定义)')
    model_id: str | None = Field(default=None, description='绑定 data_model.id')
    measure: str | None = Field(default=None, description='度量JSON')
    dimensions: str | None = Field(default=None, description='维度JSON')
    time_field: str | None = Field(default=None, description='时间字段')
    default_grain: str | None = Field(default=None, description='默认时间粒度')
    default_filters: str | None = Field(default=None, description='固定过滤JSON')
    unit: str | None = Field(default=None, description='单位')
    verified_examples: str | None = Field(default=None, description='审定示例JSON')
    status: str | None = Field(default=None, description='状态: 0启用 1停用')
    review_state: str | None = Field(default=None, description='ok/stale')
    built_in: str | None = Field(default=None, description='是否内置')
    user_id: int | None = Field(default=None)
    dept_id: int | None = Field(default=None)
    create_by: str | None = Field(default=None)
    create_time: datetime | None = Field(default=None)
    update_by: str | None = Field(default=None)
    update_time: datetime | None = Field(default=None)
    remark: str | None = Field(default=None)


class DataMetricQuery(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    page_num: int = Field(default=1)
    page_size: int = Field(default=10)
    keyword: str | None = Field(default=None)
    status: str | None = Field(default=None)
