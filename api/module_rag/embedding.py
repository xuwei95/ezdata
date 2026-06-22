"""
Embedding 客户端 —— provider 可插拔(DashScope / OpenAI 兼容端点),纯 HTTP,无 SDK 依赖。

来源优先级(由 service 决定后传入):知识库绑定的 ai_models 模型 > env 兜底(RagConfig)。
DashScope 用 OpenAI 兼容端点 /compatible-mode/v1/embeddings,与 OpenAI 同形,便于统一。
带 rag_embedding 缓存的逻辑在 service 层(按 hash+model 命中),这里只管"算"。
"""

from __future__ import annotations

import requests

# provider → 默认 base_url(用户未配 base_url 时);其它 OpenAI 兼容端点设 EMBEDDING_URL 即可
_DEFAULT_BASE = {
    'dashscope': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'tongyi': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'openai': 'https://api.openai.com/v1',
    'siliconflow': 'https://api.siliconflow.cn/v1',
    'deepseek': 'https://api.deepseek.com/v1',
}

# 已知模型维度(便于建库时确定 dims;未知则用首条文本实测)
_KNOWN_DIMS = {
    'text-embedding-v1': 1536,
    'text-embedding-v2': 1536,
    'text-embedding-v3': 1024,
    'text-embedding-ada-002': 1536,
    'text-embedding-3-small': 1536,
    'text-embedding-3-large': 3072,
    'BAAI/bge-m3': 1024,
    'BAAI/bge-large-zh-v1.5': 1024,
    'BAAI/bge-large-en-v1.5': 1024,
    'Qwen/Qwen3-Embedding-0.6B': 1024,
}


class EmbeddingClient:
    def __init__(self, provider: str, model: str, api_key: str, base_url: str | None = None,
                 *, dims: int | None = None, batch_size: int = 16, timeout: int = 60) -> None:
        self.provider = (provider or 'dashscope').strip().lower()
        self.model = model
        self.api_key = api_key
        base = (base_url or '').strip() or _DEFAULT_BASE.get(self.provider, _DEFAULT_BASE['openai'])
        self.base = base.rstrip('/')
        self._dims = dims or _KNOWN_DIMS.get(model)
        self.batch_size = batch_size
        self.timeout = timeout

    @property
    def dims(self) -> int:
        """返回维度;未知则实测一条。"""
        if self._dims is None:
            self._dims = len(self.embed(['_dim_probe_'])[0])
        return self._dims

    def embed(self, texts: list[str]) -> list[list[float]]:
        """批量向量化,保持入参顺序。"""
        if not texts:
            return []
        out: list[list[float]] = []
        for i in range(0, len(texts), self.batch_size):
            out.extend(self._embed_batch(texts[i:i + self.batch_size]))
        return out

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def _embed_batch(self, batch: list[str]) -> list[list[float]]:
        url = f'{self.base}/embeddings'
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}
        payload: dict = {'model': self.model, 'input': batch}
        if self.provider == 'openai' and self._dims and self.model.startswith('text-embedding-3'):
            payload['dimensions'] = self._dims  # openai v3 可指定维度
        resp = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        if resp.status_code >= 400:
            raise RuntimeError(f'embedding 调用失败 {resp.status_code}: {resp.text[:300]}')
        data = resp.json().get('data') or []
        # 按 index 排序确保对齐
        data = sorted(data, key=lambda d: d.get('index', 0))
        return [d['embedding'] for d in data]
