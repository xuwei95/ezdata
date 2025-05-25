"""
kafka消费demo
"""
from etl.libs.kafka_utils import KafkaConsumer

# ######################### 设置 #########################
bootstrap_servers = '124.220.54.30:9092'

if __name__ == '__main__':
    consumer = KafkaConsumer('test', **{
            "bootstrap_servers": bootstrap_servers,
            "group_id": "3242342"
        })
    print(consumer.topics())
    for msg in consumer:
        print(msg)