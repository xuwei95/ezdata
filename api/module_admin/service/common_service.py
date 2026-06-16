import os
from datetime import datetime

from fastapi import BackgroundTasks, Request, UploadFile
from fastapi.concurrency import run_in_threadpool

from common.vo import CrudResponseModel
from config.env import StorageConfig, UploadConfig
from exceptions.exception import ServiceException
from module_admin.entity.vo.common_vo import UploadResponseModel
from utils.storage_utils import storage
from utils.upload_util import UploadUtil


class CommonService:
    """
    通用模块服务层
    """

    @classmethod
    async def upload_service(cls, request: Request, file: UploadFile) -> CrudResponseModel:
        """
        通用上传service

        :param request: Request对象
        :param file: 上传文件对象
        :return: 上传结果
        """
        if not UploadUtil.check_file_extension(file):
            raise ServiceException(message='文件类型不合法')
        relative_path = (
            f'upload/{datetime.now().strftime("%Y")}/{datetime.now().strftime("%m")}/{datetime.now().strftime("%d")}'
        )
        filename = f'{file.filename.rsplit(".", 1)[0]}_{datetime.now().strftime("%Y%m%d%H%M%S")}{UploadConfig.UPLOAD_MACHINE}{UploadUtil.generate_random_number()}.{file.filename.rsplit(".")[-1]}'
        # 对象键：相对路径 + 文件名（local 后端落在 UPLOAD_PATH 下，与 /profile 静态服务一致）
        object_key = f'{relative_path}/{filename}'
        # 通过存储抽象写入（local 写磁盘 / s3 写 MinIO）。后端为同步实现，放线程池避免阻塞事件循环
        data = await file.read()
        await run_in_threadpool(storage.save, object_key, data)

        # local 走 /profile 静态访问；s3/MinIO 走对象存储下载地址
        if StorageConfig.storage_type == 's3':
            url = storage.get_download_url(object_key)
        else:
            url = f'{request.base_url}{UploadConfig.UPLOAD_PREFIX[1:]}/{object_key}'

        return CrudResponseModel(
            is_success=True,
            result=UploadResponseModel(
                fileName=f'{UploadConfig.UPLOAD_PREFIX}/{object_key}',
                newFileName=filename,
                originalFilename=file.filename,
                url=url,
            ),
            message='上传成功',
        )

    @classmethod
    async def download_services(
        cls, background_tasks: BackgroundTasks, file_name: str, delete: bool
    ) -> CrudResponseModel:
        """
        下载下载目录文件service

        :param background_tasks: 后台任务对象
        :param file_name: 下载的文件名称
        :param delete: 是否在下载完成后删除文件
        :return: 上传结果
        """
        filepath = os.path.join(UploadConfig.DOWNLOAD_PATH, file_name)
        if '..' in file_name:
            raise ServiceException(message='文件名称不合法')
        if not UploadUtil.check_file_exists(filepath):
            raise ServiceException(message='文件不存在')
        if delete:
            background_tasks.add_task(UploadUtil.delete_file, filepath)
        return CrudResponseModel(is_success=True, result=UploadUtil.generate_file(filepath), message='下载成功')

    @classmethod
    async def download_resource_services(cls, resource: str) -> CrudResponseModel:
        """
        下载上传目录文件service

        :param resource: 下载的文件名称
        :return: 上传结果
        """
        # 还原对象键：去掉 /profile 前缀与前导斜杠（local/s3 后端统一用相对键）
        object_key = resource.split(UploadConfig.UPLOAD_PREFIX, 1)[-1].lstrip('/')
        filename = resource.rsplit('/', 1)[-1]
        if (
            '..' in filename
            or not UploadUtil.check_file_timestamp(filename)
            or not UploadUtil.check_file_machine(filename)
            or not UploadUtil.check_file_random_code(filename)
        ):
            raise ServiceException(message='文件名称不合法')
        if not await run_in_threadpool(storage.exists, object_key):
            raise ServiceException(message='文件不存在')
        # 经存储抽象流式读取（local 读磁盘 / s3 读 MinIO）
        return CrudResponseModel(is_success=True, result=storage.load_stream(object_key), message='下载成功')
