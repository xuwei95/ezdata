from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from common.constant import CommonConstant
from common.vo import CrudResponseModel, PageModel
from exceptions.exception import ServiceException
from module_admin.dao.notice_dao import NoticeDao
from module_admin.entity.vo.notice_vo import (
    DeleteNoticeModel,
    NoticeModel,
    NoticePageQueryModel,
    NoticeReadUserPageQueryModel,
    NoticeTopModel,
    NoticeTopResponseModel,
)
from utils.common_util import CamelCaseUtil


class NoticeService:
    """
    通知公告管理模块服务层
    """

    TOP_NOTICE_LIMIT = 5

    @classmethod
    async def get_notice_top_services(cls, query_db: AsyncSession, user_id: int) -> NoticeTopResponseModel:
        """
        获取首页顶部通知公告及当前用户已读状态

        :param query_db: orm对象
        :param user_id: 用户ID
        :return: 首页顶部通知公告响应对象
        """
        notice_list = await NoticeDao.get_notice_list_with_read_status(query_db, user_id, cls.TOP_NOTICE_LIMIT)
        notice_models = [NoticeTopModel(**CamelCaseUtil.transform_result(notice)) for notice in notice_list]
        unread_count = sum(not notice.is_read for notice in notice_models)

        return NoticeTopResponseModel(data=notice_models, unreadCount=unread_count)

    @classmethod
    async def get_notice_read_user_list_services(
        cls, query_db: AsyncSession, query_object: NoticeReadUserPageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取公告已读用户列表

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 已读用户列表
        """
        return await NoticeDao.get_notice_read_user_list(query_db, query_object, is_page)

    @classmethod
    async def mark_notice_read_services(
        cls, query_db: AsyncSession, user_id: int, notice_ids: list[int]
    ) -> CrudResponseModel:
        """
        标记通知公告已读

        :param query_db: orm对象
        :param user_id: 用户ID
        :param notice_ids: 公告ID列表
        :return: 操作结果
        """
        try:
            await NoticeDao.add_notice_reads(query_db, user_id, notice_ids)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='标记成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    def parse_notice_ids(cls, notice_ids: str) -> list[int]:
        """
        解析逗号分隔的公告ID

        :param notice_ids: 逗号分隔的公告ID
        :return: 去重后的公告ID列表
        """
        try:
            return list(
                dict.fromkeys(int(notice_id.strip()) for notice_id in notice_ids.split(',') if notice_id.strip())
            )
        except ValueError as exc:
            raise ServiceException(message='公告ID格式不正确') from exc

    @classmethod
    async def get_notice_list_services(
        cls, query_db: AsyncSession, query_object: NoticePageQueryModel, is_page: bool = True
    ) -> PageModel | list[dict[str, Any]]:
        """
        获取通知公告列表信息service

        :param query_db: orm对象
        :param query_object: 查询参数对象
        :param is_page: 是否开启分页
        :return: 通知公告列表信息对象
        """
        notice_list_result = await NoticeDao.get_notice_list(query_db, query_object, is_page)

        return notice_list_result

    @classmethod
    async def check_notice_unique_services(cls, query_db: AsyncSession, page_object: NoticeModel) -> bool:
        """
        校验通知公告是否存在service

        :param query_db: orm对象
        :param page_object: 通知公告对象
        :return: 校验结果
        """
        notice_id = -1 if page_object.notice_id is None else page_object.notice_id
        notice = await NoticeDao.get_notice_detail_by_info(query_db, page_object)
        if notice and notice.notice_id != notice_id:
            return CommonConstant.NOT_UNIQUE
        return CommonConstant.UNIQUE

    @classmethod
    async def _sync_notice_recipients(cls, query_db: AsyncSession, notice_id: int, notice_users: str | None) -> None:
        """按 notice_users(逗号用户名)重设某公告的收件人:先清后加。
        None=不改动(未提交收件人字段);空串=广播(清空收件人);有名字=定向。
        """
        if notice_users is None:
            return
        await NoticeDao.delete_notice_users(query_db, [notice_id])
        names = [n.strip() for n in notice_users.split(',') if n.strip()]
        if names:
            user_ids = await NoticeDao.resolve_user_ids_by_names_async(query_db, names)
            NoticeDao.add_notice_users(query_db, notice_id, user_ids)

    @classmethod
    async def add_notice_services(cls, query_db: AsyncSession, page_object: NoticeModel) -> CrudResponseModel:
        """
        新增通知公告信息service

        :param query_db: orm对象
        :param page_object: 新增通知公告对象
        :return: 新增通知公告校验结果
        """
        if not await cls.check_notice_unique_services(query_db, page_object):
            raise ServiceException(message=f'新增通知公告{page_object.notice_title}失败，通知公告已存在')
        try:
            db_notice = await NoticeDao.add_notice_dao(query_db, page_object)
            # 选了收件人 → 定向投递;留空 → 广播(不写收件人行)
            await cls._sync_notice_recipients(query_db, db_notice.notice_id, page_object.notice_users)
            await query_db.commit()
            return CrudResponseModel(is_success=True, message='新增成功')
        except Exception as e:
            await query_db.rollback()
            raise e

    @classmethod
    async def edit_notice_services(cls, query_db: AsyncSession, page_object: NoticeModel) -> CrudResponseModel:
        """
        编辑通知公告信息service

        :param query_db: orm对象
        :param page_object: 编辑通知公告对象
        :return: 编辑通知公告校验结果
        """
        edit_notice = page_object.model_dump(exclude_unset=True)
        # notice_users 非 sys_notice 列,单独处理,构造更新前先剔除
        edit_notice.pop('notice_users', None)
        notice_info = await cls.notice_detail_services(query_db, page_object.notice_id)
        if notice_info.notice_id:
            if not await cls.check_notice_unique_services(query_db, page_object):
                raise ServiceException(message=f'修改通知公告{page_object.notice_title}失败，通知公告已存在')
            try:
                await NoticeDao.edit_notice_dao(query_db, edit_notice)
                # 重设收件人(留空=改回广播)
                await cls._sync_notice_recipients(query_db, page_object.notice_id, page_object.notice_users)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='更新成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='通知公告不存在')

    @classmethod
    async def delete_notice_services(cls, query_db: AsyncSession, page_object: DeleteNoticeModel) -> CrudResponseModel:
        """
        删除通知公告信息service

        :param query_db: orm对象
        :param page_object: 删除通知公告对象
        :return: 删除通知公告校验结果
        """
        if page_object.notice_ids:
            notice_id_list = page_object.notice_ids.split(',')
            try:
                for notice_id in notice_id_list:
                    await NoticeDao.delete_notice_dao(query_db, NoticeModel(noticeId=notice_id))
                # 连带清理这些公告的已读记录 + 收件人记录,避免残留脏数据
                ids_int = [int(nid) for nid in notice_id_list]
                await NoticeDao.delete_notice_reads(query_db, ids_int)
                await NoticeDao.delete_notice_users(query_db, ids_int)
                await query_db.commit()
                return CrudResponseModel(is_success=True, message='删除成功')
            except Exception as e:
                await query_db.rollback()
                raise e
        else:
            raise ServiceException(message='传入通知公告id为空')

    @classmethod
    async def notice_detail_services(cls, query_db: AsyncSession, notice_id: int) -> NoticeModel:
        """
        获取通知公告详细信息service

        :param query_db: orm对象
        :param notice_id: 通知公告id
        :return: 通知公告id对应的信息
        """
        notice = await NoticeDao.get_notice_detail_by_id(query_db, notice_id=notice_id)
        if not notice:
            return NoticeModel()
        result = NoticeModel(**CamelCaseUtil.transform_result(notice))
        # 回填收件人(逗号用户名;空=广播),供编辑表单预填
        result.notice_users = ','.join(await NoticeDao.get_notice_user_names(query_db, notice_id))
        return result
