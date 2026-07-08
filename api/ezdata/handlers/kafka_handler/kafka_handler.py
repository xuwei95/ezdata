"""
Kafka handler:流式消息源(kafka-python)。

借鉴旧版 etl/data_models/kafka_topic.py:Consumer 消费 / Producer 写入。
  - query:有界预览(consumer_timeout_ms 兜底,读最多 N 条);
  - stream:长驻消费,持续 yield(供 worker);
  - extract:把一批消费包成 dlt resource(微批装载);
  - write:Producer 发送。
生产可换 confluent-kafka(librdkafka,更快更稳),API 略不同。
"""

import json
from collections.abc import Iterable, Iterator
from typing import Any

from ezdata.handlers.base import Capability, Connector, ConnectResult
from ezdata.handlers.kafka_handler.connection_args import connection_args, connection_args_example


class KafkaHandler(Connector):
    name = 'kafka'
    title = 'Apache Kafka'
    family = 'stream'
    capabilities = Capability.WRITE | Capability.EXTRACT | Capability.STREAM | Capability.SCHEMA
    connection_args = connection_args
    connection_args_example = connection_args_example

    def _conn_kwargs(self) -> dict:
        servers = self.arg('bootstrap_servers', default='127.0.0.1:9092')
        kw: dict[str, Any] = {'bootstrap_servers': [s.strip() for s in str(servers).split(',') if s.strip()]}
        for k in ('security_protocol', 'sasl_mechanism', 'sasl_plain_username', 'sasl_plain_password'):
            if self.arg(k):
                kw[k] = self.arg(k)
        return kw

    def _consumer(
        self, topic: str, *, timeout_ms: int | None = None, offset: str = 'latest', group: str | None = None
    ) -> Any:
        from kafka import KafkaConsumer

        kw = self._conn_kwargs()
        kw.update(
            auto_offset_reset=offset,
            enable_auto_commit=False,
            value_deserializer=lambda v: v.decode('utf-8', 'replace') if v else None,
        )
        if group or self.arg('group_id'):
            kw['group_id'] = group or self.arg('group_id')
        if timeout_ms is not None:
            kw['consumer_timeout_ms'] = timeout_ms
        return KafkaConsumer(topic, **kw)

    def test_connection(self) -> ConnectResult:
        try:
            from kafka import KafkaConsumer

            c = KafkaConsumer(**self._conn_kwargs())
            ok = bool(c.topics() is not None)
            c.close()
            return ConnectResult(True, 'ok') if ok else ConnectResult(False, '无法获取 topic 列表')
        except Exception as e:
            return ConnectResult(False, str(e))

    def list_tables(self) -> list[str]:
        from kafka import KafkaConsumer

        c = KafkaConsumer(**self._conn_kwargs())
        topics = sorted(c.topics())
        c.close()
        return topics

    def _to_record(self, msg: Any) -> dict:
        val = msg.value
        if isinstance(val, str):
            try:
                val = json.loads(val)
            except (ValueError, TypeError):
                pass
        rec = {'_topic': msg.topic, '_partition': msg.partition, '_offset': msg.offset, '_timestamp': msg.timestamp}
        rec.update(val if isinstance(val, dict) else {'value': val})
        return rec

    def query(self, statement: dict, params: dict | None = None, limit: int | None = None) -> list[dict]:
        """有界预览。statement = {'topic':..., 'offset':'earliest'|'latest'}。"""
        topic = statement['topic'] if isinstance(statement, dict) else statement
        n = limit or (statement.get('max') if isinstance(statement, dict) else None) or 20
        offset = statement.get('offset', 'earliest') if isinstance(statement, dict) else 'earliest'
        c = self._consumer(topic, timeout_ms=3000, offset=offset)
        out = []
        for msg in c:
            out.append(self._to_record(msg))
            if len(out) >= n:
                break
        c.close()
        return out

    def stream(self, *, topic: str, offset: str = 'latest', group: str | None = None, **kwargs: Any) -> Iterator[dict]:
        """长驻消费,持续 yield(阻塞)。"""
        c = self._consumer(topic, offset=offset, group=group)
        try:
            for msg in c:
                yield self._to_record(msg)
        finally:
            c.close()

    def extract(self, table: str, *, max_messages: int = 10_000, timeout_ms: int = 5000, **kwargs: Any) -> Any:
        """把一批消费包成 dlt resource(有界微批,供批装载)。"""
        import dlt

        handler, topic = self, table

        @dlt.resource(name=topic, write_disposition='append')
        def _msgs() -> Any:
            c = handler._consumer(topic, timeout_ms=timeout_ms, offset='earliest')
            n = 0
            try:
                for msg in c:
                    yield handler._to_record(msg)
                    n += 1
                    if n >= max_messages:
                        break
            finally:
                c.close()

        return _msgs

    def write(self, data: Iterable[dict], table: str, mode: str = 'append', **kwargs: Any) -> Any:
        """Producer 发送 JSON 消息到 topic。"""
        from kafka import KafkaProducer

        kw = self._conn_kwargs()
        producer = KafkaProducer(value_serializer=lambda x: json.dumps(x, default=str).encode('utf-8'), **kw)
        n = 0
        for rec in data:
            producer.send(table, rec)
            n += 1
        producer.flush()
        producer.close()
        return {'written': n}
