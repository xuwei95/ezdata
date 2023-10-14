# docker 安装
curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun
# docker-compose 安装
curl -SL https://github.com/docker/compose/releases/download/v2.12.2/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose

## 构建镜像
docker build -t ezdata:1.0 .
## 导出容器
docker export 容器ID > ezdata.tar
## 导入容器
docker import ezdata.tar ezdata:1.0
## 导出镜像文件
docker save -o ezdata_1.0.tar ezdata:1.0
## 导入镜像文件
docker load -i ezdata_1.0.tar
## 上传镜像
docker login
docker tag local_image_name:tag docker_hub_username/repository_name:tag
docker push docker_hub_username/repository_name:tag
## docker-compose
```
# 启动
docker-compose up -d
# 停止
docker-compose stop
# 停止并删除
docker-compose down
# 查看日志
docker-compose logs -f
```
## 其他
### es
- 挂载前需要 chmod -R 777 elasticsearch
- 设置密码 进入容器
- ./bin/elasticsearch-setup-passwords interactive
- curl -H "Content-Type:application/json" -XPOST -u elastic 'http://127.0.0.1:9200/_xpack/security/user/elastic/_password' -d '{ "password" : "ezdata123" }'
- 安装es sql插件  ./bin/elasticsearch-plugin install https://github.com/NLPchina/elasticsearch-sql/releases/download/7.17.2.0/elasticsearch-sql-7.17.2.0.zip


## xorbits
### master
docker run -it -d -p 8008:8008 -p 9009:9009 -p 9010:9010 --name xorbits-master --network host python:3.8.8
### worker
docker run -it -d -p 9010:9010 --name xorbits-worker --network host python:3.8.8
### 依赖安装
pip install 'xorbits[extra]' -i https://pypi.doubanio.com/simple
### 运行
nohup xorbits-supervisor -H 10.0.4.16 -p 9009 -w 8008 2>&1 &
nohup xorbits-worker -H 10.0.4.16 -p 9010 -s 10.0.4.16:9009 2>&1 &
nohup xorbits-worker -H 10.0.4.17 -p 9010 -s 10.0.4.16:9009 2>&1 &