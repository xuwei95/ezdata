from fastapi import Depends, params

from config.get_db import get_db


def DBSessionDependency() -> params.Depends:
    """
    数据库会话依赖

    :return: 数据库会话依赖
    """
    return Depends(get_db)
