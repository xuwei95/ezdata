"""
往 Kafka 里批量产生数据
"""
import random
from json import dumps
from kafka import KafkaProducer
import time
import pandas as pd

# ######################### 设置 #########################
topic = "test"  # kafka topic
bootstrap_servers = '124.220.54.30:9092'


def write_data():
    # 初始化生产者
    producer = KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda x: dumps(x).encode('utf-8'),
        api_version=(0, 10)
    )
    send_num = 10
    time_limit = 10
    base_time = int(time.time())
    for k in range(100):
        if k < send_num:
            t = base_time + (k - send_num) * 60 * time_limit
            dic = {
                "aaa": 111
            }
            print(t, dic)
            producer.send(topic, value=dic)
        else:
            break


if __name__ == '__main__':
    s_time = time.time()
    write_data()
    e_time = time.time()
    print(s_time, e_time, e_time - s_time)
