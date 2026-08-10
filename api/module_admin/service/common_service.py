import asyncio
import hashlib
import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
from pathlib import Path
from typing import Literal

import aiofiles
from fastapi import BackgroundTasks, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession

from common.vo import CrudResponseModel
from config.env import StorageConfig, UploadConfig
from exceptions.exception import FileRangeNotSatisfiableException, ServiceException
from module_admin.dao.file_access_dao import FileAclDao
from module_admin.dao.file_info_dao import FileInfoDao
from module_admin.entity.do.file_do import SysFileInfo
from module_admin.entity.vo.common_vo import UploadResponseModel
from module_admin.entity.vo.file_vo import FileInfoModel
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.file_access_service import FileAuditService
from utils.file_util import FileByteRange, FileDownloadResult, FileUtil
from utils.storage_utils import storage
from utils.upload_util import FilePathUtil, UploadUtil


class CommonService:
    """
    通用模块服务层
    """

    @classmethod
    async def upload_service(
        cls,
        request: Request,
        query_db: AsyncSession,
        current_user: CurrentUserModel,
        file: UploadFile,
        access_type: Literal['public', 'private'] = 'public',
    ) -> CrudResponseModel:
        """
        通用上传service

        :param request: Request对象
        :param query_db: orm对象
        :param current_user: 当前用户对象
        :param file: 上传文件对象
        :param access_type: 文件访问类型
        :return: 上传结果
        """
        if access_type not in {'public', 'private'}:
            raise ServiceException(message='文件访问类型不合法')
        if not UploadUtil.check_file_extension(file):
            raise ServiceException(message='文件类型不合法')
        if file.size is not None and file.size > UploadConfig.MAX_FILE_SIZE:
            raise ServiceException(message=f'文件大小不能超过{UploadConfig.MAX_FILE_SIZE // 1024 // 1024}MB')

        now = datetime.now()
        relative_path = Path('upload', now.strftime('%Y'), now.strftime('%m'), now.strftime('%d'))
        file_id = str(uuid.uuid4())
        extension = UploadUtil.get_file_extension(file.filename)
        original_filename = UploadUtil.get_original_filename(file.filename)
        file_stem = UploadUtil.get_safe_file_stem(file.filename)
        storage_type = StorageConfig.storage_type

        # 按当前存储后端写入字节：s3 走对象存储抽象，local 保持原有磁盘落盘（含冲突重试）
        filename, storage_key, total_size, file_hash, filepath = await cls._persist_upload(
            file, access_type, relative_path, storage_type, now, extension, file_stem
        )

        user = current_user.user
        if user is None:
            cls._cleanup_stored_file(storage_type, access_type, storage_key, filepath)
            raise ServiceException(message='无法获取当前用户信息')

        try:
            file_info = FileInfoModel(
                fileId=file_id,
                originalName=original_filename,
                storedName=filename,
                storageKey=storage_key,
                storageType=storage_type,
                accessType=access_type,
                uploadUserId=user.user_id,
                ownerUserId=user.user_id,
                deptId=user.dept_id,
                extension=extension,
                contentType=file.content_type,
                fileSize=total_size,
                fileHash=file_hash,
                createBy=user.user_name,
                createTime=now,
                updateBy=user.user_name,
                updateTime=now,
            )
            await FileInfoDao.add_file_info_dao(query_db, file_info)
            await query_db.commit()
        except Exception:
            await query_db.rollback()
            cls._cleanup_stored_file(storage_type, access_type, storage_key, filepath)
            await cls._enqueue_file_access_log(
                request,
                current_user,
                file_id,
                action='upload',
                result='failed',
                error_message='文件信息写入失败',
            )
            raise

        download_path = f'/common/files/{file_id}/download/{filename}'
        if access_type == 'public':
            if storage_type == 's3':
                # 对象存储公有文件直接返回后端下载地址，不经 /profile 静态服务
                file_url = storage.get_download_url(cls._object_key(access_type, storage_key))
                file_name = file_url
            else:
                file_name = f'{UploadConfig.UPLOAD_PREFIX}/{storage_key}'
                file_url = f'{request.base_url}{UploadConfig.UPLOAD_PREFIX[1:]}/{storage_key}'
        else:
            file_name = download_path
            file_url = f'{request.base_url}{download_path.lstrip("/")}'

        await cls._enqueue_file_access_log(
            request,
            current_user,
            file_id,
            action='upload',
            result='completed',
            bytes_sent=total_size,
        )

        return CrudResponseModel(
            is_success=True,
            result=UploadResponseModel(
                fileName=file_name,
                newFileName=filename,
                originalFilename=original_filename,
                url=file_url,
                fileId=file_id,
                accessType=access_type,
                downloadUrl=download_path,
            ),
            message='上传成功',
        )

    @classmethod
    async def _persist_upload(
        cls,
        file: UploadFile,
        access_type: str,
        relative_path: Path,
        storage_type: str,
        now: datetime,
        extension: str,
        file_stem: str,
    ) -> tuple[str, str, int, str, Path | None]:
        """将上传字节写入存储后端。

        :return: (存储文件名, 存储相对键, 文件大小, SHA-256, 本地落盘路径或None[对象存储])
        """
        relative_path_url = relative_path.as_posix()

        def make_name() -> str:
            return (
                f'{file_stem}_{now.strftime("%Y%m%d%H%M%S")}'
                f'{UploadConfig.UPLOAD_MACHINE}{UploadUtil.generate_random_number()}.{extension}'
            )

        if storage_type == 's3':
            # 对象存储：文件名带时间戳与随机码，冲突概率可忽略；单桶内以 access_type 作前缀区分公私
            filename = make_name()
            storage_key = f'{relative_path_url}/{filename}'
            try:
                total_size, file_hash = await storage.save_upload(
                    file, cls._object_key(access_type, storage_key), UploadConfig.MAX_FILE_SIZE
                )
            except ValueError as exc:
                raise ServiceException(
                    message=f'文件大小不能超过{UploadConfig.MAX_FILE_SIZE // 1024 // 1024}MB'
                ) from exc
            return filename, storage_key, total_size, file_hash, None

        storage_root = UploadConfig.UPLOAD_PATH if access_type == 'public' else UploadConfig.PRIVATE_UPLOAD_PATH
        dir_path = Path(storage_root, relative_path)
        UploadUtil.ensure_directory(dir_path)
        for _ in range(10):
            filename = make_name()
            filepath = dir_path / filename
            try:
                total_size, file_hash = await cls._write_uploaded_file(file, filepath)
                break
            except FileExistsError:
                continue
        else:
            raise ServiceException(message='文件名生成冲突，请重新上传')
        storage_key = f'{relative_path_url}/{filename}'
        return filename, storage_key, total_size, file_hash, filepath

    @classmethod
    async def _write_uploaded_file(cls, file: UploadFile, filepath: Path) -> tuple[int, str]:
        """
        将上传文件写入目标路径并计算摘要

        :param file: 上传文件对象
        :param filepath: 文件目标路径
        :return: 文件大小和SHA-256
        """
        total_size = 0
        file_hasher = hashlib.sha256()
        file_created = False
        try:
            async with aiofiles.open(filepath, 'xb') as target_file:
                file_created = True
                while chunk := await file.read(1024 * 1024):
                    total_size += len(chunk)
                    if total_size > UploadConfig.MAX_FILE_SIZE:
                        raise ServiceException(
                            message=f'文件大小不能超过{UploadConfig.MAX_FILE_SIZE // 1024 // 1024}MB'
                        )
                    file_hasher.update(chunk)
                    await target_file.write(chunk)
        except Exception:
            if file_created and UploadUtil.check_file_exists(filepath):
                UploadUtil.delete_file(filepath)
            raise
        return total_size, file_hasher.hexdigest()

    @staticmethod
    def _object_key(access_type: str, storage_key: str) -> str:
        """对象存储物理键：单桶内以 access_type 作前缀区分公私（本地后端不用）。"""
        return FileUtil.build_object_storage_key(access_type, storage_key)

    @classmethod
    def _cleanup_stored_file(
        cls,
        storage_type: str,
        access_type: str,
        storage_key: str,
        filepath: Path | None,
    ) -> None:
        """写库失败等场景下清理已落地的文件字节（本地删磁盘 / s3 删对象），清理失败不影响主流程。"""
        try:
            if storage_type == 's3':
                storage.delete(cls._object_key(access_type, storage_key))
            elif filepath is not None and UploadUtil.check_file_exists(filepath):
                UploadUtil.delete_file(filepath)
        except Exception:
            pass

    @classmethod
    async def download_managed_file_services(
        cls,
        request: Request,
        query_db: AsyncSession,
        current_user: CurrentUserModel,
        file_id: str,
        enforce_owner_permission: bool = True,
        file_data_scope_sql: ColumnElement | None = None,
        range_header: str | None = None,
    ) -> FileDownloadResult:
        """
        下载已登记文件service

        :param request: Request对象
        :param query_db: orm对象
        :param current_user: 当前用户对象
        :param file_id: 文件ID
        :param enforce_owner_permission: 是否校验文件所有者权限
        :param file_data_scope_sql: 文件数据权限对应的查询sql语句
        :param range_header: Range请求头
        :return: 文件下载结果
        """
        file_info = await FileInfoDao.get_file_info_by_id(query_db, file_id, file_data_scope_sql)
        user = current_user.user
        if file_info is None or user is None:
            await cls._enqueue_file_access_log(
                request,
                current_user,
                file_id,
                action='download',
                result='denied',
                error_message='文件不存在或无权访问',
            )
            raise ServiceException(message='文件不存在或无权访问')
        if file_info.storage_type not in {'local', 's3'} or file_info.access_type not in {'public', 'private'}:
            await cls._enqueue_file_access_log(
                request,
                current_user,
                file_id,
                action='download',
                result='failed',
                error_message='文件存储类型或访问类型异常',
            )
            raise ServiceException(message='文件不存在或无权访问')

        current_time = datetime.now()
        is_expired = (
            file_info.access_type == 'private' and file_info.expire_time and file_info.expire_time < current_time
        )
        if is_expired:
            is_allowed = False
        elif not enforce_owner_permission or file_info.access_type == 'public':
            is_allowed = True
        else:
            is_allowed = await cls._has_private_file_download_permission(
                query_db,
                current_user,
                file_info,
                file_id,
                current_time,
            )
        if not is_allowed:
            await cls._enqueue_file_access_log(
                request,
                current_user,
                file_id,
                action='download',
                result='denied',
                error_message='文件不存在或无权访问',
            )
            raise ServiceException(message='文件不存在或无权访问')

        # 解析存储位置与大小：本地读磁盘（seek），s3 读对象存储（head/Range）
        try:
            if file_info.storage_type == 's3':
                object_key = cls._object_key(file_info.access_type, file_info.storage_key)
                file_size = await run_in_threadpool(storage.stat, object_key)

                def source_factory(br: FileByteRange) -> AsyncGenerator[bytes, None]:
                    return cls._aiter_sync(storage.load_range(object_key, br.start, br.length))
            else:
                storage_root = (
                    UploadConfig.UPLOAD_PATH
                    if file_info.access_type == 'public'
                    else UploadConfig.PRIVATE_UPLOAD_PATH
                )
                filepath = FilePathUtil.resolve_file_within_root(storage_root, file_info.storage_key)
                file_size = filepath.stat().st_size

                def source_factory(br: FileByteRange) -> AsyncGenerator[bytes, None]:
                    return UploadUtil.generate_file(filepath, start=br.start, length=br.length)
        except (FileNotFoundError, ValueError) as exc:
            await cls._enqueue_file_access_log(
                request,
                current_user,
                file_id,
                action='download',
                result='failed',
                error_message='文件不存在或存储路径异常',
            )
            raise ServiceException(message='文件不存在或无权访问') from exc
        try:
            byte_range = FileUtil.parse_byte_range(range_header, file_size)
        except FileRangeNotSatisfiableException:
            await cls._enqueue_file_access_log(
                request,
                current_user,
                file_id,
                action='download',
                result='failed',
                error_message='RangeNotSatisfiable',
                operation_detail={'range': range_header or ''},
            )
            raise

        original_name = file_info.original_name
        await query_db.rollback()
        await cls._enqueue_file_access_log(
            request,
            current_user,
            file_id,
            action='download',
            result='allowed',
            operation_detail=cls._build_download_operation_detail(byte_range),
        )
        stream = cls._generate_audited_file(request, current_user, file_id, source_factory(byte_range), byte_range)
        return FileDownloadResult(
            data=stream,
            filename=original_name,
            byte_range=byte_range,
        )

    @classmethod
    async def _has_private_file_download_permission(
        cls,
        query_db: AsyncSession,
        current_user: CurrentUserModel,
        file_info: SysFileInfo,
        file_id: str,
        current_time: datetime,
    ) -> bool:
        """
        校验私有文件下载权限

        :param query_db: orm对象
        :param current_user: 当前用户对象
        :param file_info: 文件信息
        :param file_id: 文件ID
        :param current_time: 当前时间
        :return: 是否允许下载
        """
        user = current_user.user
        if user is None or user.user_id is None:
            return False
        if bool(getattr(user, 'admin', False)) or user.user_id == file_info.owner_user_id:
            return True

        file_acl_list = await FileAclDao.get_effective_file_acl_list(query_db, file_id, current_time)
        role_ids = cls._get_current_user_role_ids(user)
        dept_id, ancestor_dept_ids = cls._get_current_user_dept_ids(user)
        matched_effects = []
        for file_acl in file_acl_list:
            is_matched = False
            if file_acl.subject_type == 'user':
                is_matched = file_acl.subject_id == user.user_id
            elif file_acl.subject_type == 'role':
                is_matched = file_acl.subject_id in role_ids
            elif file_acl.subject_type == 'dept':
                is_matched = file_acl.subject_id == dept_id or (
                    file_acl.include_children in {'1', True} and file_acl.subject_id in ancestor_dept_ids
                )
            if is_matched:
                matched_effects.append(file_acl.effect)

        if 'deny' in matched_effects:
            return False
        if user.user_id == file_info.upload_user_id and getattr(file_info, 'uploader_access_enabled', '1') in {
            '1',
            True,
        }:
            return True
        return 'allow' in matched_effects

    @staticmethod
    def _get_current_user_role_ids(user: object) -> set[int]:
        """
        获取当前用户角色ID集合

        :param user: 当前用户对象
        :return: 角色ID集合
        """
        role_ids = {
            role.role_id
            for role in (getattr(user, 'role', None) or [])
            if role is not None and getattr(role, 'role_id', None) is not None
        }
        role_ids_text = getattr(user, 'role_ids', None)
        if role_ids_text:
            role_ids.update(int(role_id) for role_id in role_ids_text.split(',') if role_id.strip().isdigit())
        return role_ids

    @staticmethod
    def _get_current_user_dept_ids(user: object) -> tuple[int | None, set[int]]:
        """
        获取当前用户部门及祖级部门ID

        :param user: 当前用户对象
        :return: 当前部门ID和祖级部门ID集合
        """
        dept = getattr(user, 'dept', None)
        dept_id = getattr(user, 'dept_id', None) or getattr(dept, 'dept_id', None)
        ancestors = getattr(dept, 'ancestors', None) or ''
        ancestor_dept_ids = {int(ancestor_id) for ancestor_id in ancestors.split(',') if ancestor_id.strip().isdigit()}
        return dept_id, ancestor_dept_ids

    @staticmethod
    async def _aiter_sync(sync_gen: Generator[bytes, None, None]) -> AsyncGenerator[bytes, None]:
        """把同步字节生成器（如 s3 的 Range 读）逐块搬到线程池，避免网络读阻塞事件循环。"""
        it = iter(sync_gen)
        sentinel = object()
        while True:
            chunk = await run_in_threadpool(next, it, sentinel)
            if chunk is sentinel:
                break
            yield chunk

    @classmethod
    async def _generate_audited_file(
        cls,
        request: Request,
        current_user: CurrentUserModel,
        file_id: str,
        source: AsyncGenerator[bytes, None],
        byte_range: FileByteRange,
    ) -> AsyncGenerator[bytes, None]:
        """
        生成带有完成审计的文件流

        :param request: Request对象
        :param current_user: 当前用户对象
        :param file_id: 文件ID
        :param source: 字节数据源（本地磁盘或对象存储的 Range 读，均为异步字节生成器）
        :param byte_range: 文件字节范围
        :yield: 文件二进制数据
        """
        bytes_sent = 0
        audit_result: Literal['completed', 'failed'] = 'failed'
        error_message = 'StreamClosed'
        try:
            async for chunk in source:
                bytes_sent += len(chunk)
                yield chunk
            if bytes_sent != byte_range.length:
                raise OSError('文件在下载期间发生变化')
        except asyncio.CancelledError:
            error_message = 'CancelledError'
            raise
        except Exception as exc:
            error_message = exc.__class__.__name__
            raise
        else:
            audit_result = 'completed'
            error_message = ''
        finally:
            await cls._enqueue_file_access_log(
                request,
                current_user,
                file_id,
                action='download',
                result=audit_result,
                bytes_sent=bytes_sent,
                error_message=error_message,
                operation_detail=cls._build_download_operation_detail(byte_range),
            )

    @classmethod
    async def _enqueue_file_access_log(
        cls,
        request: Request,
        current_user: CurrentUserModel,
        file_id: str,
        action: Literal['upload', 'download'],
        result: Literal['allowed', 'denied', 'completed', 'failed'],
        bytes_sent: int = 0,
        error_message: str = '',
        operation_detail: dict[str, object] | None = None,
    ) -> None:
        """
        将文件访问审计写入日志队列

        :param request: Request对象
        :param current_user: 当前用户对象
        :param file_id: 文件ID
        :param action: 操作类型
        :param result: 操作结果
        :param bytes_sent: 已发送字节数
        :param error_message: 失败原因
        :param operation_detail: 操作详情
        :return: None
        """
        await FileAuditService.enqueue_file_audit(
            request,
            current_user,
            file_id,
            action,
            result,
            bytes_sent=bytes_sent,
            error_message=error_message,
            operation_detail=operation_detail,
        )

    @staticmethod
    def _build_download_operation_detail(byte_range: FileByteRange) -> dict[str, object] | None:
        """
        构造分段下载审计详情

        :param byte_range: 文件字节范围
        :return: 分段下载审计详情
        """
        if not byte_range.is_partial:
            return None
        return {
            'rangeStart': byte_range.start,
            'rangeEnd': byte_range.end,
            'fileSize': byte_range.file_size,
        }

    @classmethod
    async def download_services(
        cls,
        background_tasks: BackgroundTasks,
        file_name: str,
        delete: bool,
        range_header: str | None = None,
    ) -> FileDownloadResult:
        """
        下载下载目录文件service

        :param background_tasks: 后台任务对象
        :param file_name: 下载的文件名称
        :param delete: 是否在下载完成后删除文件
        :param range_header: Range请求头
        :return: 文件下载结果
        """
        try:
            filepath = FilePathUtil.resolve_file_within_root(UploadConfig.DOWNLOAD_PATH, file_name)
        except (FileNotFoundError, ValueError) as exc:
            raise ServiceException(message='文件名称不合法或文件不存在') from exc
        accept_ranges = not delete
        byte_range = FileUtil.parse_byte_range(range_header if accept_ranges else None, filepath.stat().st_size)
        if delete:
            background_tasks.add_task(UploadUtil.delete_file, filepath)
        return FileDownloadResult(
            data=UploadUtil.generate_file(
                filepath,
                start=byte_range.start,
                length=byte_range.length,
            ),
            filename=file_name,
            byte_range=byte_range,
            accept_ranges=accept_ranges,
        )

    @classmethod
    async def download_resource_services(
        cls,
        resource: str,
        range_header: str | None = None,
    ) -> FileDownloadResult:
        """
        下载上传目录文件service

        :param resource: 下载的文件名称
        :param range_header: Range请求头
        :return: 文件下载结果
        """
        resource_prefix = f'{UploadConfig.UPLOAD_PREFIX.rstrip("/")}/'
        if not resource.startswith(resource_prefix):
            raise ServiceException(message='资源路径不合法')
        relative_resource = resource[len(resource_prefix) :]
        try:
            filepath = FilePathUtil.resolve_file_within_root(UploadConfig.UPLOAD_PATH, relative_resource)
        except (FileNotFoundError, ValueError) as exc:
            raise ServiceException(message='资源路径不合法或文件不存在') from exc
        filename = filepath.name
        if (
            '..' in filename
            or not UploadUtil.check_file_timestamp(filename)
            or not UploadUtil.check_file_machine(filename)
            or not UploadUtil.check_file_random_code(filename)
            or UploadUtil.get_file_extension(filename) not in UploadConfig.DEFAULT_ALLOWED_EXTENSION
        ):
            raise ServiceException(message='资源文件名称不合法')
        byte_range = FileUtil.parse_byte_range(range_header, filepath.stat().st_size)
        return FileDownloadResult(
            data=UploadUtil.generate_file(
                filepath,
                start=byte_range.start,
                length=byte_range.length,
            ),
            filename=filename,
            byte_range=byte_range,
        )
