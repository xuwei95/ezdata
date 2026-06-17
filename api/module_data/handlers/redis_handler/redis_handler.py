"""Redis handler:KV/哈希/列表(redis-py),原生 client + dlt resource(scan)。"""

from typing import Any

from module_data.handlers.base import Capability, Connector, ConnectResult
from module_data.handlers.redis_handler.connection_args import connection_args, connection_args_example


class RedisHandler(Connector):
    name = 'redis'
    title = 'Redis'
    family = 'kv'
    capabilities = Capability.READ | Capability.WRITE | Capability.EXTRACT | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._client = None

    @property
    def client(self) -> Any:
        if self._client is None:
            import redis

            self._client = redis.Redis(
                host=self.arg('host', default='127.0.0.1'), port=int(self.arg('port', default=6379)),
                password=self.arg('password') or None, db=int(self.arg('db', default=0)), decode_responses=True)
        return self._client

    def test_connection(self) -> ConnectResult:
        try:
            return ConnectResult(True, 'ok') if self.client.ping() else ConnectResult(False, 'ping 失败')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self, pattern: str = '*', count: int = 200) -> list[str]:
        """扫描 key(当作"表")。"""
        keys = []
        for k in self.client.scan_iter(match=pattern, count=count):
            keys.append(k)
            if len(keys) >= count:
                break
        return keys

    def _read_key(self, key: str) -> dict:
        t = self.client.type(key)
        if t == 'string':
            val: Any = self.client.get(key)
        elif t == 'hash':
            val = self.client.hgetall(key)
        elif t == 'list':
            val = self.client.lrange(key, 0, -1)
        elif t == 'set':
            val = list(self.client.smembers(key))
        elif t == 'zset':
            val = self.client.zrange(key, 0, -1, withscores=True)
        else:
            val = None
        return {'key': key, 'type': t, 'value': val}

    def query(self, statement: str | dict, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """statement = key 名 或 {'pattern': '...'}(批量读匹配的 key)。"""
        if isinstance(statement, dict):
            pat = statement.get('pattern', '*')
            return [self._read_key(k) for k in self.list_tables(pat, limit or 100)]
        return [self._read_key(statement)]

    def extract(self, table: str = '*', *, count: int = 1000, **kwargs: Any) -> Any:
        """table 作为 key 匹配模式,scan 出所有 key 的值。"""
        import dlt

        handler = self

        @dlt.resource(name='redis', write_disposition='append')
        def _kv() -> Any:
            for k in handler.client.scan_iter(match=table, count=count):
                yield handler._read_key(k)

        return _kv

    def write(self, data: Any, table: str = '', mode: str = 'append', **kwargs: Any) -> Any:
        """data 为 {key: value} 或可迭代 (key,value);table 作为 key 前缀(可选)。"""
        n = 0
        items = data.items() if isinstance(data, dict) else data
        for k, v in items:
            self.client.set(f'{table}{k}' if table else k, v)
            n += 1
        return {'written': n}
