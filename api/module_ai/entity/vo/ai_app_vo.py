from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size


class AiAppModel(BaseModel):
    """
    AI应用表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    app_id: int | None = Field(default=None, description='应用主键')
    name: str | None = Field(default=None, description='应用名称')
    icon: str | None = Field(default=None, description='应用图标')
    description: str | None = Field(default=None, description='应用描述')
    app_type: str | None = Field(default=None, description='应用类型/分类')
    status: Literal['0', '1'] | None = Field(default=None, description='状态: 0发布 1草稿')
    config: Any | None = Field(default=None, description='应用配置(对象):prompt/prologue/presetQuestions/quickCommands/toolIds/datasetIds/model')
    user_id: int | None = Field(default=None, description='用户ID')
    dept_id: int | None = Field(default=None, description='部门ID')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')
    remark: str | None = Field(default=None, description='备注')

    @NotBlank(field_name='name', message='应用名称不能为空')
    @Size(field_name='name', min_length=0, max_length=100, message='应用名称长度不能超过100个字符')
    def get_name(self) -> str | None:
        return self.name


class AiAppPageQueryModel(AiAppModel):
    """AI应用分页查询模型"""

    keyword: str | None = Field(default=None, description='关键字(名称/描述)')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteAiAppModel(BaseModel):
    """删除AI应用模型"""

    model_config = ConfigDict(alias_generator=to_camel)

    app_ids: str = Field(description='需要删除的应用主键')


class PromptGenerateReq(BaseModel):
    """AI 生成提示词请求"""

    model_config = ConfigDict(alias_generator=to_camel)

    requirement: str = Field(description='一句话需求/应用定位')
    model_id: int | None = Field(default=0, description='用于生成的模型ID(默认env兜底)')


class AppDebugReq(BaseModel):
    """应用调试对话请求(用草稿 config,免先保存)"""

    model_config = ConfigDict(alias_generator=to_camel)

    config: dict | None = Field(default=None, description='草稿应用配置(prompt/toolIds/datasetIds/model 等)')
    message: str = Field(description='用户消息')
    session_id: str | None = Field(default=None, description='会话ID')


class ApiChatReq(BaseModel):
    """对外 API 对话请求(apikey 鉴权)"""

    model_config = ConfigDict(alias_generator=to_camel)

    api_key: str | None = Field(default=None, description='应用 API Key(也可放 X-API-Key 头)')
    message: str = Field(description='用户消息')
    session_id: str | None = Field(default=None, description='会话ID(不传则新建)')
