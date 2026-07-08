from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class TaskTemplateModel(BaseModel):
    """
    任务模板表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: str | None = Field(default=None, description='主键')
    name: str | None = Field(default=None, description='模板名称')
    code: str | None = Field(default=None, description='模板编码')
    icon: str | None = Field(default=None, description='模板图标')
    type: int | None = Field(default=1, description='表单类型,1内置组件2动态配置')
    runner_type: int | None = Field(default=1, description='执行器类型，1内置执行器2动态代码')
    runner_code: str | None = Field(default=None, description='动态执行器代码')
    component: str | None = Field(default=None, description='前端组件')
    params: str | None = Field(default=None, description='模板参数schema')
    built_in: int | None = Field(default=0, description='是否内置 1是 0不是')
    status: int | None = Field(default=1, description='状态 1启用 0禁用')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')
    remark: str | None = Field(default=None, description='备注')


class TaskTemplateQueryModel(TaskTemplateModel):
    """
    任务模板不分页查询模型

    查询字段默认 None，避免继承的业务默认值(status=1/type=1等)被当作过滤条件。
    """

    type: int | None = Field(default=None, description='表单类型')
    runner_type: int | None = Field(default=None, description='执行器类型')
    built_in: int | None = Field(default=None, description='是否内置')
    status: int | None = Field(default=None, description='状态')
    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')


class TaskTemplatePageQueryModel(TaskTemplateQueryModel):
    """
    任务模板分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class DeleteTaskTemplateModel(BaseModel):
    """
    删除任务模板模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的任务模板ID')


class TaskModel(BaseModel):
    """
    任务表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: str | None = Field(default=None, description='主键')
    template_code: str | None = Field(default=None, description='任务模板编码')
    task_type: int | None = Field(default=1, description='任务类型，1普通任务2dag工作流任务')
    name: str | None = Field(default=None, description='名称')
    params: str | None = Field(default=None, description='参数')
    status: int | None = Field(default=0, description='状态 0停用 1启用')
    built_in: int | None = Field(default=0, description='是否内置 1是 0不是')
    trigger_type: int | None = Field(default=1, description='触发方式，1单次2定时')
    crontab: str | None = Field(default=None, description='定时设置')
    priority: int | None = Field(default=1, description='优先级')
    retry: int | None = Field(default=0, description='失败重试次数')
    countdown: int | None = Field(default=0, description='失败重试间隔(秒)')
    timeout: int | None = Field(default=0, description='任务超时(秒):0=全局默认,-1=不限(流式/超长),>0=自定义')
    run_queue: str | None = Field(default='default', description='运行队列')
    running_id: str | None = Field(default=None, description='正在运行任务实例ID')
    job_id: int | None = Field(default=None, description='关联的调度任务ID')
    alert_strategy_ids: str | None = Field(default=None, description='绑定的告警策略ID(逗号分隔)')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')
    remark: str | None = Field(default=None, description='备注')


class TaskQueryModel(TaskModel):
    """
    任务不分页查询模型

    查询用字段默认置为 None，避免继承 TaskModel 的业务默认值(task_type=1/trigger_type=1/status=0)
    被当作过滤条件，导致定时任务/启用任务在列表中被过滤掉而"看不到"。
    """

    task_type: int | None = Field(default=None, description='任务类型')
    trigger_type: int | None = Field(default=None, description='触发方式')
    status: int | None = Field(default=None, description='状态')
    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')


class TaskPageQueryModel(TaskQueryModel):
    """
    任务分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class EditTaskStatusModel(BaseModel):
    """
    修改任务状态模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    id: str = Field(description='任务ID')
    status: int = Field(description='状态 0停用 1启用')


class DeleteTaskModel(BaseModel):
    """
    删除任务模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    ids: str = Field(description='需要删除的任务ID')


class DebugTaskModel(BaseModel):
    """任务调试运行入参(不落任务实例、不投 Celery,沙箱/本地执行一次)"""

    model_config = ConfigDict(alias_generator=to_camel)

    template_code: str | None = Field(default=None, description='模板编码:PythonTask/ShellTask/DataIntegrationTask 等')
    runner_type: int | None = Field(default=1, description='执行器类型,1内置2动态')
    runner_code: str | None = Field(default=None, description='动态执行器代码(runner_type=2)')
    params: dict = Field(default_factory=dict, description='任务参数')
    timeout: int | None = Field(default=None, description='超时(秒)')


class TaskInstanceModel(BaseModel):
    """
    任务实例表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: str | None = Field(default=None, description='主键')
    parent_id: str | None = Field(default=None, description='父任务id')
    task_id: str | None = Field(default=None, description='任务id')
    node_id: str | None = Field(default=None, description='dag节点id')
    name: str | None = Field(default=None, description='任务名称')
    status: str | None = Field(default=None, description='状态')
    worker: str | None = Field(default=None, description='worker')
    retry_num: int | None = Field(default=0, description='重试次数')
    progress: float | None = Field(default=0, description='任务进度')
    start_time: datetime | None = Field(default=None, description='开始时间')
    end_time: datetime | None = Field(default=None, description='结束时间')
    closed: int | None = Field(default=0, description='是否已关闭')
    result: str | None = Field(default=None, description='执行结果')


class TaskInstanceQueryModel(TaskInstanceModel):
    """
    任务实例不分页查询模型
    """

    begin_time: str | None = Field(default=None, description='开始时间')
    end_time: str | None = Field(default=None, description='结束时间')


class TaskInstancePageQueryModel(TaskInstanceQueryModel):
    """
    任务实例分页查询模型
    """

    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class TaskLogModel(BaseModel):
    """
    任务执行明细日志表对应pydantic模型
    """

    model_config = ConfigDict(alias_generator=to_camel, from_attributes=True)

    id: int | None = Field(default=None, description='日志ID')
    task_uuid: str | None = Field(default=None, description='任务实例ID')
    level: str | None = Field(default=None, description='日志级别')
    content: str | None = Field(default=None, description='日志内容')
    create_time: datetime | None = Field(default=None, description='创建时间')
    cursor: str | None = Field(
        default=None,
        description='增量游标(随行返回):前端回传最后一行的cursor以拉取更新的日志。db后端=日志id,es后端=时间戳',
    )


class TaskLogQueryModel(BaseModel):
    """
    任务日志查询模型
    """

    model_config = ConfigDict(alias_generator=to_camel)

    task_uuid: str = Field(description='任务实例ID')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=20, description='每页记录数')
    after: str | None = Field(
        default=None,
        description='增量游标:不为空时仅返回该游标之后的新日志(正序),用于控制台持续追加。'
        'db后端为日志id,es后端为时间戳;由上一次返回行的cursor回传,后端无关',
    )
