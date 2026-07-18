from typing import Any

from sqlalchemy import ColumnElement, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_ai.entity.do.ai_skill_do import AiSkill
from module_ai.entity.vo.ai_skill_vo import AiSkillPageQueryModel
from utils.page_util import PageUtil


class AiSkillDao:
    """AI技能管理数据库操作层"""

    @classmethod
    async def get_ai_skill_detail_by_id(cls, db: AsyncSession, skill_id: int) -> AiSkill | None:
        return (await db.execute(select(AiSkill).where(AiSkill.skill_id == skill_id))).scalars().first()

    @classmethod
    async def get_ai_skill_by_code(cls, db: AsyncSession, code: str) -> AiSkill | None:
        return (await db.execute(select(AiSkill).where(AiSkill.code == code))).scalars().first()

    @classmethod
    async def get_ai_skill_list(
        cls, db: AsyncSession, query_object: AiSkillPageQueryModel, data_scope_sql: ColumnElement, is_page: bool = False
    ) -> PageModel | list[dict[str, Any]]:
        kw = query_object.keyword
        query = (
            select(AiSkill)
            .where(
                or_(AiSkill.name.like(f'%{kw}%'), AiSkill.code.like(f'%{kw}%')) if kw else True,
                AiSkill.status == query_object.status if query_object.status else True,
                data_scope_sql,
            )
            .order_by(AiSkill.skill_id)
        )
        return await PageUtil.paginate(db, query, query_object.page_num, query_object.page_size, is_page)

    @classmethod
    async def get_by_codes(cls, db: AsyncSession, codes: list[str]) -> list[AiSkill]:
        """按 code 批量取技能(忽略 status,供软引用解析——被引用的"库技能"可停用不进清单但仍可加载)。"""
        if not codes:
            return []
        return list((await db.execute(select(AiSkill).where(AiSkill.code.in_(codes)))).scalars().all())

    @classmethod
    async def list_enabled(cls, db: AsyncSession, skill_ids: list[int] | None = None) -> list[AiSkill]:
        """取启用的技能;skill_ids 为空 → 全部启用(普通对话),否则按 id 过滤(应用绑定)。"""
        stmt = select(AiSkill).where(AiSkill.status == '0')
        if skill_ids:
            stmt = stmt.where(AiSkill.skill_id.in_(skill_ids))
        return list((await db.execute(stmt.order_by(AiSkill.skill_id))).scalars().all())

    @classmethod
    async def add_ai_skill_dao(cls, db: AsyncSession, data: dict) -> AiSkill:
        db_obj = AiSkill(**data)
        db.add(db_obj)
        await db.flush()
        return db_obj

    @classmethod
    async def edit_ai_skill_dao(cls, db: AsyncSession, data: dict) -> None:
        await db.execute(update(AiSkill), [data])

    @classmethod
    async def delete_ai_skill_dao(cls, db: AsyncSession, skill_id: int) -> None:
        await db.execute(delete(AiSkill).where(AiSkill.skill_id == skill_id))
