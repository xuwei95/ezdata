from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DagGraphModel(BaseModel):
    """DAG 图版本文档。"""

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True, populate_by_name=True)

    id: str | None = Field(default=None, description='主键')
    dag_task_id: str | None = Field(default=None, description='所属 DAG 任务id')
    version: str | None = Field(default=None, description="版本:'draft' 或 发布版本号")
    status: str | None = Field(default=None, description='draft/published/archived')
    graph: Any | None = Field(default=None, description='整张图(nodes/edges/viewport)')
    remark: str | None = Field(default=None, description='发布说明')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')


class DagCreateReq(BaseModel):
    """新建 DAG 任务(容器)。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(description='DAG 名称')
    run_queue: str | None = Field(default='default', description='运行队列')
    remark: str | None = Field(default=None, description='备注')


class DagDraftSaveReq(BaseModel):
    """保存草稿图。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    graph: dict = Field(description='整张图 JSON(nodes/edges/viewport)')


class DagPublishReq(BaseModel):
    """发布草稿为正式版本。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    remark: str | None = Field(default=None, description='发布说明')


class DagRunReq(BaseModel):
    """运行 DAG。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    source: str = Field(default='published', description='published 正式版 / draft 试运行')


class DagSettingsReq(BaseModel):
    """DAG 本体设置。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str = Field(description='名称')
    status: int = Field(default=1, description='1启用 0停用')
    trigger_type: int = Field(default=1, description='1单次 2定时')
    crontab: str | None = Field(default=None, description='定时 Cron 表达式')
    run_queue: str | None = Field(default='default', description='运行队列')
    run_type: int = Field(default=1, description='1分布式 2单机')
    retry: int = Field(default=0, description='失败重试次数')
    countdown: int = Field(default=0, description='重试间隔(秒)')
    remark: str | None = Field(default=None, description='备注')
