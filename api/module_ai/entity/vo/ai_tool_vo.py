from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size


class AiToolModel(BaseModel):
    """
    AI工具表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    tool_id: int | None = Field(default=None, description='工具主键')
    name: str | None = Field(default=None, description='工具名称')
    code: str | None = Field(default=None, description='工具代码(唯一标识)')
    tool_type: str | None = Field(default=None, description='工具类型: mcp/builtin')
    description: str | None = Field(default=None, description='工具描述')
    args: Any | None = Field(default=None, description='工具配置(MCP 连接参数等),对象')
    status: Literal['0', '1'] | None = Field(default=None, description='状态: 0启用 1停用')
    built_in: Literal['0', '1'] | None = Field(default=None, description='是否内置: 1是 0否')
    user_id: int | None = Field(default=None, description='用户ID')
    dept_id: int | None = Field(default=None, description='部门ID')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')
    remark: str | None = Field(default=None, description='备注')

    @NotBlank(field_name='name', message='工具名称不能为空')
    @Size(field_name='name', min_length=0, max_length=100, message='工具名称长度不能超过100个字符')
    def get_name(self) -> str | None:
        return self.name

    @NotBlank(field_name='code', message='工具代码不能为空')
    @Size(field_name='code', min_length=0, max_length=100, message='工具代码长度不能超过100个字符')
    def get_code(self) -> str | None:
        return self.code


class AiToolPageQueryModel(AiToolModel):
    """
    AI工具管理分页查询模型
    """

    keyword: str | None = Field(default=None, description='关键字(名称/代码)')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteAiToolModel(BaseModel):
    """
    删除AI工具模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    tool_ids: str = Field(description='需要删除的工具主键')


class TestToolReq(BaseModel):
    """
    测试 MCP 工具连接请求
    """

    model_config = ConfigDict(alias_generator=to_camel)

    tool_type: str = Field(default='mcp', description='工具类型')
    args: dict = Field(default_factory=dict, description='MCP 连接配置')
