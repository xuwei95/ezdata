from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size


class AlertStrategyModel(BaseModel):
    """
    告警策略表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    strategy_id: int | None = Field(default=None, description='策略主键')
    strategy_name: str | None = Field(default=None, description='策略名称')
    biz: str | None = Field(default=None, description='业务类型')
    trigger_conf: str | None = Field(default=None, description='触发条件(JSON)')
    forward_conf: str | None = Field(default=None, description='转发渠道配置(JSON数组)')
    status: int | None = Field(default=None, description='状态(1启用 0停用)')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')
    remark: str | None = Field(default=None, description='备注信息')

    @NotBlank(field_name='strategy_name', message='策略名称不能为空')
    @Size(field_name='strategy_name', min_length=0, max_length=200, message='策略名称长度不能超过200个字符')
    def get_strategy_name(self) -> str | None:
        return self.strategy_name

    def validate_fields(self) -> None:
        self.get_strategy_name()


class AlertStrategyPageQueryModel(AlertStrategyModel):
    """告警策略分页查询模型"""

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteAlertStrategyModel(BaseModel):
    """删除告警策略模型"""

    model_config = ConfigDict(alias_generator=to_camel)

    strategy_ids: str = Field(description='需要删除的策略主键(逗号分隔)')


class AlertRecordModel(BaseModel):
    """
    告警记录表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    alert_id: int | None = Field(default=None, description='告警主键')
    strategy_id: int | None = Field(default=None, description='告警策略id')
    title: str | None = Field(default=None, description='告警标题')
    content: str | None = Field(default=None, description='告警内容')
    level: int | None = Field(default=None, description='告警等级')
    status: int | None = Field(default=None, description='告警状态(0未处理 1已处理)')
    biz: str | None = Field(default=None, description='告警业务')
    source: str | None = Field(default=None, description='告警对象')
    metric: str | None = Field(default=None, description='告警指标')
    tags: str | None = Field(default=None, description='告警标签(JSON)')
    ext_params: str | None = Field(default=None, description='额外参数(JSON)')
    recover_time: datetime | None = Field(default=None, description='恢复时间')
    create_time: datetime | None = Field(default=None, description='创建时间')


class AlertRecordPageQueryModel(AlertRecordModel):
    """告警记录分页查询模型"""

    begin_time: str | None = Field(default=None, description='创建时间(范围起)')
    end_time: str | None = Field(default=None, description='创建时间(范围止)')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class EditAlertStatusModel(BaseModel):
    """修改告警处理状态模型"""

    model_config = ConfigDict(alias_generator=to_camel)

    alert_id: int = Field(description='告警主键')
    status: int = Field(description='告警状态(0未处理 1已处理)')


class DeleteAlertRecordModel(BaseModel):
    """删除告警记录模型"""

    model_config = ConfigDict(alias_generator=to_camel)

    alert_ids: str = Field(description='需要删除的告警主键(逗号分隔)')
