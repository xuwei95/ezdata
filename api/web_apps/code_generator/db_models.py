from web_apps import db
from models import BaseModel


class CodeGenModel(BaseModel):
    '''
    代码生成器模型
    '''
    __tablename__ = 'code_gen_model'
    id = db.Column(db.String(36), primary_key=True, comment='主键')
    title = db.Column(db.String(255), default='', comment='项目名称')
    module_name = db.Column(db.String(255), default='', comment='模块文件名称')
    api_prefix = db.Column(db.String(255), default='', comment='api接口前缀，不设默认使用模块文件名称')
    model_name = db.Column(db.String(255), default='', comment='模型名称')
    model_value = db.Column(db.String(255), default='', comment='模型值')
    extend_base_model = db.Column(db.SmallInteger, default=1, comment='是否继承基础模型类1是0不是')
    table_name = db.Column(db.String(255), default='', comment='数据库表名')
    table_desc = db.Column(db.String(255), default='', comment='数据库表描述')
    model_type = db.Column(db.SmallInteger, default=1, comment='模型类型1单表')
    query_params = db.Column(db.Text, default='[]', comment='高级查询参数')
    buttons = db.Column(db.Text, default='[]', comment='按钮设置')
    fields = db.Column(db.Text, default='[]', comment='字段列表')
    form_style = db.Column(db.SmallInteger, default=1, comment='表单风格1一列2两列3三列4四列')
    frontend_gen_type = db.Column(db.SmallInteger, default=1, comment='前端生成代码类型1vue3模版,2vue3原生,3vue2')
    backend_gen_type = db.Column(db.SmallInteger, default=1, comment='后端生成代码类型1flaREDACTEDsqlalchemy模版')
    is_scroll = db.Column(db.SmallInteger, default=1, comment='滚动条1有0无')
    modal_type = db.Column(db.SmallInteger, default=1, comment='编辑弹窗类型1弹窗2抽屉')
    modal_width = db.Column(db.Integer, default=800, comment='弹窗宽度，为0则全屏')
    is_sync = db.Column(db.SmallInteger, default=0, comment='是否已同步数据库1是0不是')


if __name__ == '__main__':
    db.create_all()
    db.session.commit()
    db.session.flush()