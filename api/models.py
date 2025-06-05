# coding: utf-8
from web_apps import db
import datetime
import json


class BaseModel(db.Model):
    '''
    数据库orm模型基类
    '''
    __abstract__ = True
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='id主键')
    tenant_id = db.Column(db.Integer, default=1, index=True, comment='租户id')
    description = db.Column(db.Text, default='', comment='简介')
    sort_no = db.Column(db.Float, default=1, comment='排序')
    del_flag = db.Column(db.SmallInteger, default=0, comment='软删除标记')
    create_by = db.Column(db.String(100), default='', comment='创建者')
    create_time = db.Column(
        db.TIMESTAMP,
        server_default=db.text('CURRENT_TIMESTAMP'),
        comment='创建时间')
    update_by = db.Column(db.String(100), default='', comment='修改者')
    update_time = db.Column(
        db.TIMESTAMP,
        server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
        comment='修改时间')

    def to_dict(self, date_type='str'):
        '''
        转为字典
        :return:
        '''
        value = {}
        for column in self.__table__.columns:
            attribute = getattr(self, column.name)
            if isinstance(attribute, datetime.datetime) and date_type == 'str':
                attribute = str(attribute)
            value[column.name] = attribute
        return value

    def from_dict(self, attributes):
        """Update the current instance base on attribute->value by *attributes*"""
        for attribute in attributes:
            setattr(self, attribute, attributes[attribute])
        return self


class User(BaseModel):
    '''
    用户表
    '''
    __tablename__ = 'sys_user'
    username = db.Column(db.String(100), index=True, comment='登录的用户名')
    password = db.Column(db.String(256), index=True, comment='密码')
    nickname = db.Column(db.String(100), index=True, comment='昵称')
    avatar = db.Column(db.String(1024), comment='头像')
    birthday = db.Column(db.DateTime, comment='生日')
    sex = db.Column(db.SmallInteger, default=0, comment='性别(0-默认未知,1-男,2-女)')
    email = db.Column(db.String(45), index=True, comment='邮箱')
    phone = db.Column(db.String(45), index=True, comment='手机号')
    org_code = db.Column(db.String(64), index=True, comment='登录会话的机构编码')
    tenant_id = db.Column(db.Integer, index=True, comment='登录会话的租户id')
    status = db.Column(db.SmallInteger, default=1, comment='2-冻结,1-正常,0-禁用')
    user_identity = db.Column(db.SmallInteger, default=1, comment='身份(1普通成员 2上级)')
    third_id = db.Column(db.String(100), index=True, comment='第三方登陆的唯一标志')
    third_type = db.Column(db.String(100), comment='第三方登陆的类型')
    work_no = db.Column(db.String(100), index=True, comment='工号')
    verify_token = db.Column(db.String(50), default='', comment='验证token')
    login_times = db.Column(db.Integer, default=0, comment='登录次数')
    login_time = db.Column(db.Integer, comment='上次登录时间')
    login_ip = db.Column(db.String(500), comment='上次登录IP')
    valid_start_time = db.Column(db.Integer, comment='有效期(开始)')
    valid_end_time = db.Column(db.Integer, comment='有效期（结束）')

    def _get_join_obj(self):
        """获取用户租户关联对象，不存在则创建"""
        join_obj = db.session.query(UserTenantJoin).filter_by(
            tenant_id=self.tenant_id,
            user_id=self.id
        ).first()
        if not join_obj:
            join_obj = UserTenantJoin(
                tenant_id=self.tenant_id,
                user_id=self.id
            ).save()
            db.session.add(join_obj)
        return join_obj

    @property
    def depart_id_list(self) -> str:
        join_obj = db.session.query(UserTenantJoin).filter_by(
            tenant_id=self.tenant_id,
            user_id=self.id
        ).first()
        return join_obj.depart_id_list if join_obj else '[]'

    @property
    def post_id_list(self) -> str:
        join_obj = db.session.query(UserTenantJoin).filter_by(
            tenant_id=self.tenant_id,
            user_id=self.id
        ).first()
        return join_obj.post_id_list if join_obj else '[]'

    @property
    def role_id_list(self) -> str:
        join_obj = db.session.query(UserTenantJoin).filter_by(
            tenant_id=self.tenant_id,
            user_id=self.id
        ).first()
        return join_obj.role_id_list if join_obj else '["1"]'

    @property
    def tenant_id_list(self) -> str:
        join_objs = db.session.query(UserTenantJoin).filter_by(user_id=self.id).all()
        return json.dumps([str(i.tenant_id) for i in join_objs])


class Tenant(BaseModel):
    '''
    租户表
    '''
    __tablename__ = 'sys_tenant'
    name = db.Column(db.String(100), comment='租户名称')
    begin_date = db.Column(db.Integer, comment='开始时间')
    end_date = db.Column(db.Integer, comment='结束时间')
    status = db.Column(db.SmallInteger, default=1, comment='状态 1正常 0冻结')


class UserTenantJoin(BaseModel):
    __tablename__ = 'sys_user_tenant_join'

    user_id = db.Column(db.Integer, nullable=False, comment='用户ID')
    tenant_id = db.Column(db.Integer, nullable=False, comment='租户ID')
    depart_id_list = db.Column(db.Text, default='[]', comment='部门列表')
    post_id_list = db.Column(db.Text, default='[]', comment='职务列表')
    role_id_list = db.Column(db.Text, default='[]', comment='角色列表')


class Role(BaseModel):
    '''
    角色表
    '''
    __tablename__ = 'sys_role'
    role_name = db.Column(db.String(100), index=True, comment='角色名称')
    role_code = db.Column(db.String(100), index=True, comment='角色编码')
    status = db.Column(db.SmallInteger, default=1, comment='1-正常,0-禁用')
    permissions = db.Column(db.Text, default='[]', comment='权限列表')


class Depart(BaseModel):
    '''
    部门表
    '''
    __tablename__ = 'sys_depart'
    depart_name = db.Column(db.String(100), index=True, comment='机构/部门名称')
    parent_id = db.Column(db.Integer, comment='父级ID')
    depart_name_en = db.Column(db.String(500), index=True, comment='英文名')
    depart_name_abbr = db.Column(db.String(500), index=True, comment='缩写')
    org_category = db.Column(db.SmallInteger, default=1, comment='机构类别 1公司，2组织机构，2岗位')
    org_type = db.Column(db.SmallInteger, default=1, comment='机构类型 1一级部门 2子部门')
    org_code = db.Column(db.String(100), index=True, comment='机构编码')
    mobile = db.Column(db.String(32), comment='手机号')
    fax = db.Column(db.String(32), comment='传真')
    address = db.Column(db.String(100), comment='地址')
    memo = db.Column(db.String(500), comment='备注')
    is_leaf = db.Column(db.SmallInteger, default=1, comment='是否叶子节点: 1:是   0:不是')
    status = db.Column(db.SmallInteger, default=1, comment='状态（1启用，0不启用）')
    qywx_identifier = db.Column(db.String(100), comment='对接企业微信的ID')
    permissions = db.Column(db.Text, default='[]', comment='权限列表')


class Position(BaseModel):
    '''
    职务表
    '''
    __tablename__ = 'sys_position'
    name = db.Column(db.String(100), comment='名称')
    code = db.Column(db.String(100), comment='编码')
    org_code = db.Column(db.String(100), default='', comment='所属机构编码')
    post_rank = db.Column(db.Integer, default=1, comment='职级')
    company_id = db.Column(db.Integer, comment='公司id')


class PerMission(BaseModel):
    '''
    权限表
    '''
    __tablename__ = 'sys_permission'
    name = db.Column(db.String(100), index=True, comment='名称')
    parent_id = db.Column(db.Integer, comment='父级ID')
    url = db.Column(db.String(255), default="", comment='路径')
    component = db.Column(db.String(255), default="", comment='组件')
    component_name = db.Column(db.String(100), default="", comment='组件名称')
    redirect = db.Column(db.String(255), default="", comment='一级菜单跳转地址')
    menu_type = db.Column(db.SmallInteger, default=0, comment='菜单类型(0:一级菜单; 1:子菜单:2:按钮权限)')
    perms = db.Column(db.String(255), comment='菜单权限编码')
    perms_type = db.Column(db.SmallInteger, default=1, comment='权限策略1显示2禁用')
    always_show = db.Column(db.SmallInteger, default=1, comment='聚合子路由: 1是0否')
    icon = db.Column(db.String(255), comment='菜单图标')
    is_route = db.Column(db.SmallInteger, default=1, comment='是否路由菜单: 0:不是  1:是（默认值1）')
    is_leaf = db.Column(db.SmallInteger, default=1, comment='是否叶子节点: 1:是   0:不是')
    keep_alive = db.Column(db.SmallInteger, default=1, comment='是否缓存该页面:   1:是   0:不是')
    hidden = db.Column(db.SmallInteger, default=1, comment='是否隐藏路由: 0否,1是')
    hide_tab = db.Column(db.SmallInteger, default=1, comment='是否隐藏tab: 0否,1是')
    rule_flag = db.Column(db.SmallInteger, default=0, comment='是否添加数据权限1是0否')
    status = db.Column(db.SmallInteger, default=1, comment='按钮权限状态(0无效1有效)')
    internal_or_external = db.Column(db.SmallInteger, default=1, comment='外链菜单打开方式 0/内部打开 1/外部打开')


class Dict(BaseModel):
    '''
    数据字典表
    '''
    __tablename__ = 'sys_dict'
    dict_name = db.Column(db.String(100), comment='字典名称')
    dict_code = db.Column(db.String(100), default='', comment='字典编码')
    type = db.Column(db.SmallInteger, default=1, comment='字典值类型，0为string,1为number')


class DictItem(BaseModel):
    '''
    数据字典详情
    '''
    __tablename__ = 'sys_dict_item'
    dict_id = db.Column(db.Integer, comment='所属字典id')
    name = db.Column(db.String(50), comment='字典项文本')
    value = db.Column(db.String(50), default='', comment='字典项值')
    extend = db.Column(db.Text, default='{}', comment='额外参数')
    status = db.Column(db.SmallInteger, default=1, comment='状态（1启用 0禁用）')


class File(BaseModel):
    '''
    文件资源表
    '''
    __tablename__ = 'sys_file'
    file_name = db.Column(db.String(255), nullable=True, comment='文件名称')
    url = db.Column(db.TEXT, nullable=True, comment='文件地址')
    file_type = db.Column(db.String(50), nullable=True, comment='文档类型（folder:文件夹 excel:excel doc:word ppt:ppt image:图片  archive:其他文档 video:视频 pdf:pdf）')
    store_type = db.Column(db.String(50), nullable=True, comment='文件上传类型(temp/本地上传(临时文件) manage/知识库)')
    parent_id = db.Column(db.Integer, comment='父级id')
    file_size = db.Column(db.Float, comment='文件大小（kb）')
    iz_folder = db.Column(db.SmallInteger, default=0, comment='是否文件夹(1：是  0：否)')
    iz_root_folder = db.Column(db.SmallInteger, default=0, comment='是否为1级文件夹，允许为空 (1：是 )')
    iz_star = db.Column(db.SmallInteger, default=0, comment='是否标星(1：是  0：否)')
    down_count = db.Column(db.Integer, default=0, comment='下载次数')
    read_count = db.Column(db.Integer, default=0, comment='阅读次数')
    share_url = db.Column(db.String(255), comment='分享链接')
    share_perms = db.Column(db.SmallInteger, default=0, comment='分享权限(1.关闭分享 2.允许所有联系人查看 3.允许任何人查看)')
    enable_down = db.Column(db.SmallInteger, default=0, comment='是否允许下载(1：是  0：否)')
    enable_update = db.Column(db.SmallInteger, default=0, comment='是否允许修改(1：是  0：否)')


class Notice(BaseModel):
    '''
    通知公告
    '''
    __tablename__ = 'sys_notice'
    title = db.Column(db.String(200), comment='标题')
    msg_content = db.Column(db.Text, comment='内容')
    start_time = db.Column(db.Integer, comment='开始时间')
    end_time = db.Column(db.Integer, comment='结束时间')
    sender = db.Column(db.String(100), comment='发送人')
    priority = db.Column(db.String(10), default='M', comment='优先级（L低，M中，H高）')
    msg_category = db.Column(db.String(10), comment='消息类型1:通知公告2:系统消息')
    msg_type = db.Column(db.String(10), comment='通告对象类型（USER:指定用户，ALL:全体用户）')
    send_status = db.Column(db.String(10), default='0', comment='发布状态（0未发布，1已发布，2已撤销）')
    send_time = db.Column(db.Integer, comment='发送时间')
    cancel_time = db.Column(db.Integer, comment='撤销时间')
    bus_type = db.Column(db.String(20), comment='业务类型(email:邮件 bpm:流程)')
    bus_id = db.Column(db.String(50), comment='业务id')
    open_type = db.Column(db.String(20), comment='打开方式(组件：component 路由：url)')
    open_page = db.Column(db.String(255), comment='组件/路由 地址')
    user_ids = db.Column(db.Text, default='[]', comment='指定用户')
    msg_abstract = db.Column(db.Text, default='', comment='摘要')
    dt_task_id = db.Column(db.String(100), comment='钉钉task_id，用于撤回消息')


class NoticeSend(BaseModel):
    '''
    通知公告发送记录
    '''
    __tablename__ = 'sys_notice_send'
    notice_id = db.Column(db.Integer, comment='通知id')
    user_id = db.Column(db.Integer, comment='用户id')
    read_flag = db.Column(db.SmallInteger, default=0, comment='阅读状态（0未读，1已读）')
    star_flag = db.Column(db.SmallInteger, default=0, comment='标星状态( 1为标星 空/0没有标星)')
    read_time = db.Column(db.Integer, comment='阅读时间')


if __name__ == '__main__':
    from web_apps import db, app
    with app.app_context():
        db.create_all()
        db.session.commit()
        db.session.flush()
