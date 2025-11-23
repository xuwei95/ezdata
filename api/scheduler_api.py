'''
任务调度系统
'''
from flask import Flask, jsonify
from flask_cors import CORS
from web_apps.scheduler.views import scheduler_bp
from web_apps.scheduler.services.scheduler_service import scheduler, init_scheduler
from web_apps.scheduler.scheduler_config import SchedulerConfig
import config


app = Flask(__name__)
# 加载配置文件
app.config.from_object(config)
CORS(app, supports_credentials=True)  # 跨域支持
# 为实例化的flask引入定时任务配置
app.config.from_object(SchedulerConfig())


@app.route('/')
def rend_html():
    return jsonify({'msg': 'ok'})


app.register_blueprint(scheduler_bp, url_prefix="/api/scheduler")
scheduler.init_app(app)  # 把任务列表载入实例flask
if __name__ == '__main__':
    scheduler.start()  # 启动任务计划
    init_scheduler()  # 初始化调度器
    app.run(debug=False, port=8002, host='0.0.0.0')
