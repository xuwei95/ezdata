# encoding: utf-8
"""
elastic search 操作封装类
"""
from elasticsearch import Elasticsearch
from elasticsearch import helpers


class EsClient(object):
    def __init__(self, hosts=None, **kwargs):
        """
                :arg hosts: list of nodes, or a single node, we should connect to.
                    Node should be a dictionary ({"host": "localhost", "port": 9200}),
                    the entire dictionary will be passed to the :class:`~elasticsearch.Connection`
                    class as kwargs, or a string in the format of ``host[:port]`` which will be
                    translated to a dictionary automatically.  If no value is given the
                    :class:`~elasticsearch.Connection` class defaults will be used.
                :arg params: any additional arguments will be passed on to the
                    :class:`~elasticsearch.Transport` class and, subsequently, to the
                    :class:`~elasticsearch.Connection` instances.

                exsample：Elasticsearch(hosts=[{'host':'localhost','port':9200}])
                exsample：Elasticsearch(hosts=['node1','node2'])
                """
        self._client = Elasticsearch(hosts=hosts, **kwargs)

    def base_query(self, **kwargs):
        """
        elastic search 原始查询类，主要入参 index，body，size，headers
        """
        return self._client.search(**kwargs)

    def query(self, p_index, p_query, p_size=1, headers=None):
        """
        常用查询函数
        """
        return self.base_query(index=p_index, body=p_query, size=p_size, headers=headers)

    def query_count(self, p_index, p_query, headers=None):
        """
        常用计数函数
        """
        l_result = self.base_query(index=p_index, body=p_query, headers=headers)
        return l_result['hits'].get('total')

    def query_data(self, p_index, p_query, headers=None):
        """
        常用计数函数
        """
        l_result = self.base_query(index=p_index, body=p_query, headers=headers)
        return l_result['hits'].get('hits')

    def query_agg_data(self, p_index, p_query, p_agg_name='res', headers=None):
        """
        常用聚合函数
        """
        l_result = self.base_query(index=p_index, body=p_query, headers=headers)
        return l_result['aggregations'][p_agg_name]['buckets']

    def update(self, index, id, body, headers=None):
        """
        client = EsClient().update("test_log_1", 'xQAwR3YBGr1x55HFO65t', {'module': 'test_es'})
        """
        r_body = {'doc': body}
        self._client.update(index, id, r_body, headers=headers)

    def write(self, p_data_list):
        """
        数据写入函数

        """
        l_tmp_list = []
        for l_data in p_data_list:
            l_tmp_list.append(l_data)
            if len(l_tmp_list) == 1000:
                helpers.bulk(self._client, l_tmp_list)
                l_tmp_list.clear()

        if len(l_tmp_list) > 0:
            helpers.bulk(self._client, l_tmp_list)
            l_tmp_list.clear()

    def create_mapping(self, index_name, mapping):
        '''
        创建es mapping
        :param index_name:
        :param mapping:
        :return:
        '''
        result = ''
        if not self._client.indices.exists(index=index_name):
            self._client.indices.create(index=index_name, ignore=400)
        result = self._client.indices.put_mapping(
            index=index_name, body=mapping)
        return result

    def get_setting(self, index_name):
        '''
        获取索引设置
        :param index_name:
        :return:
        '''
        result = self._client.indices.get_settings(index_name)
        return result

    def get_mapping(self, index_name):
        '''
        获取索引mapping
        :param index_name:
        :return:
        '''
        result = self._client.indices.get_mapping(index_name)
        return result

    def put_settings(self, index_name, body):
        '''
        设置索引
        :param index_name:
        :param body:
        :return:
        '''
        result = self._client.indices.put_settings(body, index_name)
        return result

    def delete_index(self, index_name):
        '''
        删除索引
        :param index_name:
        :return:
        '''
        result = ''
        if self._client.indices.exists(index=index_name):
            result = self._client.indices.delete(
                index=index_name, ignore=[400, 404])
            return result
        return result

    def refresh(self, index_name):
        '''
        刷新索引
        :param index_name:
        :return:
        '''
        result = self._client.indices.refresh(index_name, request_timeout=600)
        return result

    def get_one_byid(self, index_name, _id):
        '''
        根据_id 查询数据
        :param index_name:
        :param _id:
        :return:
        '''
        result = self._client.get(index=index_name, id=_id)
        return result

    def query_all(self, index_name, query_dict):
        '''
        查询所有数据
        :param index_name:
        :param query_dict:
        :return:
        '''
        result = self._client.search(
            index=index_name,
            body=query_dict,
            request_timeout=600)
        return result

    def scroll_search(self, index_name, query_dict):
        '''
        针对大量数据使用scroll迭代查询
        :param index_name:
        :param query_dict:
        :return:
        '''
        result = self._client.search(
            index=index_name,
            body=query_dict,
            scroll="1m",
            request_timeout=600)
        return result

    def scroll(self, sid):
        '''
        根据scroll id查询
        :param sid:
        :return:
        '''
        result = self._client.scroll(
            scroll_id=sid, scroll='10m', request_timeout=600)
        return result

    def deleteAllDocByIndex(self, index_name):
        '''
        根据索引删除所有记录
        :param index_name:
        :return:
        '''
        query = {'query': {'match_all': {}}}
        return self._client.delete_by_query(
            index=index_name, body=query, request_timeout=600)

    def deleteAllByQuery(self, index_name, query):
        '''
        根据查询条件删除对应记录
        :param index_name:
        :param query:
        :return:
        '''
        return self._client.delete_by_query(index=index_name, body=query)

    def insert_one_byid(self, index_name, row_obj):
        '''
        根据_id 插入记录
        :param index_name:
        :param row_obj:
        :return:
        '''
        _id = row_obj.get("_id", 1)
        row_obj.pop("_id")
        result = self._client.index(index=index_name, body=row_obj, id=_id)
        return result

    def insert_one(self, index_name, body):
        '''
        插入一条记录
        :param index_name:
        :param body:
        :return:
        '''
        result = self._client.index(index=index_name, body=body)
        return result

    def update_data_bulk(self, index_name, row_obj_list, upsert=False):
        '''
        批量更新
        :param index_name: 索引名
        :param row_obj_list: 记录列表，每条需要有_id
        :return:
        '''
        load_data = []
        for row_obj in row_obj_list:
            # new
            action = {}
            if "_id" in row_obj:
                action['_id'] = row_obj.get('_id', 'None')
                row_obj.pop("_id")
                action['_op_type'] = 'update'
                action['doc'] = {}
                for r_o_i in row_obj:
                    action['doc'][r_o_i] = row_obj.get(r_o_i, None)
                if upsert:
                    action['doc_as_upsert'] = True
                load_data.append(action)
        result = {}
        if load_data:
            success, failed = helpers.bulk(
                self._client, load_data, index=index_name, raise_on_error=True, request_timeout=1000)
            result['success'] = success
            result['failed'] = failed
        return result

    def add_data_bulk(self, index_name, row_obj_list):
        '''
        批量插入
        :param index_name:
        :param row_obj_list:
        :return:
        '''
        load_data = []
        for row_obj in row_obj_list:
            # new
            action = {}
            action['_index'] = index_name
            if '_id' in row_obj:
                action['_id'] = row_obj.get('_id', 'None')
                row_obj.pop("_id")
            action['_source'] = {}
            for r_o_i in row_obj:
                action['_source'][r_o_i] = row_obj.get(r_o_i, None)
            load_data.append(action)
        result = {}
        if load_data:
            success, failed = helpers.bulk(
                self._client, load_data, index=index_name, raise_on_error=True, request_timeout=1000)
            result['success'] = success
            result['failed'] = failed
        return result

    def delete_data_bulk(self, index_name, row_obj_list):
        '''
        批量删除
        :param index_name:
        :param row_obj_list:
        :return:
        '''
        load_data = []
        for row_obj in row_obj_list:
            # new
            action = {}
            action['_op_type'] = 'delete'
            if "_id" in row_obj:
                action['_id'] = row_obj.get('_id', 'None')
                row_obj.pop("_id")
                load_data.append(action)
        result = {}
        if load_data:
            success, failed = helpers.bulk(
                self._client, load_data, index=index_name, raise_on_error=True, request_timeout=1000)
            result['success'] = success
            result['failed'] = failed
        return result

    def update_by_id(self, index_name, row_obj):
        '''
        根据_id更新记录
        :param index_name:
        :param row_obj:
        :return:
        '''
        _id = row_obj.get("_id", 1)
        row_obj.pop("_id")
        result = self._client.update(
            index=index_name, body={
                "doc": row_obj}, id=_id, request_timeout=600)
        return result

    def delete_by_id(self, index_name, _id):
        '''
        根据_id 删除记录
        :param index_name:
        :param _id:
        :return:
        '''
        result = self._client.delete(index=index_name, id=_id)
        return result

    def deleteDocByQuery(self, index_name, query):
        '''
        根据查询条件删除记录
        :param index_name:
        :param query:
        :return:
        '''
        return self._client.delete_by_query(index=index_name, body=query)

