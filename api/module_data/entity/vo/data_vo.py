from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class DataSourceVo(BaseModel):
    """数据源 VO。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str | None = Field(default=None, description='主键')
    name: str | None = Field(default=None, description='名称')
    code: str | None = Field(default=None, description='编码')
    source_type: str | None = Field(default=None, description='源类型')
    family: str | None = Field(default=None, description='源族')
    config: dict | None = Field(default=None, description='非密钥连接参数')
    secrets: Any | None = Field(default=None, description='密钥参数(提交时传明文 dict,返回时脱敏 dict)')
    status: str | None = Field(default=None, description='状态')
    last_test_at: datetime | None = Field(default=None, description='最后测试时间')
    remark: str | None = Field(default=None, description='备注')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')


class DataSourceQuery(BaseModel):
    """数据源分页查询。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = Field(default=None, description='名称')
    code: str | None = Field(default=None, description='编码')
    source_type: str | None = Field(default=None, description='源类型')
    family: str | None = Field(default=None, description='源族')
    status: str | None = Field(default=None, description='状态')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class TestConnReq(BaseModel):
    """测连接:按 id 或内联 source_type+config(+secrets)。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str | None = Field(default=None, description='已存数据源 id')
    source_type: str | None = Field(default=None, description='源类型(内联测试)')
    config: dict | None = Field(default=None, description='连接参数')
    secrets: dict | None = Field(default=None, description='密钥参数')


class DataModelVo(BaseModel):
    """数据模型 VO。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str | None = Field(default=None, description='主键')
    name: str | None = Field(default=None, description='名称')
    code: str | None = Field(default=None, description='编码')
    datasource_code: str | None = Field(default=None, description='数据源编码')
    kind: str | None = Field(default='table', description='类型')
    object_name: str | None = Field(default=None, description='表/索引/集合名')
    db_schema: str | None = Field(default=None, description='schema/库名')
    fields: list | None = Field(default=None, description='字段结构')
    default_filters: list | None = Field(default=None, description='默认过滤')
    auth: str | None = Field(default='query,extract', description='授权位')
    status: int | None = Field(default=1, description='状态')
    remark: str | None = Field(default=None, description='备注')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_by: str | None = Field(default=None, description='更新者')
    update_time: datetime | None = Field(default=None, description='更新时间')


class DataModelQuery(BaseModel):
    """数据模型分页查询。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: str | None = Field(default=None, description='名称')
    code: str | None = Field(default=None, description='编码')
    datasource_code: str | None = Field(default=None, description='数据源编码')
    page_num: int = Field(default=1, description='当前页码')
    page_size: int = Field(default=10, description='每页记录数')


class QueryReq(BaseModel):
    """数据查询(不分页):filters 或 native。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    filters: list[dict] | None = Field(default=None, description='统一过滤结构 [{field,op,value}]')
    native: Any | None = Field(default=None, description='原生查询(SQL 串 / DSL dict / pipeline)')
    params: dict | None = Field(default=None, description='看板变量取值 {name: value},取数前替换 native 里的 {{name}}')
    limit: int | None = Field(default=5000, description='安全上限')


class AiQueryReq(BaseModel):
    """AI 取数:自然语言 → 生成原生查询 → 执行。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    question: str = Field(description='自然语言需求')
    limit: int | None = Field(default=200, description='安全上限')


class SearchReq(BaseModel):
    """数据接口分页查询。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    filters: list[dict] | None = Field(default=None, description='统一过滤结构')
    page: int = Field(default=1, description='页码')
    pagesize: int = Field(default=20, description='每页条数')


class EtlPreviewReq(BaseModel):
    """ETL 抽取预览:批量源按原生查询取样本;流式源抽 1 条事件。均支持逐行转换。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    datasource_code: str | None = Field(default=None, description='源数据源编码(代码取数时可空)')
    native: Any = Field(default=None, description='原生查询(批量源:SQL 串 / DSL dict)')
    object_name: str | None = Field(default=None, description='表/主题(流式源过滤)')
    transform_code: str | None = Field(default=None, description='逐行转换 transform(row),预览转换后形态')
    limit: int = Field(default=50, description='预览条数(强制上限 200;流式源固定抽 1 条)')
    # 代码取数(沙箱预览):mode=code 时用 code 跑出 result(list[dict]),datasource_codes 为代码可用的源
    mode: str | None = Field(default=None, description='抽取方式 datasource(默认)/ code 代码取数')
    code: str | None = Field(default=None, description='代码取数:产出 result(list[dict]) 的 Python')
    datasource_codes: list[str] | None = Field(default=None, description='代码取数:get_handler 可用的数据源编码')


class EtlTestLoadReq(BaseModel):
    """ETL 测试写入:把预览样本写入目标,验证装载配置。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    datasource_code: str = Field(description='目标数据源编码')
    table: str = Field(description='目标表(文件目标时为对象 key)')
    mode: str = Field(default='append', description='写入模式 append/replace/merge')
    dataset: str = Field(default='public', description='目标数据集/库')
    format: str | None = Field(default='csv', description='文件目标的序列化格式 csv/json/jsonl')
    records: list[dict] = Field(description='待写入的样本记录(来自预览)')


class EtlAiQueryReq(BaseModel):
    """ETL AI 生成原生查询:自然语言 + 源表结构 → 原生查询。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    datasource_code: str = Field(description='源数据源编码')
    object_names: list[str] | None = Field(default=None, description='相关表(空=全库结构,支持连表)')
    question: str = Field(description='自然语言需求')


class EtlAiTransformReq(BaseModel):
    """ETL AI 生成转换函数:自然语言 + 字段 → transform(row)。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    question: str = Field(description='自然语言需求')
    columns: list[str] | None = Field(default=None, description='可用字段名(来自预览)')


class EtlAiExtractReq(BaseModel):
    """ETL AI 生成取数代码:自然语言 → 产出 result(list[dict]) 的 Python(爬虫/任意取数)。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    question: str = Field(description='自然语言需求(要抓什么数据)')
    datasource_codes: list[str] | None = Field(default=None, description='代码里可用 get_handler 的数据源编码')


class DeleteReq(BaseModel):
    """批量删除(逗号分隔 id)。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    ids: str = Field(description='逗号分隔的主键')


class AnalysisTemplateVo(BaseModel):
    """数据分析模板 VO。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str | None = Field(default=None, description='主键')
    name: str | None = Field(default=None, description='模板名称')
    model_id: str | None = Field(default=None, description='数据模型ID')
    model_name: str | None = Field(default=None, description='数据模型名')
    query: dict | None = Field(default=None, description='取数配置 {type,native/filters/question}')
    chart_spec: Any | None = Field(default=None, description='图表配置(EchartsBuilder cfg:type/x/ys/series/sort/style)')
    params: Any | None = Field(default=None, description='看板变量定义+当前值 [{name,label,type,default,value,options}]')
    refresh_interval: int | None = Field(default=None, description='自动刷新间隔(秒,0=不刷新)')
    share_token: str | None = Field(default=None, description='匿名分享令牌(空=未开启)')
    remark: str | None = Field(default=None, description='备注')
    create_by: str | None = Field(default=None, description='创建者')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_time: datetime | None = Field(default=None, description='更新时间')


class DashboardVo(BaseModel):
    """看板/大屏 VO(dash_type=board/screen)。列表只返回基础字段;详情/保存带 canvas/components/filters。"""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: str | None = Field(default=None, description='主键')
    name: str | None = Field(default=None, description='名称')
    dash_type: str | None = Field(default='board', description='chart/board/screen')
    share_token: str | None = Field(default=None, description='匿名分享令牌(空=未开启)')
    refresh_interval: int | None = Field(default=None, description='自动刷新间隔(秒,0=不刷新)')
    thumbnail: str | None = Field(default=None, description='缩略图(可选)')
    remark: str | None = Field(default=None, description='备注')
    canvas: Any | None = Field(default=None, description='画布设置 {mode,cols,width,height,background,theme,scaleMode}')
    components: Any | None = Field(default=None, description='组件数组 [{id,type,ref/inline,pos,props,subscribe,emit}]')
    filters: Any | None = Field(default=None, description='全局筛选/变量 [{name,label,type,default,options}]')
    create_time: datetime | None = Field(default=None, description='创建时间')
    update_time: datetime | None = Field(default=None, description='更新时间')
