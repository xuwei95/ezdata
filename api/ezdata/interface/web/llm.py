"""LLM 客户端:基于 agno,暂支持 openai(含一切 OpenAI 兼容端点)与 anthropic 两族。

配置来自 config.llm_config()(读 env LLM_*)。只做 AI 取数需要的最小能力:
把提示词发给模型,拿回文本(complete)或流式增量(stream)。用于 NL→查询语句。

依赖:agno + 对应 provider SDK(openai / anthropic)——这是 ezdata.interface.web 唯一的重依赖。
★agno 一律**惰性导入**(在真正建模型时才 import):
  - `import ezdata.interface.web` / 启动 web 不需要 agno;
  - 未装 agno 时,仅在真正发起 AI 取数(complete/stream)时抛可读错误。

provider 归一:名字含 anthropic/claude → Claude;其余(openai/siliconflow/deepseek/…)→ OpenAIChat。
"""

from collections.abc import Iterator

from . import config

# provider(小写)判定为 anthropic 族;其余一律走 OpenAI 兼容
_ANTHROPIC_ALIASES = {'anthropic', 'claude'}

# AI 取数的输出很短(一条查询/一段 {func,params});把输出上限压到这个量级,
# 既省 token,又规避 Anthropic 在超大 max_tokens 下对非流式请求要求「必须 streaming」的限制。
_MAX_OUTPUT_TOKENS = 8192


class LLMError(RuntimeError):
    pass


def _is_anthropic(provider: str) -> bool:
    return (provider or '').strip().lower() in _ANTHROPIC_ALIASES


def _build_model(cfg: dict, temperature: float | None):
    """按 cfg 造 agno 模型对象(仅 openai / anthropic 两族)。agno 在此惰性导入。"""
    provider = (cfg.get('type') or 'openai').strip()
    base_url = cfg.get('base_url') or None
    # 输出上限:取配置与 _MAX_OUTPUT_TOKENS 的较小值(配置缺省时用默认上限)
    max_tokens = min(int(cfg.get('max_tokens') or _MAX_OUTPUT_TOKENS), _MAX_OUTPUT_TOKENS)

    params: dict = {'id': cfg.get('model'), 'api_key': cfg.get('api_key'), 'max_tokens': max_tokens}
    params = {k: v for k, v in params.items() if v}
    if temperature is not None:
        params['temperature'] = temperature

    try:
        if _is_anthropic(provider):
            from agno.models.anthropic import Claude

            # Claude 不接受顶层 base_url;自定义网关须走 client_params(对齐主项目 AiUtil 的处理)
            if base_url:
                params['client_params'] = {'base_url': base_url}
            return Claude(**params)

        from agno.models.openai import OpenAIChat

        if base_url:
            params['base_url'] = base_url
        return OpenAIChat(**params)
    except ImportError as e:
        raise LLMError(
            '未安装 agno 或对应 provider SDK:请 `pip install agno openai anthropic`(或 pip install ezdata[ai])'
        ) from e


class LLMClient:
    """AI 取数用的最小 LLM 客户端(agno 封装)。"""

    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or config.llm_config()

    @property
    def ready(self) -> bool:
        # anthropic 可不填 base_url(用官方端点),故就绪只看 api_key + model
        return bool(self.cfg.get('api_key') and self.cfg.get('model'))

    def _agent(self, temperature: float | None):
        from agno.agent import Agent

        return Agent(model=_build_model(self.cfg, temperature))

    def complete(self, prompt: str, *, system: str | None = None, temperature: float = 0.0) -> str:
        """一次性补全,返回文本。"""
        if not self.ready:
            raise LLMError('LLM 未配置:请检查 .env 的 LLM_API_KEY / LLM_MODEL')
        text = f'{system}\n\n{prompt}' if system else prompt
        try:
            out = self._agent(temperature).run(text)
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f'LLM 调用失败: {e}') from e
        return (getattr(out, 'content', None) or str(out) or '').strip()

    def stream(self, prompt: str, *, system: str | None = None, temperature: float = 0.0) -> Iterator[str]:
        """流式补全:逐段 yield 文本增量(对齐主项目 _ai_stream:取事件 .content,无增量则回退整段)。"""
        if not self.ready:
            raise LLMError('LLM 未配置:请检查 .env 的 LLM_API_KEY / LLM_MODEL')
        text = f'{system}\n\n{prompt}' if system else prompt
        try:
            produced = False
            for ev in self._agent(temperature).run(text, stream=True):
                chunk = getattr(ev, 'content', None)
                if chunk:
                    produced = True
                    yield chunk
            if not produced:  # 个别模型/版本不产 content 增量事件,回退整段
                out = self._agent(temperature).run(text)
                yield getattr(out, 'content', None) or str(out)
        except LLMError:
            raise
        except Exception as e:
            raise LLMError(f'LLM 流式调用失败: {e}') from e


def strip_code_fence(text: str) -> str:
    """去掉模型可能带出的 ```sql ... ``` / ``` ... ``` 包裹。"""
    t = text.strip()
    if t.startswith('```'):
        lines = t.splitlines()
        # 去首行 ``` 或 ```sql
        lines = lines[1:]
        # 去尾行 ```
        if lines and lines[-1].strip().startswith('```'):
            lines = lines[:-1]
        t = '\n'.join(lines).strip()
    return t
