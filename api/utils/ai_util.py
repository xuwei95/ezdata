from importlib import import_module
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from config.database import async_engine
from config.env import DataBaseConfig

if TYPE_CHECKING:
    from agno.db.base import AsyncBaseDb
    from agno.models.base import Model

# 提供商名称 -> (模块路径, 类名) 的映射，延迟导入避免启动时加载所有AI SDK
_PROVIDER_REGISTRY: dict[str, tuple[str, str]] = {
    'AIMLAPI': ('agno.models.aimlapi', 'AIMLAPI'),
    'Anthropic': ('agno.models.anthropic', 'Claude'),
    'Cerebras': ('agno.models.cerebras', 'Cerebras'),
    'CerebrasOpenAI': ('agno.models.cerebras', 'CerebrasOpenAI'),
    'Cohere': ('agno.models.cohere', 'Cohere'),
    'CometAPI': ('agno.models.cometapi', 'CometAPI'),
    'DashScope': ('agno.models.dashscope', 'DashScope'),
    'DeepInfra': ('agno.models.deepinfra', 'DeepInfra'),
    'DeepSeek': ('agno.models.deepseek', 'DeepSeek'),
    'Fireworks': ('agno.models.fireworks', 'Fireworks'),
    'Google': ('agno.models.google', 'Gemini'),
    'Groq': ('agno.models.groq', 'Groq'),
    'HuggingFace': ('agno.models.huggingface', 'HuggingFace'),
    'LangDB': ('agno.models.langdb', 'LangDB'),
    'LiteLLM': ('agno.models.litellm', 'LiteLLM'),
    'LiteLLMOpenAI': ('agno.models.litellm', 'LiteLLMOpenAI'),
    'LlamaCpp': ('agno.models.llama_cpp', 'LlamaCpp'),
    'LMStudio': ('agno.models.lmstudio', 'LMStudio'),
    'Meta': ('agno.models.meta', 'Llama'),
    'Mistral': ('agno.models.mistral', 'MistralChat'),
    'N1N': ('agno.models.n1n', 'N1N'),
    'Nebius': ('agno.models.nebius', 'Nebius'),
    'Nexus': ('agno.models.nexus', 'Nexus'),
    'Nvidia': ('agno.models.nvidia', 'Nvidia'),
    'Ollama': ('agno.models.ollama', 'Ollama'),
    'OpenAI': ('agno.models.openai', 'OpenAIChat'),
    'OpenAIResponses': ('agno.models.openai.responses', 'OpenAIResponses'),
    'OpenRouter': ('agno.models.openrouter', 'OpenRouter'),
    'Perplexity': ('agno.models.perplexity', 'Perplexity'),
    'Portkey': ('agno.models.portkey', 'Portkey'),
    'Requesty': ('agno.models.requesty', 'Requesty'),
    'Sambanova': ('agno.models.sambanova', 'Sambanova'),
    'SiliconFlow': ('agno.models.siliconflow', 'Siliconflow'),
    'Together': ('agno.models.together', 'Together'),
    'Vercel': ('agno.models.vercel', 'V0'),
    'VLLM': ('agno.models.vllm', 'VLLM'),
    'xAI': ('agno.models.xai', 'xAI'),
}

# OpenAI 兼容(经 agno OpenAIChat 走线)的提供商:这类才认 collect_metrics_on_completion 参数,
# 且才可能遇到「流式每块重复带累计 usage」的放大坑。Anthropic/Gemini 等各有自己的用量通道,不在此列。
_OPENAI_COMPAT_PROVIDERS: frozenset[str] = frozenset({'OpenAI', 'OpenAIResponses'})
# 「官方 OpenAI 线」主机:usage 单独放在 choices 为空的独立末块里,须保持 agno 默认逐块采集,
# 不能开 collect_metrics_on_completion(开了会命中 `if not response.choices: return False` 而漏采,记 0)。
# api.openai.com 以及 Azure OpenAI(*.openai.azure.com)属此类;其余自建/聚合网关一律按「累计 usage」处理。
_OPENAI_WIRE_HOST = 'api.openai.com'
_AZURE_OPENAI_SUFFIX = '.openai.azure.com'

# 存储引擎名称 -> (模块路径, 类名) 的映射
_STORAGE_ENGINE_REGISTRY: dict[str, tuple[str, str]] = {
    'mysql': ('agno.db.mysql', 'AsyncMySQLDb'),
    'postgresql': ('agno.db.postgres', 'AsyncPostgresDb'),
}

# 已加载的提供商类缓存，避免重复import_module
_provider_class_cache: dict[str, 'type[Model]'] = {}
_storage_class_cache: dict[str, 'type[AsyncBaseDb]'] = {}


class AiUtil:
    """
    AI工具类
    """

    @classmethod
    def _resolve_provider_class(cls, provider: str) -> 'type[Model] | None':
        """
        按需加载并缓存提供商模型类

        :param provider: 提供商名称
        :return: 模型类，未找到返回None
        """
        if provider in _provider_class_cache:
            return _provider_class_cache[provider]
        entry = _PROVIDER_REGISTRY.get(provider)
        if entry is None:
            return None
        module_path, class_name = entry
        provider_cls = getattr(import_module(module_path), class_name)
        _provider_class_cache[provider] = provider_cls
        return provider_cls

    @classmethod
    def _resolve_storage_class(cls, db_type: str) -> 'type[AsyncBaseDb]':
        """
        按需加载并缓存存储引擎类

        :param db_type: 数据库类型
        :return: 存储引擎类
        """
        if db_type in _storage_class_cache:
            return _storage_class_cache[db_type]
        entry = _STORAGE_ENGINE_REGISTRY.get(db_type)
        if entry is None:
            # 默认使用MySQL
            entry = _STORAGE_ENGINE_REGISTRY['mysql']
        module_path, class_name = entry
        storage_cls = getattr(import_module(module_path), class_name)
        _storage_class_cache[db_type] = storage_cls
        return storage_cls

    @classmethod
    def get_storage_engine(cls) -> 'AsyncBaseDb':
        """
        获取存储引擎实例

        :return: 存储引擎实例
        """
        storage_engine_class = cls._resolve_storage_class(DataBaseConfig.db_type)

        return storage_engine_class(
            db_engine=async_engine,
            db_schema=DataBaseConfig.db_database if DataBaseConfig.db_type == 'mysql' else 'public',
            session_table='ai_sessions',
            memory_table='ai_memories',
            metrics_table='ai_metrics',
            eval_table='ai_eval_runs',
            knowledge_table='ai_knowledge',
            culture_table='ai_culture',
            traces_table='ai_traces',
            spans_table='ai_spans',
            versions_table='ai_schema_versions',
            create_schema=False,
        )

    @classmethod
    def _wants_completion_metrics(cls, provider: str, base_url: str | None) -> bool:
        """是否应开启 collect_metrics_on_completion(仅收尾块采一次 usage)。

        背景(见 agno models/openai/chat.py 的 _should_collect_metrics):agno 默认(False)对
        每个带 usage 的流式块都采集并累加。SiliconFlow / DeepSeek / 自建 one-api 等聚合网关流式时
        每块都重复带「累计 usage」,于是 token 被放大成「真实值 × 流式块数」(一句话记成几十万/几亿)。
        置 True 改为只在 finish_reason 收尾块采一次,结果正确。

        唯一不能开的是「官方 OpenAI 线」(api.openai.com / *.openai.azure.com):其 usage 单独放在
        choices 为空的独立末块里,开了反而漏采记 0。故判据是「OpenAI 兼容 且 base_url 指向非官方主机」。
        判据只认 provider 名 + base_url,不发网络请求,兜底模型(无 DB 行)与库内模型同样适用——
        这也是把 .env 里 LLM_TYPE=openai + 第三方 DeepSeek 网关 那个放大坑永久修掉的地方。
        """
        if provider == 'SiliconFlow':
            return True
        # OpenAI 兼容 provider,或未知 provider(下方会回退到 OpenAIChat)——两者都走 OpenAI 兼容线
        is_openai_compat = provider in _OPENAI_COMPAT_PROVIDERS or provider not in _PROVIDER_REGISTRY
        if is_openai_compat and base_url:
            host = (urlparse(base_url).hostname or '').lower()
            if host and host != _OPENAI_WIRE_HOST and not host.endswith(_AZURE_OPENAI_SUFFIX):
                return True
        return False

    @classmethod
    def get_model_from_factory(
        cls,
        provider: str,
        model_code: str,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ) -> 'Model':
        """
        从工厂获取模型实例

        :param provider: 提供商
        :param model_code: 模型编码
        :param model_name: 模型名称
        :param api_key: API密钥
        :param base_url: 基础URL
        :param temperature: 温度
        :param max_tokens: 最大令牌数
        :return: 模型实例
        """
        params = {
            'id': model_code,
            'name': model_name,
            'base_url': base_url,
            'api_key': api_key,
            'temperature': temperature,
            'max_tokens': max_tokens,
            **kwargs,
        }
        params = {k: v for k, v in params.items() if v is not None}
        if provider == 'Ollama':
            params['host'] = base_url
        if provider == 'DashScope' and not base_url:
            params['base_url'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        if provider == 'Anthropic' and base_url:
            # Anthropic 的 Claude 不接受 base_url 顶层参数，自定义网关需通过 client_params 传入
            params.pop('base_url', None)
            client_params = dict(params.get('client_params') or {})
            client_params.setdefault('base_url', base_url)
            params['client_params'] = client_params
        if cls._wants_completion_metrics(provider, base_url):
            # 非官方 OpenAI 线(SiliconFlow / DeepSeek / 自建聚合网关)的两处网关兼容修复:
            # ① 流式 usage 放大坑:每块重复带累计 usage,agno 默认逐块累加会放大成「真实值 × 流式块数」。
            #    仅在收尾块采一次,结果正确。详见 _wants_completion_metrics。
            params.setdefault('collect_metrics_on_completion', True)
            # ② system→developer 角色坑:agno 2.8 的 OpenAIChat.default_role_map 把 system 映射成
            #    developer(OpenAI o1/o3 约定),而这类聚合/自建网关只认 system/assistant/user/tool,
            #    收到 developer 直接 400(invalid value: developer)→ 对话半截而止。强制标准 system 角色。
            #    官方 OpenAI 线(api.openai.com / *.openai.azure.com,由 _wants_completion_metrics 排除)
            #    的 o 系列反而需要 developer,故此覆盖仅作用于非官方主机。
            params.setdefault(
                'role_map', {'system': 'system', 'user': 'user', 'assistant': 'assistant', 'tool': 'tool'}
            )
        model_class = cls._resolve_provider_class(provider)
        if model_class is None:
            # 未知提供商，回退到OpenAI
            model_class = cls._resolve_provider_class('OpenAI')

        return model_class(**params)
