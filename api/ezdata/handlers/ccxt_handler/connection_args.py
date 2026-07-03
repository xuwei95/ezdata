"""CCXT 连接参数:连加密货币交易所;公开行情免 key,私有接口可填密钥。"""

from collections import OrderedDict

from ezdata.handlers.const import ARG_TYPE

connection_args: 'OrderedDict[str, dict]' = OrderedDict(
    exchange={'type': ARG_TYPE.STR, 'label': '交易所',
              'description': 'ccxt 交易所 id,如 okx/gate/kraken/kucoin(中国网络可达);binance 等可能被墙。',
              'required': True},
    apiKey={'type': ARG_TYPE.PWD, 'label': 'API Key', 'description': '私有接口用(公开行情免填)。', 'secret': True},
    secret={'type': ARG_TYPE.PWD, 'label': 'API Secret', 'description': '私有接口用。', 'secret': True},
    password={'type': ARG_TYPE.PWD, 'label': 'Passphrase', 'description': '部分交易所(如 okx)私有接口需要。', 'secret': True},
    options={'type': ARG_TYPE.DICT, 'label': '额外参数', 'description': 'ccxt 构造额外项(如 {"defaultType":"spot"})。'},
)

connection_args_example: 'OrderedDict[str, dict]' = OrderedDict(exchange='okx')
