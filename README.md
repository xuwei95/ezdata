ezdata
===============

项目介绍
-----------------------------------
ezdata 是基于python后端和vue3前端开发的低代码数据处理和任务调度系统。

其主要功能如下
- 多数据源管理，支持连接文件，关系型数据库，nosql数据库，时序数据库，图数据库等多种数据源。
- 各数据源抽象为统一数据模型，支持创建，删除，字段管理，自定义查询取数，封装数据查询api接口等各种功能。
- 低代码数据集成，可视化处理流中每一步结果，可使用分布式pandas引擎拓展至tb级大型数据集，使用多种内置转换算法或自定义代码快速实现数据传输管道。
- 内置python，shell，数据集成等多种任务模版，也支持自定义任务模版，使用内置表单引擎或编写动态执行代码快速实现数据处理，网络爬虫，监控，自动化等各种任务需求及调度运行。
- 单任务和dag任务工作流调度，支持分布式worker执行，任务队列管理，任务失败重试，任务失败告警，任务运行日志及执行历史查看等调度系统功能。
- 数据可视化，低代码数据可视化大屏，拖拽设计及快速对接数据api接口。

项目链接
-----------------------------------
- 项目官网：  [http://www.ezdata.cloud](http://www.ezdata.cloud)

- 在线演示 ： [在线演示](http://110.40.157.36)

[comment]: <> (- 开发文档：  [主项目文档]&#40;http://www.ezdata.cloud/docs/hello.html&#41;)

项目源码
-----------------------------------
| 仓库  | 后端  |前端 | 数据大屏前端   |
|--------------------|--------------------|--------------------|--------------------|
| Github | [ezdata](https://github.com/xuwei95/ezdata) | [ezdata_frontend](https://github.com/xuwei95/ezdata_frontend)  | [ezdata_bigscreen](https://github.com/xuwei95/ezdata_bigscreen)  |
| 码云  | [ezdata](https://gitee.com/xuwei95/ezdata) | [ezdata_frontend](https://gitee.com/xuwei95/ezdata_frontend)  | [ezdata_bigscreen](https://gitee.com/xuwei95/ezdata_bigscreen)  |


系统效果
----
##### 主页
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/dashboard.png?raw=true "在这里输入图片标题")
##### 数据源管理
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/datasource.png?raw=true "在这里输入图片标题")
##### 数据模型管理
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/datamodel.png?raw=true "在这里输入图片标题")
##### 数据自定义查询及接口封装
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/data_query.png?raw=true "在这里输入图片标题")
##### 数据集成
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/etl.png?raw=true "在这里输入图片标题")
##### 任务模版管理
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/task_template.png?raw=true "在这里输入图片标题")

##### 任务调度
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/task_scheduler.png?raw=true "在这里输入图片标题")

##### dag任务工作流
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/dag_detail.png?raw=true "在这里输入图片标题")

##### worker执行节点管理
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/worker_ops.png?raw=true "在这里输入图片标题")

##### 数据可视化大屏
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/bigscreen1.png?raw=true "在这里输入图片标题")

![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/bigscreen2.png?raw=true "在这里输入图片标题")



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

