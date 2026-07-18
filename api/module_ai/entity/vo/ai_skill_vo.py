from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic_validation_decorator import NotBlank, Size


class AiSkillModel(BaseModel):
    """
    AI技能表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    skill_id: int | None = Field(default=None, description='技能主键')
    name: str | None = Field(default=None, description='技能名称')
    code: str | None = Field(default=None, description='技能代码(唯一标识)')
    description: str | None = Field(default=None, description='技能描述(常驻,决定何时选用)')
    content: str | None = Field(default=None, description='技能正文(SKILL.md,按需加载)')
    resources: str | None = Field(default=None, description='附加文件JSON([{name,content}])')
    ref_skills: str | None = Field(default=None, description='引用的技能code(逗号分隔,软引用)')
    skill_type: str | None = Field(default=None, description='类型: process流程型 / knowledge知识型')
    datasource_codes: str | None = Field(default=None, description='知识型绑定的数据源code(逗号分隔)')
    status: Literal['0', '1'] | None = Field(default=None, description='状态: 0启用 1停用')
    built_in: Literal['0', '1'] | None = Field(default=None, description='是否内置: 1是 0否')
    user_id: int | None = Field(default=None, description='用户ID')
    dept_id: int | None = Field(default=None, description='部门ID')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')
    remark: str | None = Field(default=None, description='备注')

    @NotBlank(field_name='name', message='技能名称不能为空')
    @Size(field_name='name', min_length=0, max_length=100, message='技能名称长度不能超过100个字符')
    def get_name(self) -> str | None:
        return self.name

    @NotBlank(field_name='code', message='技能代码不能为空')
    @Size(field_name='code', min_length=0, max_length=100, message='技能代码长度不能超过100个字符')
    def get_code(self) -> str | None:
        return self.code


class AiSkillPageQueryModel(AiSkillModel):
    """AI技能管理分页查询模型"""

    keyword: str | None = Field(default=None, description='关键字(名称/代码)')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteAiSkillModel(BaseModel):
    """删除AI技能模型"""

    model_config = ConfigDict(alias_generator=to_camel)

    skill_ids: str = Field(description='需要删除的技能主键')
