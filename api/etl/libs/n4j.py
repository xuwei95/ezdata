# encoding: utf-8
"""
neo4j 操作封装类
"""
from py2neo import Graph, Node, Relationship
import time


class NjClient(object):
    def __init__(self, p_url, **kwargs):
        """
        NjClient('http://localhost:7474', **{'username':'', 'password':''})
        新版本认证使用auth=(kwargs['username'], kwargs['password'])
        """
        try:
            self._client = Graph(p_url, **kwargs)
        except Exception as e:
            print(e)
            self._client = Graph(p_url, auth=(kwargs['username'], kwargs['password']))

    def delete_all(self):
        self._client.delete_all()

    def query(self, p_query):
        return self._client.run(p_query).data()

    def find(self, p_labels, p_properties):
        return self._client.nodes.match(*p_labels, **p_properties)

    def find_one(self, p_labels, p_properties):
        """
        查询节点
        """
        return self.find(p_labels, p_properties).first()

    def create_node(self, p_labels, p_properties):
        """
        创建一个新节点
        """
        self._client.create(Node(*p_labels, **p_properties))
        return self.find_one(p_labels, p_properties)

    def create_node_with_check(self, p_labels, p_check_properties, p_properties):
        """
        查询并创建节点
        p_labels label列表
        p_check_properties 确定节点唯一性属性
        p_properties 创建或者更新的属性列表
        """
        node = self.find_one(p_labels, p_check_properties)
        if node is None:
            return self.create_node(p_labels, p_properties)

        return node

    def update_node(self, p_labels, p_key_properties, p_data_properties):
        """
        更新节点
        p_labels label列表
        p_key_properties 确定节点唯一性属性
        p_properties 创建或者更新的属性列表
        """
        node = self.find_one(p_labels, p_key_properties)
        if node is None:
            return None

        for key, value in p_data_properties.items():
            node[key] = value
        node['update_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
        self._client.push(node)
        return node

    def update_or_create_node(self, p_labels, p_properties):
        """
        更新或者新建节点
        p_labels label列表
        p_properties 确定节点唯一性属性也是更新的属性
        """
        node = self.update_node(p_labels, p_properties, p_properties)
        if node:
            return node

        node = self.create_node(p_labels, p_properties)
        return node

    def update_or_create_node_with_key(self, p_labels, p_key_properties, p_properties):
        """
        更新或者新建节点
        p_labels label列表
        p_key_properties 确定节点唯一性属性
        p_properties 创建或者更新的属性列表
        """
        node = self.update_node(p_labels, p_key_properties, p_properties)
        if node:
            return node

        node = self.create_node(p_labels, p_properties)
        return node

    def update_with_key(self, p_labels, p_key_properties, p_properties):
        """
        更新节点属性
        """
        nodes = self.find(p_labels, p_key_properties)
        for node in nodes.all():
            for key, value in p_properties.items():
                node[key] = value
            self._client.push(node)

    def update_by_identity(self, identity, p_properties):
        """
        根据节点ID更新属性
        """
        node = self._client.nodes.get(identity)
        if node:
            for key, value in p_properties.items():
                node[key] = value
            self._client.push(node)

    def update_by_identity_with_ext(self, identity, p_properties):
        """
        根据节点ID更新属性，同时更新部分附加固有属性
        """
        node = self._client.nodes.get(identity)
        if node:
            for key, value in p_properties.items():
                node[key] = value
            node['gmt_modified'] = int(time.time())
            node['gmt_modified_datetime'] = time.strftime('%Y-%m-%d %H:%M:%S')
            self._client.push(node)

    def find_by_identity(self, identity):
        """
        根据节点ID获取节点
        """
        return self._client.nodes.get(identity)

    def create_relation(self, start_node, label, end_node, relation_info):
        """
        创建节点关系
        """
        relation = Relationship(start_node, label, end_node, **relation_info)
        return self._client.create(relation)


