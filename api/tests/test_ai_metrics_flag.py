"""AiUtil 的 metrics 采集口径判据(治「流式每块重复带累计 usage → token 放大」)。

纯判据 _wants_completion_metrics 只看 provider + base_url,不发网络请求;另对 OpenAI 兼容
提供商断言工厂真的把 collect_metrics_on_completion 塞进了模型(构造 agno 模型不联网)。
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.ai_util import AiUtil


@pytest.mark.parametrize(
    ('provider', 'gateway_url', 'expected'),
    [
        # 第三方 DeepSeek / 聚合网关(.env 里那个坑):OpenAI 名下 + 非官方主机 → 开
        ('OpenAI', 'https://ai.1592653.xyz/v1', True),
        ('OpenAI', 'https://api.siliconflow.cn/v1', True),
        # SiliconFlow 专有 provider:恒开(其官方线也逐块带累计 usage)
        ('SiliconFlow', 'https://api.siliconflow.cn/v1', True),
        ('SiliconFlow', None, True),
        # 官方 OpenAI 线:usage 在独立空 choices 末块,须保持默认逐块采集 → 不开
        ('OpenAI', 'https://api.openai.com/v1', False),
        ('OpenAI', None, False),  # 无 base_url = 官方默认
        # Azure OpenAI:同官方线口径 → 不开
        ('OpenAI', 'https://my-res.openai.azure.com', False),
        # 未知 provider 会回退到 OpenAIChat,自建主机同样按累计 usage 处理 → 开
        ('SomeGatewayX', 'https://llm.internal.corp/v1', True),
        # 非 OpenAI 兼容线(Anthropic/Gemini 各有用量通道,且不认此参数)→ 不开
        ('Anthropic', 'https://gateway.example.com/api', False),
        ('Google', None, False),
    ],
)
def test_wants_completion_metrics(provider: str, gateway_url: str | None, expected: bool) -> None:
    assert AiUtil._wants_completion_metrics(provider, gateway_url) is expected


def test_factory_sets_flag_for_custom_openai_gateway() -> None:
    """自建 OpenAI 网关:工厂应把 collect_metrics_on_completion 置 True(永久修 .env token 放大坑)。"""
    model = AiUtil.get_model_from_factory(
        provider='OpenAI',
        model_code='deepseek-v4-pro',
        api_key='sk-test',
        base_url='https://ai.1592653.xyz/v1',
    )
    assert getattr(model, 'collect_metrics_on_completion', None) is True


def test_factory_keeps_default_for_official_openai() -> None:
    """官方 OpenAI 线:不得开启(否则漏采空 choices 末块的 usage,记 0)。"""
    model = AiUtil.get_model_from_factory(
        provider='OpenAI',
        model_code='gpt-4o-mini',
        api_key='sk-test',
        base_url=None,
    )
    assert getattr(model, 'collect_metrics_on_completion', False) is False
