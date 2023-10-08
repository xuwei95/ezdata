apt-get update
apt-get install wget curl apt-transport-https -y
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-7.x.list
apt-get update && apt-get install elasticsearch
service elasticsearch start
# es地址 /usr/share/elasticsearch
# es配置地址 /etc/elasticsearch/elasticsearch.yml
# nginx
apt-get install nginx
# minio
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
mv minio /usr/bin/minio
mkdir /opt/minio-data
export MINIO_ROOT_USER=minio                                                                                                                                    │·················
export MINIO_ROOT_PASSWORD=ezdata123
minio server /opt/minio-data
nohup minio server /opt/minio-data --console-address :19001 2>&1 &
# mysql
wget https://dev.mysql.com/get/mysql-apt-config_0.8.16-1_all.deb
dpkg -i mysql-apt-config_0.8.16-1_all.deb
apt-get install mysql-server
alter user'root'@'%' identified with mysql_native_password by 'ezdata123';
# redis
apt-get install redis-server
配置文件路径
/etc/redis/redis.conf
持久化数据路径
/var/lib/redis
日志路径
/var/log/redis
vim /etc/redis/redis.conf
requirepass ezdata123
