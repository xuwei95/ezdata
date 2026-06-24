from typing import Any

from sqlalchemy import ColumnElement, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_ai.entity.do.ai_app_do import AiApp
from module_ai.entity.vo.ai_app_vo import AiAppPageQueryModel
from utils.page_util import PageUtil


class AiAppDao:
    """AI应用管理数据库操作层"""

    @classmethod
    async def get_ai_app_detail_by_id(cls, db: AsyncSession, app_id: int) -> AiApp | None:
        return (await db.execute(select(AiApp).where(AiApp.app_id == app_id))).scalars().first()

    @classmethod
    async def get_ai_app_list(
        cls, db: AsyncSession, query_object: AiAppPageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        kw = query_object.keyword
        query = (
            select(AiApp)
            .where(
                or_(AiApp.name.like(f'%{kw}%'), AiApp.description.like(f'%{kw}%')) if kw else True,
                AiApp.status == query_object.status if query_object.status else True,
                AiApp.app_type == query_object.app_type if query_object.app_type else True,
                data_scope_sql,
            )
            .order_by(AiApp.update_time.desc())
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def add_ai_app_dao(cls, db: AsyncSession, data: dict) -> AiApp:
        db_obj = AiApp(**data)
        db.add(db_obj)
        await db.flush()
        return db_obj

    @classmethod
    async def edit_ai_app_dao(cls, db: AsyncSession, data: dict) -> None:
        await db.execute(update(AiApp), [data])

    @classmethod
    async def delete_ai_app_dao(cls, db: AsyncSession, app_id: int) -> None:
        await db.execute(delete(AiApp).where(AiApp.app_id == app_id))
