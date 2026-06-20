"""
Contextual Retrieval(Anthropic 2024)—— embed 前给每个分段加 LLM 生成的上下文背景。

把"片段在全文中的背景"前置到片段文本再做向量化/全文索引,显著提升召回准确率。
同步执行(训练线程内),用 AiConfig 兜底 LLM;无 LLM 或失败时原样返回(优雅降级)。
逐段 1 次 LLM 调用,较慢且有成本,故为知识库级可选(默认关)。
"""

from __future__ import annotations

_PROMPT = (
    '下面是一篇文档,以及其中的一个片段。请用一两句简体中文写出该片段在整篇文档中的上下文背景'
    '(它在讲什么、属于哪部分),便于检索时定位。只输出背景文本本身,不要任何解释或前缀。\n\n'
    '<文档>\n{doc}\n</文档>\n\n<片段>\n{chunk}\n</片段>\n\n背景:'
)


def _llm_cfg() -> dict | None:
    from config.env import AiConfig  # noqa: PLC0415
    if not AiConfig.enabled:
        return None
    return dict(provider=AiConfig.provider, model_code=AiConfig.llm_model, model_name=None,
                api_key=AiConfig.llm_api_key, base_url=AiConfig.llm_url or None, max_tokens=300)


def contextualize(doc_text: str, chunks: list[str], *, max_doc_chars: int = 6000) -> list[str]:
    """给每段加上下文前缀。无 LLM 或异常 → 原样返回对应段。"""
    cfg = _llm_cfg()
    if not cfg or not chunks:
        return chunks
    try:
        from agno.agent import Agent  # noqa: PLC0415
        from utils.ai_util import AiUtil  # noqa: PLC0415
        agent = Agent(model=AiUtil.get_model_from_factory(**cfg))
    except Exception:  # noqa: BLE001
        return chunks

    doc_excerpt = doc_text[:max_doc_chars]
    out: list[str] = []
    for ch in chunks:
        try:
            res = agent.run(_PROMPT.format(doc=doc_excerpt, chunk=ch))
            ctx = (getattr(res, 'content', None) or '').strip()
            out.append(f'{ctx}\n\n{ch}' if ctx else ch)
        except Exception:  # noqa: BLE001
            out.append(ch)
    return out
