from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import PageModel
from module_apitoken.entity.do.api_token_do import ApiToken
from module_apitoken.entity.vo.api_token_vo import ApiTokenQuery
from utils.page_util import PageUtil


class ApiTokenDao:
    """通用 API Token DAO。"""

    @classmethod
    async def get_by_id(cls, db: AsyncSession, t_id: str) -> ApiToken | None:
        return (await db.execute(select(ApiToken).where(ApiToken.id == t_id))).scalars().first()

    @classmethod
    async def get_by_token(cls, db: AsyncSession, token: str) -> ApiToken | None:
        return (await db.execute(select(ApiToken).where(ApiToken.token == token))).scalars().first()

    @classmethod
    async def get_list(cls, db: AsyncSession, q: ApiTokenQuery, is_page: bool = False) -> PageModel | list:
        query = (
            select(ApiToken)
            .where(
                ApiToken.name.like(f'%{q.name}%') if q.name else True,
                ApiToken.token_type == q.token_type if q.token_type else True,
                ApiToken.ref_id == q.ref_id if q.ref_id else True,
            )
            .order_by(ApiToken.create_time.desc())
        )
        return await PageUtil.paginate(db, query, q.page_num, q.page_size, is_page)

    @classmethod
    async def add(cls, db: AsyncSession, obj: dict) -> ApiToken:
        do = ApiToken(**obj)
        db.add(do)
        await db.flush()
        return do

    @classmethod
    async def edit(cls, db: AsyncSession, t_id: str, data: dict) -> None:
        do = await cls.get_by_id(db, t_id)
        if do:
            for k, v in data.items():
                setattr(do, k, v)
            await db.flush()

    @classmethod
    async def remove(cls, db: AsyncSession, ids: list[str]) -> None:
        await db.execute(delete(ApiToken).where(ApiToken.id.in_(ids)))
