from etl.data_models import DataModel


class HdfsModel(DataModel):

    def __init__(self, model_info):
        super().__init__(model_info)


import hdfs3

# 创建 HDFS 客户端连接
client = hdfs3.HDFileSystem(host='127.0.0.1', port=50070, user='hadoop')
with client.open('/path/to/file.txt', 'rb') as f:
    data = f.read()

# 将数据写入 HDFS
with client.open('/path/to/output.txt', 'wb') as f:
    f.write(data)