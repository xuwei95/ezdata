# coding: utf-8
'''
User模块服务
'''
import json
from web_apps import db
from models import User, Role, PerMission, Depart, Tenant, Position, UserTenantJoin
from utils.auth import encode_auth_token, decode_auth_token, set_insert_user, set_update_user
from utils.web_utils import get_user_ip
from utils.common_utils import get_now_time, gen_json_response, parse_json, format_date
from utils.query_utils import get_base_query
from werkzeug.security import generate_password_hash, check_password_hash

sex_map = {
    1: '男',
    2: '女',
    0: '未知'
}

status_map = {
    1: '正常',
    2: '冻结',
    0: '禁用'
}


def get_depart_id_map():
    '''
    获取部门字段映射
    :return:
    '''
    depart_objs = get_base_query(Depart).all()
    depart_map = {}
    for obj in depart_objs:
        depart_map[str(obj.id)] = obj.depart_name
    return depart_map


def serialize_user(obj, ser_type='list'):
    '''
    序列化用户数据
    :param obj:
    :param ser_type:
    :return:
    '''
    depart_map = get_depart_id_map()
    dic = {}
    if ser_type == 'list':
        dic = {
            'id': obj.id,
            'username': obj.username,
            'nickname': obj.nickname,
            'avatar': obj.avatar,
            'birthday': str(obj.birthday)[:19],
            'sex': obj.sex,
            'sex_dictText': sex_map.get(obj.sex),
            'email': obj.email,
            'phone': obj.phone,
            'org_code': obj.org_code,
            'status': obj.status,
            'status_dictText': status_map.get(obj.status),
            'user_identity': obj.user_identity,
            'third_id': obj.third_id,
            'third_type': obj.third_type,
            'work_no': obj.work_no,
            'depart_id_list': json.loads(obj.depart_id_list),
            'depart_id_list_text': ','.join([depart_map.get(i) for i in json.loads(obj.depart_id_list) if i in depart_map]),
            'post_id_list': ','.join(json.loads(obj.post_id_list)),
            'role_id_list': json.loads(obj.role_id_list),
            "tenant_id_list": json.loads(obj.tenant_id_list),
            'login_times': obj.login_times,
            'login_time': obj.login_time,
            'login_ip': obj.login_ip,
            'valid_start_time': format_date(obj.valid_start_time),
            'valid_end_time': format_date(obj.valid_end_time),
            'valid_time': [format_date(obj.valid_start_time, default=''), format_date(obj.valid_end_time, default='')],
        }
    return dic


class UserService(object):
    def __init__(self):
        pass

    def check_only_user(self, req_dict):
        '''
        检测用户重复
        :param req_dict:
        :return:
        '''
        res_data = True
        return gen_json_response(data=res_data, extends={'success': True})
    
    def get_user_permissions(self, role_code_list, org_code, is_admin=False, tenant_id=None):
        '''
        获取用户权限列表
        :return:
        '''
        perm_id_list = []
        role_obj_list = get_base_query(Role, tenant_id=tenant_id).filter(Role.role_code.in_(role_code_list)).all()
        for role_obj in role_obj_list:
            permissions = json.loads(role_obj.permissions)
            perm_id_list.extend(permissions)
        depart_obj = get_base_query(Depart, tenant_id=tenant_id).filter(Depart.org_code == org_code).first()
        if depart_obj:
            permissions = json.loads(depart_obj.permissions)
            perm_id_list.extend(permissions)
        perm_id_list = list(set(perm_id_list))
        perm_objs = get_base_query(PerMission, tenant_id=tenant_id).filter(PerMission.id.in_(perm_id_list)).all()
        perm_code_list = [i.perms for i in perm_objs]
        if is_admin:
            perm_code_list.append('*')
        return perm_code_list
    
    def get_depart_users(self, req_dict):
        '''
        查询部门用户列表
        :param req_dict:
        :return:
        '''
        depart_id = req_dict.get('depart_id', '')
        if depart_id == '':
            res_data = {
                'records': [],
                'total': 0
            }
            return gen_json_response(data=res_data)
        depart_obj = db.session.query(Depart).filter(Depart.id == depart_id).first()
        if depart_obj is None:
            return gen_json_response(code=400, msg='未知部门')
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        page = int(page)
        pagesize = int(pagesize)
        like_text = f'%"{depart_obj.id}"%'
        join_objs = get_base_query(UserTenantJoin).filter(User.depart_id_list.like(like_text)).all()
        user_ids = [i.user_id for i in join_objs]
        query = get_base_query(User).filter(User.id.in_(user_ids))
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        total = query.count()
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_user(obj)
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def get_user_departs(self, req_dict, res_type='response'):
        '''
        查询用户部门列表
        :param req_dict:
        :return:
        '''
        user_id = req_dict.get('user_id')
        user_obj = db.session.query(User).filter(User.id == user_id).first()
        if user_obj is None:
            return gen_json_response(code=400, msg='找不到该用户')
        org_id_list = json.loads(user_obj.depart_id_list)
        obj_list = get_base_query(Depart).filter(Depart.id.in_(org_id_list)).all()
        result = []
        for obj in obj_list:
            dic = {
                'id': obj.id,
                'org_code': obj.org_code,
                'depart_name': obj.depart_name
            }
            result.append(dic)
        if res_type == 'response':
            return gen_json_response(data=result)
        else:
            return result

    def edit_user_departs(self, req_dict):
        '''
        部门添加用户
        :param req_dict:
        :return:
        '''
        depart_id = req_dict.get('depart_id')
        if 'user_id' in req_dict:
            user_ids = [req_dict.get('user_id')]
        else:
            user_ids = req_dict.get('user_id_list')
        user_objs = db.session.query(User).filter(User.id.in_(user_ids)).all()
        print(user_ids, user_objs)
        for user_obj in user_objs:
            depart_id_list = json.loads(user_obj.depart_id_list)
            depart_id_list.append(str(depart_id))
            depart_id_list = list(set(depart_id_list))
            join_obj = user_obj._get_join_obj()
            join_obj.depart_id_list = json.dumps(depart_id_list)
            set_update_user(join_obj)
            db.session.add(join_obj)
        return gen_json_response(msg='操作成功。', extends={'success': True})

    def delete_user_departs(self, req_dict):
        '''
        删除用户部门关联
        :param req_dict:
        :return:
        '''
        depart_id = req_dict.get('depart_id')
        if 'user_id' in req_dict:
            user_ids = [req_dict.get('user_id')]
        else:
            user_ids = req_dict.get('user_ids').split(',')
        user_objs = db.session.query(User).filter(User.id.in_(user_ids)).all()
        for user_obj in user_objs:
            depart_id_list = json.loads(user_obj.depart_id_list)
            depart_id_list = [i for i in depart_id_list if i != str(depart_id)]
            join_obj = user_obj._get_join_obj()
            join_obj.depart_id_list = json.dumps(depart_id_list)
            set_update_user(join_obj)
            db.session.add(join_obj)
        return gen_json_response(msg='操作成功。', extends={'success': True})
    
    def select_depart(self, req_dict):
        '''
        切换部门
        :param req_dict:
        :return:
        '''
        username = req_dict.get('username')
        org_code = req_dict.get('org_code')
        tenant_id = req_dict.get('tenant_id')
        user_obj = get_base_query(User).filter(User.username == username).first()
        user_obj.org_code = org_code
        user_obj.tenant_id = tenant_id
        set_update_user(user_obj)
        db.session.add(user_obj)
        db.session.commit()
        db.session.flush()
        role_id_list = json.loads(user_obj.role_id_list)
        role_objs = get_base_query(Role).filter(Role.id.in_(role_id_list))
        role_code_list = [i.role_code for i in role_objs]
        permissions = self.get_user_permissions(role_code_list=role_code_list, org_code=org_code, is_admin=user_obj.username == 'admin')
        extends = {
            'roles': role_code_list,
            'permissions': permissions
        }
        token = encode_auth_token(user_obj, extends=extends)
        res_data = {
            'userInfo': serialize_user(user_obj),
            'token': token
        }
        return gen_json_response(data=res_data, extends={'success': True})

    def get_role_user_list(self, req_dict):
        '''
        查询角色用户列表
        :param req_dict:
        :return:
        '''
        role_id = req_dict.get('role_id')
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        like_text = f'%"{role_id}"%'
        join_objs = get_base_query(UserTenantJoin).filter(User.depart_id_list.like(like_text)).all()
        user_ids = [i.user_id for i in join_objs]
        query = get_base_query(User).filter(User.id.in_(user_ids))
        total = query.count()
        page = int(page)
        pagesize = int(pagesize)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_user(obj)
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def get_user_roles(self, req_dict):
        '''
        查询用户角色列表
        :param req_dict:
        :return:
        '''
        user_id = req_dict.get('user_id')
        user_obj = db.session.query(User).filter(User.id == user_id).first()
        if user_obj is None:
            return gen_json_response(code=400, msg='找不到该用户')
        role_id_list = json.loads(user_obj.role_id_list)
        obj_list = get_base_query(Role).filter(Role.id.in_(role_id_list)).all()
        result = []
        for obj in obj_list:
            dic = obj.to_dict()
            result.append(dic)
        return gen_json_response(data=result)

    def add_user_roles(self, req_dict):
        '''
        添加用户角色关联
        :param req_dict:
        :return:
        '''
        role_id = req_dict.get('role_id')
        if 'user_id' in req_dict:
            user_ids = [req_dict.get('user_id')]
        else:
            user_ids = req_dict.get('user_id_list')
        user_objs = db.session.query(User).filter(User.id.in_(user_ids)).all()
        print(user_ids, user_objs)
        for user_obj in user_objs:
            role_id_list = json.loads(user_obj.role_id_list)
            role_id_list.append(str(role_id))
            role_id_list = list(set(role_id_list))
            join_obj = user_obj._get_join_obj()
            join_obj.role_id_list = json.dumps(role_id_list)
            set_update_user(join_obj)
            db.session.add(join_obj)
        return gen_json_response(msg='操作成功。', extends={'success': True})

    def delete_user_roles(self, req_dict):
        '''
        删除用户角色关联
        :param req_dict:
        :return:
        '''
        role_id = req_dict.get('role_id')
        if 'user_id' in req_dict:
            user_ids = [req_dict.get('user_id')]
        else:
            user_ids = req_dict.get('user_ids').split(',')
        user_objs = db.session.query(User).filter(User.id.in_(user_ids)).all()
        for user_obj in user_objs:
            role_id_list = json.loads(user_obj.role_id_list)
            role_id_list = [i for i in role_id_list if i != str(role_id)]
            join_obj = user_obj._get_join_obj()
            join_obj.role_id_list = json.dumps(role_id_list)
            set_update_user(join_obj)
            db.session.add(join_obj)
        return gen_json_response(msg='操作成功。', extends={'success': True})

    def frozenBatch(self, req_dict):
        '''
        批量冻结
        '''
        ids = req_dict.get('ids')
        status = req_dict.get('status')
        if isinstance(ids, int):
            ids = [ids]
        else:
            ids = ids.split(',')
        obj_list = db.session.query(User).filter(User.id.in_(ids)).all()
        for obj in obj_list:
            obj.status = status
            set_update_user(obj)
            db.session.add(obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(msg='操作成功。', extends={'success': True})

    def change_password(self, req_dict):
        '''
        修改密码
        :param req_dict:
        :return:
        '''
        username = req_dict.get('username', '')
        password = req_dict.get('password', '')
        confirmPassword = req_dict.get('confirmPassword', '')
        if confirmPassword != password:
            gen_json_response(code=400, msg='两次密码输入不同！', extends={'success': False})
        user = db.session.query(User).filter_by(username=username, del_flag=0).first()
        if user is None:
            res_data = gen_json_response(code=400, msg='用户不存在！', extends={'success': False})
        else:
            user.password = generate_password_hash(password)
            set_update_user(user)
            db.session.add(user)
            db.session.commit()
            db.session.flush()
            res_data = gen_json_response(msg='修改成功!', extends={'success': True})
        return res_data

    def update_password(self, req_dict):
        '''
        修改密码
        :param req_dict:
        :return:
        '''
        username = req_dict.get('username', '')
        password = req_dict.get('password', '')
        oldpassword = req_dict.get('oldpassword', '')
        confirmpassword = req_dict.get('confirmpassword', '')
        if confirmpassword != password:
            gen_json_response(code=400, msg='两次密码输入不同！', extends={'success': False})
        user = db.session.query(User).filter_by(username=username, del_flag=0).first()
        if user is None:
            res_data = gen_json_response(code=400, msg='用户不存在！', extends={'success': False})
        else:
            pwd_valid = check_password_hash(user.password, oldpassword)
            if pwd_valid:
                user.password = generate_password_hash(password)
                set_update_user(user)
                db.session.add(user)
                db.session.commit()
                db.session.flush()
                res_data = gen_json_response(msg='修改成功!', extends={'success': True})
            else:
                res_data = gen_json_response(code=400, msg='旧密码错误！', extends={'success': False})
        return res_data

    def register(self, req_dict):
        username = req_dict.get('username', '')
        password = req_dict.get('password', '')
        phone = req_dict.get('phone', '')
        confirmPassword = req_dict.get('confirmPassword', '')
        if confirmPassword != password:
            gen_json_response(code=400, msg='两次密码输入不同！', extends={'success': False})
        user = db.session.query(User).filter_by(username=username, del_flag=0).first()
        if user is not None:
            res_data = gen_json_response(code=400, msg='用户名已存在！', extends={'success': False})
        else:
            user = User(
                username=username,
                nickname=username,
                phone=phone
            )
            user.password = generate_password_hash(password)
            login_time = get_now_time()
            user.login_time = login_time
            user.login_times = 1
            user.login_ip = get_user_ip()
            set_insert_user(user, 'system')
            # 注册默认第一个租户
            user.tenant_id = 1
            db.session.add(user)
            db.session.commit()
            db.session.flush()
            role_id_list = json.loads(user.role_id_list)
            role_objs = get_base_query(Role).filter(Role.id.in_(role_id_list))
            role_code_list = [i.role_code for i in role_objs]
            permissions = self.get_user_permissions(role_code_list=role_code_list, org_code=user.org_code, is_admin=user.username == 'admin')
            extends = {
                'roles': role_code_list,
                'permissions': permissions
            }
            token = encode_auth_token(user, extends=extends)
            res_data = gen_json_response(data={'token': token}, msg='注册成功!', extends={'success': True})
        return res_data

    def login(self, req_dict):
        '''
        登录
        '''
        username = req_dict['username']
        password = req_dict['password']
        user = db.session.query(User).filter(User.username == username, User.del_flag == 0).first()
        if user is None:
            res_data = gen_json_response(code=400, msg='用户名错误！', extends={'success': False})
            return res_data
        if user.status != 1:
            res_data = gen_json_response(code=400, msg='用户已被冻结或禁用！', extends={'success': False})
            return res_data
        pwd_valid = check_password_hash(user.password, password)
        if pwd_valid:
            login_time = get_now_time()
            user.login_time = login_time
            user.login_times = user.login_times + 1
            user.login_ip = get_user_ip().split(',')[0]
            # 默认登录租户为用户所属租户列表的第一个
            tenant_id_list = json.loads(user.tenant_id_list)
            if tenant_id_list != []:
                tenant_objs = get_base_query(Tenant, filter_tenant=False, sort_create_time=False).filter(Tenant.id.in_(tenant_id_list)).all()
                print(tenant_id_list, tenant_objs)
                if tenant_objs:
                    user.tenant_id = tenant_objs[0].id
            # 默认登录部门为用户所属部门列表的第一个
            depart_id_list = json.loads(user.depart_id_list)
            if depart_id_list != []:
                depart_objs = get_base_query(Depart, tenant_id=user.tenant_id).filter(
                    Depart.id.in_(depart_id_list)).all()
                if depart_objs:
                    user.org_code = depart_objs[0].org_code
            db.session.add(user)
            db.session.commit()
            db.session.flush()
            role_id_list = json.loads(user.role_id_list)
            role_objs = get_base_query(Role, tenant_id=user.tenant_id).filter(Role.id.in_(role_id_list))
            role_code_list = [i.role_code for i in role_objs]
            permissions = self.get_user_permissions(role_code_list=role_code_list, org_code=user.org_code,  is_admin=user.username == 'admin', tenant_id=user.tenant_id)
            extends = {
                'roles': role_code_list,
                'permissions': permissions
            }
            token = encode_auth_token(user, extends=extends)
            data = {
                "token": token,
                "userinfo": {
                    'id': user.id,
                    'tenant_id': user.tenant_id,
                    'username': user.username,
                    'nickname': user.nickname,
                    'avatar': user.avatar
                }
            }
            res_data = gen_json_response(data=data, code=200, msg='登录成功。', extends={'success': True})
        else:
            res_data = gen_json_response(code=400, msg='密码错误！', extends={'success': False})
        return res_data

    def login_by_token(self, req_dict):
        '''
        token验证登录
        :return:
        '''
        token = req_dict.get('token', '')
        try:
            info = decode_auth_token(token)
            data = {
                "token": token,
                "userinfo": info['data']
            }
            res_data = gen_json_response(data=data, code=200, msg='token验证成功。', extends={'success': True})
        except Exception as e:
            res_data = gen_json_response(code=400, msg='token验证失败！', extends={'success': False})
        return res_data

    def third_party_login(self, req_dict):
        '''
        第三方登录
        :param req_dict:
        :return:
        '''
        third_type = req_dict.get('third_type')
        third_id = req_dict.get('third_id')
        username = req_dict.get('username')
        email = req_dict.get('email')
        nickname = req_dict.get('nickname')
        
        if not all([third_type, third_id, username]):
            return gen_json_response(code=400, msg='第三方登录信息不完整', extends={'success': False})
        
        # 查找是否已存在该第三方账号的用户
        user = db.session.query(User).filter(
            User.third_type == third_type,
            User.third_id == third_id,
            User.del_flag == 0
        ).first()
        
        if user is None:
            # 创建新用户
            user = User()
            user.username = f"{third_type}_{username}"
            user.nickname = nickname or username
            user.email = email
            user.third_type = third_type
            user.third_id = third_id
            user.status = 1  # 正常状态
            user.password = generate_password_hash('third_party_user')  # 设置默认密码
            user.login_times = 0
            user.tenant_id = 1
            set_insert_user(user, 'system')
            db.session.add(user)
            db.session.commit()
            db.session.flush()
        
        # 更新登录信息
        login_time = get_now_time()
        user.login_time = login_time
        user.login_times = user.login_times + 1
        user.login_ip = ''
        
        db.session.add(user)
        db.session.commit()
        db.session.flush()
        
        # 生成token
        permissions = self.get_user_permissions(role_code_list=[], org_code=user.org_code, is_admin=user.username == 'admin', tenant_id=user.tenant_id)
        extends = {
            'roles': [],
            'permissions': permissions
        }
        token = encode_auth_token(user, extends=extends)
        return token

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        role_id = req_dict.get('role_id', '#')
        page = req_dict.get('page', 1)
        pagesize = req_dict.get('pagesize', 10)
        sort_column = req_dict.get('column', "")
        order = req_dict.get('order', "desc")
        sortInfoString = req_dict.get('sortInfoString')
        if sortInfoString:
            sortInfoString = parse_json(sortInfoString)
            sort_column = sortInfoString[-1]['column']
            order = sortInfoString[-1]['order']
        if sort_column == 'valid_end_time':
            if order.upper() == 'DESC':
                query = get_base_query(User, sort_create_time=False, sort_no=False).order_by(User.valid_end_time.desc())
            else:
                query = get_base_query(User, sort_create_time=False, sort_no=False).order_by(User.valid_end_time.asc())
        else:
            query = get_base_query(User)
        username = req_dict.get('username', '')
        if username != '':
            search_text = f"%{username}%"
            query = query.filter(User.username.like(search_text))
        nickname = req_dict.get('nickname', '')
        if nickname != '':
            search_text = f"%{nickname}%"
            query = query.filter(User.nickname.like(search_text))
        phone = req_dict.get('phone', '')
        if phone != '':
            search_text = f"%{phone}%"
            query = query.filter(User.phone.like(search_text))
        total = query.count()
        page = int(page)
        pagesize = int(pagesize)
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_user(obj)
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)

    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(User).filter(User.id == obj_id, User.delete_tag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到对应数据')
        dic = serialize_user(obj)
        return gen_json_response(dic)

    def add_obj(self, req_dict):
        '''
        添加用户并配置租户权限
        '''
        username = req_dict.get('username')
        password = req_dict.get('password')
        confirmPassword = req_dict.get('confirmPassword', '')

        if confirmPassword != password:
            return gen_json_response(code=400, msg='两次密码输入不同！', extends={'success': False})

        # 检查用户名是否已存在
        exist_obj = db.session.query(User).filter(User.username == username, User.del_flag == 0).first()
        if exist_obj:
            return gen_json_response(code=400, msg='用户名已存在！')

        # 创建用户对象
        user_obj = User()
        for k in ['username', 'nickname', 'work_no', 'user_identity', 'avatar',
                  'birthday', 'sex', 'email', 'phone', 'tenant_id']:
            if k in req_dict:
                setattr(user_obj, k, req_dict.get(k))

        # 加密密码
        password = generate_password_hash(password)
        user_obj.password = password
        set_insert_user(user_obj)
        db.session.add(user_obj)
        db.session.flush()  # 先flush获取user_id

        # 处理租户权限配置
        tenant_id_list = req_dict.get('tenant_id_list', "").split(',') if req_dict.get('tenant_id_list') else []
        if not tenant_id_list and 'tenant_id' in req_dict:
            tenant_id_list = [str(req_dict['tenant_id'])]

        for tenant_id in tenant_id_list:
            if not tenant_id.isdigit():
                continue

            tenant_id = int(tenant_id)
            # 检查租户是否存在
            tenant = db.session.query(Tenant).filter(Tenant.id == tenant_id, Tenant.del_flag == 0).first()
            if not tenant:
                continue

            # 创建或更新用户租户关联
            join_obj = db.session.query(UserTenantJoin).filter_by(
                tenant_id=tenant_id,
                user_id=user_obj.id
            ).first()

            if not join_obj:
                join_obj = UserTenantJoin(
                    tenant_id=tenant_id,
                    user_id=user_obj.id
                )

            # 设置部门列表（只包含属于该租户的部门）
            if 'depart_id_list' in req_dict:
                depart_ids = req_dict.get('depart_id_list', [])
                if isinstance(depart_ids, str):
                    try:
                        depart_ids = depart_ids.split(',')
                    except:
                        depart_ids = []
                # 过滤只属于当前租户的部门
                valid_depart_ids = db.session.query(Depart.id).filter(
                    Depart.id.in_(depart_ids),
                    Depart.tenant_id == tenant_id,
                    Depart.del_flag == 0
                ).all()
                join_obj.depart_id_list = json.dumps([str(d[0]) for d in valid_depart_ids])

            # 设置职务列表（只包含属于该租户的职务）
            if 'post_id_list' in req_dict:
                post_ids = req_dict.get('post_id_list', [])
                if isinstance(post_ids, str):
                    try:
                        post_ids = post_ids.split(',')
                    except:
                        post_ids = []
                # 过滤只属于当前租户的职务
                valid_post_ids = db.session.query(Position.id).filter(
                    Position.id.in_(post_ids),
                    Position.tenant_id == tenant_id,
                    Position.del_flag == 0
                ).all()
                join_obj.post_id_list = json.dumps([str(p[0]) for p in valid_post_ids])

            # 设置角色列表（只包含属于该租户的角色）
            if 'role_id_list' in req_dict:
                role_ids = req_dict.get('role_id_list', [])
                if isinstance(role_ids, str):
                    try:
                        role_ids = role_ids.split(',')
                    except:
                        role_ids = []
                # 过滤只属于当前租户的角色
                valid_role_ids = db.session.query(Role.id).filter(
                    Role.id.in_(role_ids),
                    Role.tenant_id == tenant_id,
                    Role.del_flag == 0
                ).all()
                join_obj.role_id_list = json.dumps([str(r[0]) for r in valid_role_ids])

            set_insert_user(join_obj)
            db.session.add(join_obj)

        db.session.commit()
        return gen_json_response(msg='添加成功。', extends={'success': True})

    def update_obj(self, req_dict):
        '''
        更新用户及租户权限配置
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(User).filter(User.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='找不到该用户！')

        # 更新用户基本信息
        for k in ['nickname', 'work_no', 'user_identity', 'avatar',
                  'birthday', 'sex', 'email', 'phone', 'tenant_id']:
            if k in req_dict:
                setattr(obj, k, req_dict.get(k))

        # 更新密码（如果有）
        if 'password' in req_dict and req_dict['password']:
            password = generate_password_hash(req_dict['password'])
            obj.password = password

        set_update_user(obj)
        db.session.add(obj)

        # 处理租户权限配置
        if 'tenant_id_list' in req_dict:
            tenant_id_list = req_dict.get('tenant_id_list', "").split(',') if req_dict.get('tenant_id_list') else []
            current_tenants = db.session.query(UserTenantJoin.tenant_id).filter(
                UserTenantJoin.user_id == obj.id
            ).all()
            current_tenant_ids = {t[0] for t in current_tenants}

            # 添加新租户
            for tenant_id in tenant_id_list:
                if not tenant_id.isdigit():
                    continue

                tenant_id = int(tenant_id)
                if tenant_id in current_tenant_ids:
                    continue

                tenant = db.session.query(Tenant).filter(Tenant.id == tenant_id, Tenant.del_flag == 0).first()
                if not tenant:
                    continue

                join_obj = UserTenantJoin(
                    tenant_id=tenant_id,
                    user_id=obj.id
                )

                # 设置部门列表（只包含属于该租户的部门）
                if 'depart_id_list' in req_dict:
                    depart_ids = req_dict.get('depart_id_list', [])
                    if isinstance(depart_ids, str):
                        try:
                            depart_ids = depart_ids.split(',')
                        except:
                            depart_ids = []
                    valid_depart_ids = db.session.query(Depart.id).filter(
                        Depart.id.in_(depart_ids),
                        Depart.tenant_id == tenant_id,
                        Depart.del_flag == 0
                    ).all()
                    join_obj.depart_id_list = json.dumps([str(d[0]) for d in valid_depart_ids])

                # 设置职务列表（只包含属于该租户的职务）
                if 'post_id_list' in req_dict:
                    post_ids = req_dict.get('post_id_list', [])
                    if isinstance(post_ids, str):
                        try:
                            post_ids = post_ids.split(',')
                        except:
                            post_ids = []
                    valid_post_ids = db.session.query(Position.id).filter(
                        Position.id.in_(post_ids),
                        Position.tenant_id == tenant_id,
                        Position.del_flag == 0
                    ).all()
                    join_obj.post_id_list = json.dumps([str(p[0]) for p in valid_post_ids])

                # 设置角色列表（只包含属于该租户的角色）
                if 'role_id_list' in req_dict:
                    role_ids = req_dict.get('role_id_list', [])
                    if isinstance(role_ids, str):
                        try:
                            role_ids = role_ids.split(',')
                        except:
                            role_ids = []
                    valid_role_ids = db.session.query(Role.id).filter(
                        Role.id.in_(role_ids),
                        Role.tenant_id == tenant_id,
                        Role.del_flag == 0
                    ).all()
                    join_obj.role_id_list = json.dumps([str(r[0]) for r in valid_role_ids])

                set_insert_user(join_obj)
                db.session.add(join_obj)

            # 移除不再关联的租户
            new_tenant_ids = {int(tid) for tid in tenant_id_list if tid.isdigit()}
            for tenant_id in current_tenant_ids:
                if tenant_id not in new_tenant_ids:
                    db.session.query(UserTenantJoin).filter(
                        UserTenantJoin.user_id == obj.id,
                        UserTenantJoin.tenant_id == tenant_id
                    ).delete()

        # 更新现有租户的权限配置
        if any(k in req_dict for k in ["post_id_list", "depart_id_list", "role_id_list"]):
            join_objs = db.session.query(UserTenantJoin).filter(
                UserTenantJoin.user_id == obj.id
            ).all()

            for join_obj in join_objs:
                # 更新部门列表（只包含属于该租户的部门）
                if 'depart_id_list' in req_dict:
                    depart_ids = req_dict.get('depart_id_list', [])
                    if isinstance(depart_ids, str):
                        try:
                            depart_ids = depart_ids.split(',')
                        except:
                            depart_ids = []
                    valid_depart_ids = db.session.query(Depart.id).filter(
                        Depart.id.in_(depart_ids),
                        Depart.tenant_id == join_obj.tenant_id,
                        Depart.del_flag == 0
                    ).all()
                    join_obj.depart_id_list = json.dumps([str(d[0]) for d in valid_depart_ids])

                # 更新职务列表（只包含属于该租户的职务）
                if 'post_id_list' in req_dict:
                    post_ids = req_dict.get('post_id_list', [])
                    if isinstance(post_ids, str):
                        try:
                            post_ids = post_ids.split(',')
                        except:
                            post_ids = []
                    valid_post_ids = db.session.query(Position.id).filter(
                        Position.id.in_(post_ids),
                        Position.tenant_id == join_obj.tenant_id,
                        Position.del_flag == 0
                    ).all()
                    join_obj.post_id_list = json.dumps([str(p[0]) for p in valid_post_ids])

                # 更新角色列表（只包含属于该租户的角色）
                if 'role_id_list' in req_dict:
                    role_ids = req_dict.get('role_id_list', [])
                    if isinstance(role_ids, str):
                        try:
                            role_ids = role_ids.split(',')
                        except:
                            role_ids = []
                    valid_role_ids = db.session.query(Role.id).filter(
                        Role.id.in_(role_ids),
                        Role.tenant_id == join_obj.tenant_id,
                        Role.del_flag == 0
                    ).all()
                    join_obj.role_id_list = json.dumps([str(r[0]) for r in valid_role_ids])

                set_update_user(join_obj)
                db.session.add(join_obj)

        db.session.commit()
        return gen_json_response(msg='更新成功。', extends={'success': True})

    def edit_self(self, req_dict, username):
        '''
        修改个人信息
        :param req_dict:
        :param username:
        :return:
        '''
        user_obj = db.session.query(User).filter_by(username=username, del_flag=0).first()
        if user_obj is None:
            return gen_json_response(code=400, msg='用户不存在！', extends={'success': False})
        for k in ['nickname', 'avatar', 'birthday', 'sex', 'email', 'phone']:
            if k in req_dict:
                setattr(user_obj, k, req_dict.get(k))
        set_update_user(user_obj)
        db.session.add(user_obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='更新成功。', extends={'success': True})

    def delete_obj(self, req_dict):
        '''
        删除
        '''
        if 'id' in req_dict:
            del_ids = [req_dict['id']]
        elif 'ids' in req_dict:
            del_ids = req_dict['ids']
        else:
            del_ids = req_dict
        del_objs = db.session.query(User).filter(User.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(msg='删除成功。', extends={'success': True})
