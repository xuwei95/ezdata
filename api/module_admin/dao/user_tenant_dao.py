import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from common.context import tenant_bypass
from module_admin.entity.do.dept_do import SysDept
from module_admin.entity.do.user_tenant_do import SysUserTenant


class UserTenantDao:
    """用户-租户成员关系 DAO。

    SysUserTenant 非多租户表(不被过滤);涉及顶级部门(SysDept,多租户表)的读取在本类内
    用 tenant_bypass 兜底,保证跨租户可读(列租户名 / admin 取全部租户)。
    """

    @classmethod
    async def list_by_user(cls, db: AsyncSession, user_id: int) -> list[SysUserTenant]:
        """某用户的全部租户成员记录"""
        return (
            await db.execute(select(SysUserTenant).where(SysUserTenant.user_id == user_id))
        ).scalars().all()

    @classmethod
    async def is_member(cls, db: AsyncSession, user_id: int, tenant_id: int) -> bool:
        """用户是否为某租户成员"""
        row = (
            await db.execute(
                select(SysUserTenant.id).where(
                    SysUserTenant.user_id == user_id, SysUserTenant.tenant_id == tenant_id
                )
            )
        ).first()
        return row is not None

    @classmethod
    async def get_default_tenant(cls, db: AsyncSession, user_id: int) -> int | None:
        """用户的默认激活租户:优先 is_default,否则任一成员;无成员返回 None"""
        rows = (
            await db.execute(
                select(SysUserTenant.tenant_id, SysUserTenant.is_default).where(
                    SysUserTenant.user_id == user_id
                )
            )
        ).all()
        if not rows:
            return None
        for tid, is_default in rows:
            if is_default:
                return tid
        return rows[0][0]

    @classmethod
    async def replace_user_tenants(
        cls, db: AsyncSession, user_id: int, tenant_ids: list[int], default_tenant_id: int | None = None
    ) -> None:
        """清空并重建某用户的租户成员(仿 user_role 同步);保证恰一个 is_default。不提交。"""
        await db.execute(delete(SysUserTenant).where(SysUserTenant.user_id == user_id))
        uniq = [t for i, t in enumerate(tenant_ids) if t is not None and t not in tenant_ids[:i]]
        if not uniq:
            return
        default_tid = default_tenant_id if default_tenant_id in uniq else uniq[0]
        for tid in uniq:
            db.add(
                SysUserTenant(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    tenant_id=tid,
                    is_default=(tid == default_tid),
                )
            )

    @classmethod
    async def add_if_absent(cls, db: AsyncSession, user_id: int, tenant_id: int, is_default: bool = False) -> bool:
        """无则插入一条成员;返回是否新增。不提交。"""
        if await cls.is_member(db, user_id, tenant_id):
            return False
        db.add(
            SysUserTenant(id=str(uuid.uuid4()), user_id=user_id, tenant_id=tenant_id, is_default=is_default)
        )
        return True

    @classmethod
    async def list_top_depts(cls, db: AsyncSession, tenant_ids: list[int] | None = None) -> list[tuple[int, str]]:
        """顶级部门(parent_id=0)= 租户;tenant_ids 给定则只取这些,否则全部。跨租户读,内部 bypass。"""
        with tenant_bypass():
            stmt = select(SysDept.dept_id, SysDept.dept_name).where(
                SysDept.parent_id == 0, SysDept.del_flag == '0'
            )
            if tenant_ids is not None:
                if not tenant_ids:
                    return []
                stmt = stmt.where(SysDept.dept_id.in_(tenant_ids))
            stmt = stmt.order_by(SysDept.order_num)
            return [(r[0], r[1]) for r in (await db.execute(stmt)).all()]
