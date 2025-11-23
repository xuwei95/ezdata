# encoding: utf-8
"""
@Description: kafka 封装类
"""
from kafka import KafkaConsumer, KafkaProducer
from kafka.structs import TopicPartition


class PrintHandler(object):
    """
    打印处理
    """

    def handle(self, data):
        print(data)


class Consumer(object):
    def __init__(self, *topic, **config):
        """
        'bootstrap_servers': 'localhost',
        'client_id': 'kafka-python-' + __version__,
        'group_id': None,
        """
        self._consumer = KafkaConsumer(*topic, **config)

    def run(self, handler):
        for msg in self._consumer:
            try:
                if handler:
                    # print(msg.value)
                    handler.handle(msg.value)
            except Exception as e:
                print(e)


class Producer(object):
    def __init__(self, topic, **config):
        """
        'bootstrap_servers': 'localhost',
        'client_id': None,
        """
        self._producer = KafkaProducer(**config)
        self._topic = topic

    def send(self, data):
        self._producer.send(self._topic, value=bytes(data, encoding='utf-8'), key=None)
        self._producer.flush()

    def close(self):
        self._producer.close()


def get_newest_offset(bootstrap_servers, topic):
    '''
    获取topic最新offset
    '''
    consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
    partitions_set = consumer.partitions_for_topic(topic)
    # 获取最新偏移量
    zz = [TopicPartition(topic, p) for p in partitions_set]
    topic_offset_dict = consumer.end_offsets(zz)
    result = list(topic_offset_dict.values())
    if result != []:
        return max(result)
    else:
        return 0


def get_group_newest_offset(bootstrap_servers, group_id, topic):
    """
    获取一个topic特定group已经消费的offset
    """
    consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers,
                             group_id=group_id,
                             )
    pts = [TopicPartition(topic=topic, partition=i) for i in
           consumer.partitions_for_topic(topic)]
    result = consumer._coordinator.fetch_committed_offsets(pts)
    result = [r.offset for r in result.values()]
    if result != []:
        return max(result)
    else:
        return 0


def fetch_kafka_data_by_page(page=0, pagesize=10, bootstrap_servers=None, topic=None, group_id=None):
    '''
    分页读取kafka数据
    '''
    if bootstrap_servers is None:
        return {
            'code': 400,
            'msg': '链接地址不能为空!'
        }
    elif topic is None:
        return {
            'code': 400,
            'msg': 'topic不能为空!'
        }
    elif group_id is not None:
        consumer = KafkaConsumer(
            group_id=group_id,  # 指定此消费者实例属于的组名，可以不指定
            bootstrap_servers=bootstrap_servers,  # 指定kafka服务器
            auto_offset_reset='earliest'
        )
        total = get_group_newest_offset(bootstrap_servers, group_id, topic)
    else:
        consumer = KafkaConsumer(
            bootstrap_servers=bootstrap_servers,  # 指定kafka服务器
            auto_offset_reset='earliest'
        )
        total = get_newest_offset(bootstrap_servers, topic)
    tp = TopicPartition(topic, 0)
    consumer.assign([tp])
    start_offset = (page-1)*pagesize
    end_offset = start_offset + pagesize
    if end_offset > total:
        return {
            'code': 200,
            'msg': 'ok',
            'records': [],
            'total': total
        }
    data_li = []
    consumer.seek(tp, start_offset)
    n = 0
    for msg in consumer:
        data = msg.value.decode('utf-8').encode('utf-8').decode('unicode_escape')
        data_li.append(data)
        if n >= pagesize:
            return {
                'code': 200,
                'msg': 'ok',
                'records': data_li,
                'total': total
            }
        n += 1


def list_all_topics(bootstrap_servers):
    """
    获取Kafka集群中的所有主题。
    :param bootstrap_servers: Kafka集群的服务器地址，格式为"host1:port1,host2:port2"。
    :return: 主题列表。
    """
    try:
        # 创建一个KafkaConsumer实例，但不订阅任何主题
        consumer = KafkaConsumer(bootstrap_servers=bootstrap_servers)
        # 获取并返回所有主题
        return list(consumer.topics())
    except Exception as e:
        print(f"Error in listing topics: {e}")
        return []