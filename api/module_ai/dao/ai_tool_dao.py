from typing import Any

from sqlalchemy import ColumnElement, and_, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_ai.entity.do.ai_tool_do import AiTool
from module_ai.entity.vo.ai_tool_vo import AiToolPageQueryModel
from utils.page_util import PageUtil


class AiToolDao:
    """
    AI工具管理数据库操作层
    """

    @classmethod
    async def get_ai_tool_detail_by_id(cls, db: AsyncSession, tool_id: int) -> AiTool | None:
        """根据工具id获取工具详情"""
        return (await db.execute(select(AiTool).where(AiTool.tool_id == tool_id))).scalars().first()

    @classmethod
    async def get_ai_tool_by_code(cls, db: AsyncSession, code: str) -> AiTool | None:
        """根据 code 获取工具(校验唯一)"""
        return (await db.execute(select(AiTool).where(AiTool.code == code))).scalars().first()

    @classmethod
    async def get_ai_tool_list(
        cls, db: AsyncSession, query_object: AiToolPageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        """根据查询参数获取工具列表"""
        kw = query_object.keyword
        query = (
            select(AiTool)
            .where(
                or_(AiTool.name.like(f'%{kw}%'), AiTool.code.like(f'%{kw}%')) if kw else True,
                AiTool.tool_type == query_object.tool_type if query_object.tool_type else True,
                AiTool.status == query_object.status if query_object.status else True,
                data_scope_sql,
            )
            .order_by(AiTool.tool_type.desc(), AiTool.tool_id)
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def add_ai_tool_dao(cls, db: AsyncSession, data: dict) -> AiTool:
        """新增工具(data 中 args 已序列化为 JSON 串)"""
        db_obj = AiTool(**data)
        db.add(db_obj)
        await db.flush()
        return db_obj

    @classmethod
    async def edit_ai_tool_dao(cls, db: AsyncSession, data: dict) -> None:
        """编辑工具(data 含主键 tool_id)"""
        await db.execute(update(AiTool), [data])

    @classmethod
    async def delete_ai_tool_dao(cls, db: AsyncSession, tool_id: int) -> None:
        """删除工具"""
        await db.execute(delete(AiTool).where(and_(AiTool.tool_id == tool_id, AiTool.built_in != '1')))
