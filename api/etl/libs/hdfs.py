import pyhdfs


class HdfsClient(object):
    def __init__(self, hosts, user_name='root', randomize_hosts=True, timeout=60, max_tries=2, retry_delay=5, requests_session=None, requests_kwargs=None):
        self.hosts = hosts
        self.randomize_hosts = randomize_hosts
        self.user_name = user_name
        self.timeout = timeout
        self.max_tries = max_tries
        self.retry_delay = retry_delay
        self.requests_session = requests_session
        self.requests_kwargs = requests_kwargs

        self.hdfs_client = self.connect_hdfs()

    def connect_hdfs(self):
        hdfs_client = pyhdfs.HdfsClient(hosts=self.hosts, user_name=self.user_name, timeout=self.timeout)
        return hdfs_client

    # 返回指定目录下的所有文件
    def listdir(self, path="/", **kwargs):
        return self.hdfs_client.listdir(path, **kwargs)

    # 返回用户的根目录
    def get_home_directory(self):
        return self.hdfs_client.get_home_directory()

    # 返回可用的namenode节点
    def get_active_namenode(self):
        return self.hdfs_client.get_active_namenode()

    # 从集群上copy到本地
    # local = /data/123.txt
    # remote = /user/root/123.txt
    def copy_to_local(self, local, remote, **kwargs):
        return self.hdfs_client.copy_to_local(local, remote, **kwargs)

    # 从本地上传文件至集群
    def copy_from_local(self, local, remote, **kwargs):
        return self.hdfs_client.copy_from_local(local, remote, **kwargs)

    # 判断目录、文件是否存在
    def is_exist(self, path, **kwargs):
        return self.hdfs_client.exists(path, **kwargs)

    # 返回目录下的所有目录，路径，文件名
    def walk(self, path, **kwargs):
        return list(self.hdfs_client.walk(path, **kwargs))

    # 删除目录、文件
    def delete(self, path):
        if '.' in path:
            return self.hdfs_client.delete(path)  # 删除文件
        else:
            try:
                return self.hdfs_client.delete(path, recursive=True)  # 删除目录  recursive=True
            except:
                return self.hdfs_client.delete(path)  # 删除文件

    # 打开文件
    def open(self, path, **kwargs):
        response = self.hdfs_client.open(path, **kwargs)
        return response.read()

    # 向已有文件中添加数据
    def append(self, path, data, **kwargs):
        self.hdfs_client.append(path, data, **kwargs)

    # 融合两个文件
    def concat(self, target, source, **kwargs):
        self.hdfs_client.concat(target, source, **kwargs)

    # 创建新目录
    def mkdirs(self, path, **kwargs):
        self.hdfs_client.mkdirs(path, **kwargs)

    # 查看文件的校验和(checksum)
    def checksum(self,path,**kwargs):
        return self.hdfs_client.get_file_checksum(path, **kwargs)

    # 查看当前路径的状态(可路径可文件)
    def list_status(self, path, **kwargs):
        return self.hdfs_client.list_status(path, **kwargs)

    # 重命名
    def rename(self, source, target):
        self.hdfs_client.rename(target, source, target)

    # 创建文件
    def create(self, path, data, **kwargs):
        return self.hdfs_client.create(path, data, **kwargs)



