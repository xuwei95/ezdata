from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class WorkerConsumerModel(BaseModel):
    """worker 消费队列增删入参"""

    model_config = ConfigDict(alias_generator=to_camel)

    worker: str = Field(description='worker 名称(如 celery@host)')
    queue: str = Field(description='队列名称')


class WorkerScaleModel(BaseModel):
    """worker 并发增减入参"""

    model_config = ConfigDict(alias_generator=to_camel)

    worker: str = Field(description='worker 名称')
    n: int = Field(default=1, description='增减的并发数')


class WorkerAutoscaleModel(BaseModel):
    """worker 弹性并发入参"""

    model_config = ConfigDict(alias_generator=to_camel)

    worker: str = Field(description='worker 名称')
    max: int = Field(description='最大并发')
    min: int = Field(description='最小并发')
