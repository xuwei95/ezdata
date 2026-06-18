from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ApiTokenVo(BaseModel):
    """API Token VO。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str | None = Field(default=None, description='主键')
    name: str | None = Field(default=None, description='名称')
    token: str | None = Field(default=None, description='apikey(自动生成)')
    token_type: str | None = Field(default='data_api', description='用途 data_api/agent')
    ref_id: str | None = Field(default=None, description='绑定资源(如模型 code);空=全部')
    status: int | None = Field(default=1, description='1启用 0停用')
    expire_time: datetime | None = Field(default=None, description='过期时间')
    remark: str | None = Field(default=None, description='备注')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')


class ApiTokenQuery(BaseModel):
    """API Token 分页查询。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = Field(default=None, description='名称')
    token_type: str | None = Field(default=None, description='用途')
    ref_id: str | None = Field(default=None, description='绑定资源')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')
