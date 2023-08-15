基于python开发的低代码数据处理和任务调度系统。
支持数据源管理，数据模型管理，数据集成，数据查询API接口封装，数据可视化大屏，低代码自定义数据处理任务模版，单任务及dag任务工作流调度等功能。
demo地址：http://api.naivdata.com/
### 依赖安装
pip install -r requirements.txt -i https://pypi.doubanio.com/simple
### 系统web接口服务
python web_api.py
### 系统任务调度接口服务
python scheduler_api.py
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

