"""Neo4j handler:图库 Cypher(官方 neo4j 驱动),原生 client + dlt resource。"""

from typing import Any

from ezdata.handlers.base import Capability, Connector, ConnectResult
from ezdata.handlers.neo4j_handler.connection_args import connection_args, connection_args_example


class Neo4jHandler(Connector):
    name = 'neo4j'
    title = 'Neo4j'
    family = 'graph'
    capabilities = Capability.READ | Capability.WRITE | Capability.EXTRACT | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._driver = None

    @property
    def database(self) -> str:
        return self.arg('database', default='neo4j')

    @property
    def driver(self) -> Any:
        def _make():
            from neo4j import GraphDatabase
            return GraphDatabase.driver(
                self.arg('uri', default='bolt://127.0.0.1:7687'),
                auth=(self.arg('username', 'user', default='neo4j'), self.arg('password', default='')))
        return self._lazy('_driver', _make)

    def test_connection(self) -> ConnectResult:
        try:
            self.driver.verify_connectivity()
            return ConnectResult(True, 'ok')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        """节点标签(当作"表")。"""
        return [r['label'] for r in self.query('CALL db.labels() YIELD label RETURN label')]

    def sample_query(self, table: str, limit: int = 100) -> str:
        return f'MATCH (n:`{table}`) RETURN n LIMIT {limit}'

    def query(self, statement: str, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """Cypher 参数化查询($param,绝不拼接)。"""
        cypher = statement
        if limit is not None and 'limit' not in cypher.lower():
            cypher = f'{cypher.rstrip().rstrip(";")} LIMIT {int(limit)}'
        with self.driver.session(database=self.database) as s:
            return [dict(r) for r in s.run(cypher, params or {})]

    def extract(self, table: str, **kwargs: Any) -> Any:
        """table 作为节点标签,抽取其全部节点属性。"""
        import dlt

        driver, db, label = self.driver, self.database, table

        @dlt.resource(name=table, write_disposition='append')
        def _nodes() -> Any:
            with driver.session(database=db) as s:
                for r in s.run(f'MATCH (n:`{label}`) RETURN n'):
                    yield dict(r['n'])

        return _nodes

    def write(self, data: Any, table: str, mode: str = 'append', **kwargs: Any) -> Any:
        """按标签 table 创建节点。"""
        n = 0
        with self.driver.session(database=self.database) as s:
            for rec in data:
                s.run(f'CREATE (n:`{table}`) SET n = $props', props=rec)
                n += 1
        return {'written': n}
