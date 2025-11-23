
后端启动
----
### 依赖安装
```
pip install -r requirements.txt -i https://pypi.doubanio.com/simple
```
### 系统web接口服务
```
python web_api.py
```
### 系统任务调度接口服务
```
python scheduler_api.py
```
## celery相关
启动worker
- windows
```
celery -A tasks worker -P eventlet
```
- linux
```
celery -A tasks worker
```
启动flower
```
celery -A tasks flower
```

