"""
ES8 向量后端 —— 原生 dense_vector + kNN + BM25(同一索引混合检索)。

为什么走 REST 而非 es-py 客户端:
  日志 ES 仍是 7.17,而 es-py 8 客户端连 7.17 服务端会因 product-check 直接拒连。
  在全栈迁到 ES8 之前,这里用 requests 直打 REST,既能用 ES8 原生 kNN,又不影响现有 es-py 7.17。
  连接参数(hosts/api_key/user/password)与 elasticsearch_handler.connection_args 同形,后续可平滑接到 data_source。
"""

from __future__ import annotations

import json
from typing import Any

import requests

from module_rag.vector_store.base import VectorStore


class EsVectorStore(VectorStore):
    name = 'elasticsearch'

    def __init__(self, connection_data: dict[str, Any], index: str, *, timeout: int = 30) -> None:
        super().__init__(connection_data, index)
        self.timeout = timeout
        hosts = self.connection_data.get('hosts') or 'http://127.0.0.1:9200'
        if isinstance(hosts, str):
            hosts = [h.strip() for h in hosts.split(',') if h.strip()]
        base = hosts[0]
        if not base.startswith(('http://', 'https://')):
            base = 'http://' + base
        self.base = base.rstrip('/')

        self._auth = None
        self._headers = {'Content-Type': 'application/json'}
        if self.connection_data.get('api_key'):
            self._headers['Authorization'] = f'ApiKey {self.connection_data["api_key"]}'
        elif self.connection_data.get('user'):
            self._auth = (self.connection_data['user'], self.connection_data.get('password', ''))

    # ---------------- 底层请求 ----------------
    def _req(self, method: str, path: str, body: dict | str | None = None) -> dict:
        url = f'{self.base}/{path.lstrip("/")}'
        data = body if isinstance(body, str) else (json.dumps(body) if body is not None else None)
        resp = requests.request(method, url, data=data, headers=self._headers, auth=self._auth, timeout=self.timeout)
        if resp.status_code >= 400:
            raise RuntimeError(f'ES {method} {path} -> {resp.status_code}: {resp.text[:500]}')
        return resp.json() if resp.text else {}

    def ping(self) -> bool:
        try:
            requests.get(self.base, headers=self._headers, auth=self._auth, timeout=5).raise_for_status()
            return True
        except Exception:
            return False

    # ---------------- 索引管理 ----------------
    def index_exists(self) -> bool:
        resp = requests.head(f'{self.base}/{self.index}', headers=self._headers, auth=self._auth, timeout=self.timeout)
        return resp.status_code == 200

    def ensure_index(self, dims: int, *, similarity: str = 'cosine', analyzer: str | None = None) -> bool:
        if self.index_exists():
            return False
        content_field: dict[str, Any] = {'type': 'text'}
        if analyzer:
            content_field['analyzer'] = analyzer
        mapping = {
            'mappings': {
                'properties': {
                    'content': content_field,
                    'content_vector': {
                        'type': 'dense_vector', 'dims': dims,
                        'index': True, 'similarity': similarity,
                        'index_options': {'type': 'hnsw', 'm': 16, 'ef_construction': 100},
                    },
                    'tenant_id': {'type': 'keyword'},
                    'dataset_id': {'type': 'keyword'},
                    'document_id': {'type': 'keyword'},
                    'chunk_id': {'type': 'keyword'},
                    'chunk_type': {'type': 'keyword'},
                    'question': {'type': 'text'},
                    'meta': {'type': 'object', 'enabled': False},
                },
            },
        }
        self._req('PUT', self.index, mapping)
        return True

    def drop(self) -> None:
        if self.index_exists():
            self._req('DELETE', self.index)

    def count(self, *, filters: list[dict] | None = None) -> int:
        body = {'query': {'bool': {'filter': filters}} if filters else {'match_all': {}}}
        return int(self._req('POST', f'{self.index}/_count', body).get('count', 0))

    def refresh(self) -> None:
        self._req('POST', f'{self.index}/_refresh')

    # ---------------- 写 / 删 ----------------
    def add(self, chunks: list[dict], *, refresh: bool = True) -> dict:
        if not chunks:
            return {'indexed': 0}
        lines = []
        for c in chunks:
            lines.append(json.dumps({'index': {'_index': self.index, '_id': c['chunk_id']}}))
            lines.append(json.dumps(c))
        ndjson = '\n'.join(lines) + '\n'
        resp = requests.post(f'{self.base}/_bulk', data=ndjson.encode('utf-8'),
                             headers={'Content-Type': 'application/x-ndjson',
                                      **({'Authorization': self._headers['Authorization']}
                                         if 'Authorization' in self._headers else {})},
                             auth=self._auth, timeout=self.timeout)
        resp.raise_for_status()
        result = resp.json()
        if result.get('errors'):
            first = next((it for it in result['items'] if list(it.values())[0].get('error')), None)
            raise RuntimeError(f'bulk 部分失败: {json.dumps(first)[:500]}')
        if refresh:
            self.refresh()
        return {'indexed': len(chunks)}

    def delete_by_document(self, document_id: str, *, tenant_id: str | None = None) -> int:
        filters = [{'term': {'document_id': document_id}}]
        if tenant_id is not None:
            filters.append({'term': {'tenant_id': tenant_id}})
        body = {'query': {'bool': {'filter': filters}}}
        return int(self._req('POST', f'{self.index}/_delete_by_query?refresh=true', body).get('deleted', 0))

    def delete_by_ids(self, ids: list[str]) -> int:
        if not ids:
            return 0
        body = {'query': {'ids': {'values': ids}}}
        return int(self._req('POST', f'{self.index}/_delete_by_query?refresh=true', body).get('deleted', 0))

    # ---------------- 检索 ----------------
    def vector_search(self, query_vector: list[float], k: int = 5, *,
                      num_candidates: int = 100, filters: list[dict] | None = None) -> list[dict]:
        knn: dict[str, Any] = {'field': 'content_vector', 'query_vector': query_vector,
                               'k': k, 'num_candidates': max(num_candidates, k)}
        if filters:
            knn['filter'] = {'bool': {'filter': filters}}
        body = {'knn': knn, 'size': k, '_source': {'excludes': ['content_vector']}}
        return self._hits(self._req('POST', f'{self.index}/_search', body))

    def keyword_search(self, query_text: str, k: int = 5, *, filters: list[dict] | None = None) -> list[dict]:
        bool_q: dict[str, Any] = {'must': {'match': {'content': query_text}}}
        if filters:
            bool_q['filter'] = filters
        body = {'query': {'bool': bool_q}, 'size': k, '_source': {'excludes': ['content_vector']}}
        return self._hits(self._req('POST', f'{self.index}/_search', body))

    @staticmethod
    def _hits(resp: dict) -> list[dict]:
        out = []
        for h in resp.get('hits', {}).get('hits', []):
            src = h.get('_source', {})
            out.append({**src, 'chunk_id': src.get('chunk_id', h.get('_id')), 'score': h.get('_score')})
        return out
