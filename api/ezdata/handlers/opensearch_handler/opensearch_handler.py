"""OpenSearch handler:ES 兼容,继承 ElasticsearchHandler,客户端换 opensearch-py。"""

from typing import Any

from ezdata.handlers.elasticsearch_handler.elasticsearch_handler import ElasticsearchHandler
from ezdata.handlers.opensearch_handler.connection_args import connection_args, connection_args_example


class OpenSearchHandler(ElasticsearchHandler):
    name = 'opensearch'
    title = 'OpenSearch'
    connection_args = connection_args
    connection_args_example = connection_args_example

    @property
    def client(self) -> Any:
        def _make():
            from opensearchpy import OpenSearch
            hosts = self.arg('hosts', default='https://127.0.0.1:9200')
            if isinstance(hosts, str):
                hosts = [h.strip() for h in hosts.split(',') if h.strip()]
            kw: dict = {'hosts': hosts, 'verify_certs': bool(self.arg('verify_certs', default=False))}
            if self.arg('user'):
                kw['http_auth'] = (self.arg('user'), self.arg('password', default=''))
            return OpenSearch(**kw)
        return self._lazy('_client', _make)
