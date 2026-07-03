"""module_data —— 数据源 web 层(controller/service/dao/entity)。

连接器与数据访问核已抽到独立的 ezdata 包(纯数据 SDK,零 db/web/config)。本包是其 web 宿主:
CRUD/鉴权/AI/沙箱在此,数据访问委托 ezdata.services。

导入即向 ezdata 注入宿主的密文解密器:web 与 worker 取到的 secrets 为 AES 密文串,
需靠它在 handler 构造时解密(见 ezdata.services.secrets)。沙箱传明文 dict,不导入本包、天然不碰加密。
"""

from ezdata.services.secrets import set_decryptor as _set_decryptor
from utils.crypto_util import CryptoUtil as _CryptoUtil

_set_decryptor(_CryptoUtil.decrypt)
