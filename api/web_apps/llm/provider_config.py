"""
LLM 提供商静态配置，读自环境变量
新增提供商：在 PROVIDER_CONFIGS 列表中追加一项即可
"""
from config import SYS_CONF

PROVIDER_CONFIGS = [
    {
        'code': 'openai',
        'name': 'OpenAI',
        'provider_type': 'openai',
        'base_url': SYS_CONF.get('LLM_URL', 'https://api.openai.com/v1'),
        'api_key': SYS_CONF.get('LLM_API_KEY', ''),
    },
    {
        'code': 'tongyi',
        'name': '通义千问',
        'provider_type': 'tongyi',
        'base_url': SYS_CONF.get('TONGYI_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1'),
        'api_key': SYS_CONF.get('TONGYI_API_KEY', SYS_CONF.get('LLM_API_KEY', '')),
    },
    {
        'code': 'dify',
        'name': 'Dify',
        'provider_type': 'dify',
        'base_url': SYS_CONF.get('DIFY_BASE_URL', SYS_CONF.get('LLM_URL', '')),
        'api_key': SYS_CONF.get('DIFY_API_KEY', SYS_CONF.get('LLM_API_KEY', '')),
    },
    {
        'code': 'gradio',
        'name': 'Gradio',
        'provider_type': 'gradio',
        'base_url': SYS_CONF.get('GRADIO_BASE_URL', SYS_CONF.get('LLM_URL', '')),
        'api_key': '',
    },
    {
        'code': 'anthropic',
        'name': 'Anthropic',
        'provider_type': 'anthropic',
        'base_url': SYS_CONF.get('ANTHROPIC_BASE_URL', ''),
        'api_key': SYS_CONF.get('ANTHROPIC_API_KEY', ''),
    },
]


def get_provider_config(code: str) -> dict | None:
    """根据 code 查找提供商配置，不存在返回 None"""
    for p in PROVIDER_CONFIGS:
        if p['code'] == code:
            return p
    return None
