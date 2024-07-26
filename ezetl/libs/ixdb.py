# encoding: utf-8
"""
@Description: influxdb 操作封装类
"""
import time
import pandas as pd
from influxdb import InfluxDBClient


class IxClient(object):
    """
    :param host: hostname to connect to InfluxDB, defaults to 'localhost'
    :type host: str
    :param port: port to connect to InfluxDB, defaults to 8086
    :type port: int
    :param username: user to connect, defaults to 'root'
    :type username: str
    :param password: password of the user, defaults to 'root'
    :type password: str
    :param pool_size: urllib3 connection pool size, defaults to 10.
    :type pool_size: int
    :param database: database name to connect to, defaults to None
    :type database: str
    :param ssl: use https instead of http to connect to InfluxDB, defaults to
        False
    :type ssl: bool
    :param verify_ssl: verify SSL certificates for HTTPS requests, defaults to
        False
    :type verify_ssl: bool
    :param timeout: number of seconds Requests will wait for your client to
        establish a connection, defaults to None
    :type timeout: int
    :param retries: number of retries your client will try before aborting,
        defaults to 3. 0 indicates try until success
    :type retries: int
    :param use_udp: use UDP to connect to InfluxDB, defaults to False
    :type use_udp: bool
    :param udp_port: UDP port to connect to InfluxDB, defaults to 4444
    :type udp_port: int
    :param proxies: HTTP(S) proxy to use for Requests, defaults to {}
    :type proxies: dict
    :param path: path of InfluxDB on the server to connect, defaults to ''
    :type path: str
    :param cert: Path to client certificate information to use for mutual TLS
        authentication. You can specify a local cert to use
        as a single file containing the private key and the certificate, or as
        a tuple of both files’ paths, defaults to None
    :type cert: str
    :param gzip: use gzip content encoding to compress requests
    :type gzip: bool
    :param session: allow for the new client request to use an existing
        requests Session, defaults to None
    :type session: requests.Session
    :raises ValueError: if cert is provided but ssl is disabled (set to False)
    """

    def __init__(self, **kwargs):
        self._client = InfluxDBClient(**kwargs)

    def create_database(self, database):
        '''
        创建数据库
        '''
        self._client.create_database(database)

    def get_list_database(self):
        '''
        获取数据库列表
        '''
        return self._client.get_list_database()

    def get_tables(self):
        '''
        获取数据库中的表
        '''
        return self._client.query("show measurements")

    def query(self, p_sql, **kwargs):
        """
        返回查询结果列表
        时间默认为秒返回
        """
        if not kwargs.get('epoch'):
            kwargs['epoch'] = 's'
        return self._client.query(p_sql, **kwargs)

    def query_as_points(self, p_sql, **kwargs):
        """
        返回查询结果列表
        时间默认为秒返回
        """
        if not kwargs.get('epoch'):
            kwargs['epoch'] = 's'
        return self._client.query(p_sql, **kwargs).get_points()

    def query_as_df(self, p_sql, **kwargs):
        """
        返回查询结果列表
        时间默认为秒返回
        """
        if not kwargs.get('epoch'):
            kwargs['epoch'] = 's'
        return pd.DataFrame(self.query_as_points(p_sql, **kwargs))

    def write_points(self, p_points):
        self._client.write_points(p_points, batch_size=5000)


class IxOutput(object):
    """
    为了提高性能，部分写入操作可以适当缓存写入
    """

    def __init__(self, **kwargs):
        self._client = IxClient(**kwargs)
        self._cache = []
        self._cache_max_size = kwargs.get('cache_size', 500)
        self._cache_max_seconds = kwargs.get('cache_seconds', 2)
        self._cache_last_time = time.time()

    def save_with_cache(self, points):
        """
        缓存写入数据
        """
        self._cache.extend(points)
        if len(self._cache) >= self._cache_max_size or time.time() - self._cache_last_time >= self._cache_max_seconds:
            self._client.write_points(self._cache)
            self._cache.clear()
            self._cache_last_time = time.time()

    def save(self, points):
        self._client.write_points(points)

    def save_when_exit(self):
        if len(self._cache) > 0:
            self._client.write_points(self._cache)
            self._cache.clear()
            self._cache_last_time = time.time()

