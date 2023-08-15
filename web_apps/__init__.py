from flask import Flask, request, jsonify
import config
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# 加载配置文件
app.config.from_object(config)
db = SQLAlchemy(app, session_options={'autocommit': True})


@app.route('/api')
def api_index():
    if request.method == 'GET':
        return jsonify({'msg': 'hello world'})
    if request.method == 'POST':
        return jsonify({'msg': 'hello world'})



