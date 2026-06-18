import secrets as _secrets
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from exceptions.exception import ServiceException
from module_apitoken.dao.api_token_dao import ApiTokenDao
from module_apitoken.entity.vo.api_token_vo import ApiTokenQuery, ApiTokenVo


class ApiTokenService:
    """通用 API Token 服务(apikey 校验,data_api/agent 等用途复用)。"""

    @classmethod
    async def get_list(cls, db: AsyncSession, q: ApiTokenQuery, is_page: bool = False) -> Any:
        return await ApiTokenDao.get_list(db, q, is_page)

    @classmethod
    async def add(cls, db: AsyncSession, vo: ApiTokenVo, operator: str) -> CrudResponseModel:
        try:
            obj = {
                'id': uuid.uuid4().hex,
                'name': vo.name,
                'token': 'sk_' + _secrets.token_urlsafe(24),
                'token_type': vo.token_type or 'data_api',
                'ref_id': vo.ref_id, 'status': 1, 'expire_time': vo.expire_time, 'remark': vo.remark,
                'create_by': operator, 'create_time': datetime.now(),
            }
            await ApiTokenDao.add(db, obj)
            await db.commit()
            return CrudResponseModel(is_success=True, message='已生成 apikey')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def delete(cls, db: AsyncSession, ids: str) -> CrudResponseModel:
        try:
            await ApiTokenDao.remove(db, [i for i in ids.split(',') if i])
            await db.commit()
            return CrudResponseModel(is_success=True, message='删除成功')
        except Exception as e:
            await db.rollback()
            raise e

    @classmethod
    async def validate(cls, db: AsyncSession, apikey: str, token_type: str, ref_id: str | None = None) -> None:
        """校验 apikey:存在、启用、类型匹配、未过期、资源范围匹配。失败抛 ServiceException。

        任意业务模块(数据接口 / agent 对话 / ...)均可调用本方法做 apikey 鉴权。
        """
        if not apikey:
            raise ServiceException(message='缺少 apikey')
        tk = await ApiTokenDao.get_by_token(db, apikey)
        if not tk or tk.status != 1:
            raise ServiceException(message='无效 apikey')
        if tk.token_type != token_type:
            raise ServiceException(message=f'apikey 类型不匹配(需 {token_type})')
        if tk.expire_time and tk.expire_time < datetime.now():
            raise ServiceException(message='apikey 已过期')
        if tk.ref_id and ref_id and tk.ref_id != ref_id:
            raise ServiceException(message='apikey 无权访问该资源')
