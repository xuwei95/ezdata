# encoding: utf-8
"""
@Description: prometheus 操作封装类
"""
import pandas as pd
from prometheus_api_client import PrometheusConnect


class PrometheusClient(object):
    """
    Prometheus 查询封装
    """

    def __init__(self, **kwargs):
        self._client = PrometheusConnect(**kwargs)

    def conn_test(self):
        return self._client.check_prometheus_connection()

    def get_all_metrics(self):
        '''
        获取metric列表
        '''
        return self._client.all_metrics()

    def query(self, p_sql, **kwargs):
        """
        返回查询结果列表
        """
        return self._client.custom_query(query=p_sql)

    def query_metric_value(self, metric_name, label_config, **kwargs):
        """
        返回查询结果列表
        时间默认为秒返回
        """
        res = self._client.get_current_metric_value(metric_name=metric_name, label_config=label_config)
        return res

    def query_as_df(self, p_sql, **kwargs):
        """
        返回查询结果列表
        时间默认为秒返回
        """
        return pd.DataFrame(self.query(p_sql, **kwargs))
