"""DynamoDB handler:文档/KV(boto3,PartiQL),原生 client + dlt resource(scan)。"""

from typing import Any

from module_data.handlers.base import Capability, Connector, ConnectResult
from module_data.handlers.dynamodb_handler.connection_args import connection_args, connection_args_example


class DynamoDBHandler(Connector):
    name = 'dynamodb'
    title = 'Amazon DynamoDB'
    family = 'document'
    capabilities = Capability.READ | Capability.WRITE | Capability.EXTRACT | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    def __init__(self, connection_data: dict[str, Any]) -> None:
        super().__init__(connection_data)
        self._client = None
        self._deser = None

    def _client_kwargs(self) -> dict:
        kw: dict = {
            'aws_access_key_id': self.arg('aws_access_key_id'),
            'aws_secret_access_key': self.arg('aws_secret_access_key'),
            'region_name': self.arg('region_name', default='us-east-1'),
        }
        if self.arg('aws_session_token'):
            kw['aws_session_token'] = self.arg('aws_session_token')
        return kw

    @property
    def client(self) -> Any:
        if self._client is None:
            import boto3

            self._client = boto3.client('dynamodb', **self._client_kwargs())
        return self._client

    def _deserialize(self, item: dict) -> dict:
        if self._deser is None:
            from boto3.dynamodb.types import TypeDeserializer

            self._deser = TypeDeserializer()
        return {k: self._deser.deserialize(v) for k, v in item.items()}

    def test_connection(self) -> ConnectResult:
        try:
            self.client.list_tables(Limit=1)
            return ConnectResult(True, 'ok')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        return self.client.list_tables().get('TableNames', [])

    def query(self, statement: str, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """PartiQL:SELECT * FROM "table" WHERE ...(参数化用 Parameters)。"""
        kw: dict = {'Statement': statement}
        if params:
            from boto3.dynamodb.types import TypeSerializer

            ser = TypeSerializer()
            kw['Parameters'] = [ser.serialize(v) for v in (params.values() if isinstance(params, dict) else params)]
        resp = self.client.execute_statement(**kw)
        items = [self._deserialize(it) for it in resp.get('Items', [])]
        return items[:limit] if limit else items

    def extract(self, table: str, **kwargs: Any) -> Any:
        """scan 全表(分页)。"""
        import dlt

        handler = self

        @dlt.resource(name=table, write_disposition='append')
        def _items() -> Any:
            paginator = handler.client.get_paginator('scan')
            for page in paginator.paginate(TableName=table):
                for it in page.get('Items', []):
                    yield handler._deserialize(it)

        return _items

    def write(self, data: Any, table: str, mode: str = 'append', **kwargs: Any) -> Any:
        from boto3.dynamodb.types import TypeSerializer

        ser = TypeSerializer()
        n = 0
        for rec in data:
            self.client.put_item(TableName=table, Item={k: ser.serialize(v) for k, v in rec.items()})
            n += 1
        return {'written': n}
