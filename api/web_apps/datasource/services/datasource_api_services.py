'''
数据源管理api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid
from web_apps.datasource.db_models import DataSource
from web_apps.datamodel.db_models import DataModel
from utils.web_utils import validate_params
import pandas as pd
import io
from utils.etl_utils import get_reader_model
from tasks.data_tasks import self_gen_datasource_model
from etl2.registry import get_registry


def serialize_datasource_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'name', 'type', 'conn_conf', 'status', 'ext_params', 'description', 'create_by', 'create_time', 'update_by', 'update_time', 'sort_no', 'del_flag']:
            if k in ['conn_conf', 'ext_params']:
                # 安全地解析JSON，如果解析失败则返回空字典
                try:
                    if dic.get(k) and isinstance(dic[k], str):
                        res[k] = json.loads(dic[k])
                    elif dic.get(k) and isinstance(dic[k], dict):
                        res[k] = dic[k]
                    else:
                        res[k] = {}
                except (json.JSONDecodeError, TypeError):
                    res[k] = {}
            else:
                res[k] = dic.get(k)
        return res
    elif ser_type == 'detail':
        for k in ['conn_conf']:
            try:
                if dic.get(k) and isinstance(dic[k], str):
                    dic[k] = json.loads(dic[k])
                elif not dic.get(k) or not isinstance(dic[k], dict):
                    dic[k] = {}
            except (json.JSONDecodeError, TypeError):
                dic[k] = {}
        for k in []:
            dic.pop(k)
    elif ser_type == 'all_list':
        res = {}
        for k in ['id', 'name', 'type']:
            if k in ['conn_conf', 'ext_params']:
                try:
                    if dic.get(k) and isinstance(dic[k], str):
                        res[k] = json.loads(dic[k])
                    elif dic.get(k) and isinstance(dic[k], dict):
                        res[k] = dic[k]
                    else:
                        res[k] = {}
                except (json.JSONDecodeError, TypeError):
                    res[k] = {}
            else:
                res[k] = dic.get(k)
        return res
        
    return dic

    
class DataSourceApiService(object):
    def __init__(self):
        pass
        
    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(DataSource)
        # 数据源名称 查询逻辑
        name = req_dict.get('name', '')
        if name != '':
            query = query.filter(DataSource.name.like("%" + name + "%"))
        # 数据源类型 查询逻辑
        type = req_dict.get('type', '')
        if type != '':
            query = query.filter(DataSource.type.like("%" + type + "%"))
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_datasource_model(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)
    
    def get_obj_all_list(self, req_dict):
        '''
        获取全量列表
        '''
        query = get_base_query(DataSource)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_datasource_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(DataSource).filter(
            DataSource.id == obj_id,
            DataSource.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_datasource_model(obj, ser_type='detail')
        return gen_json_response(data=dic)
    
    def add_obj(self, req_dict):
        '''
        添加
        '''
        # 名称 判重逻辑
        name = req_dict.get('name', '')
        if name != '':
            exist_obj = db.session.query(DataSource).filter(
                DataSource.name == name,
                DataSource.del_flag == 0).first()
            if exist_obj:
                return gen_json_response(code=400, msg='字段"名称"已存在')
        obj = DataSource()
        for key in req_dict:
            if key in ['conn_conf']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'ext_params':
                try:
                    json_value = json.loads(req_dict[key])
                    obj.ext_params = json.dumps(json_value, ensure_ascii=False, indent=2)
                except Exception as e:
                    return gen_json_response(code=400, msg='额外参数必须是json格式')
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        # 如果开启了自动建模，针对数据源自动创建模型
        auto_gen = req_dict.get('auto_gen', '0')
        if str(auto_gen) == '1':
            # self_gen_datasource_model(obj.id)
            self_gen_datasource_model.apply_async(args=(obj.id,))
        return gen_json_response(msg='添加成功', extends={'success': True})
    
    def edit_obj(self, req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        # 判重逻辑
        exist_query = db.session.query(DataSource).filter(DataSource.id != obj_id, DataSource.del_flag == 0)
        name = req_dict.get('name', '')
        if name != '':
            exist_query = exist_query.filter(DataSource.name == name)
        exist_obj = exist_query.first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在')
        obj = db.session.query(DataSource).filter(DataSource.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key in ['conn_conf']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'ext_params':
                try:
                    json_value = json.loads(req_dict[key])
                    obj.ext_params = json.dumps(json_value, ensure_ascii=False, indent=2)
                except Exception as e:
                    return gen_json_response(code=400, msg='额外参数必须是json格式')
            else:
                setattr(obj, key, req_dict[key])
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='编辑成功', extends={'success': True})
    
    def delete_obj(self, req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        # 判断是否存在关联数据模型，若有，不允许删除
        exist_model_objs = db.session.query(DataModel).filter(DataModel.datasource_id == obj_id,
                                                              DataModel.del_flag == 0).all()
        if exist_model_objs != []:
            return gen_json_response(code=400, msg='数据源存在关联数据模型，无法删除')
        del_obj = db.session.query(DataSource).filter(DataSource.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        del_obj.del_flag = 1
        set_update_user(del_obj)
        db.session.add(del_obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    def delete_batch(self, req_dict):
        '''
        批量删除
        '''
        del_ids = req_dict.get('ids')
        if isinstance(del_ids, str):
            del_ids = del_ids.split(',')
        # 判断是否存在关联数据模型，若有，不允许删除
        exist_model_objs = db.session.query(DataModel).filter(DataModel.datasource_id.in_(del_ids),
                                                              DataModel.del_flag == 0).all()
        if exist_model_objs != []:
            return gen_json_response(code=400, msg='数据源存在关联数据模型，无法删除')
        del_objs = db.session.query(DataSource).filter(DataSource.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    def importExcel(self, file):
        '''
        excel导入
        '''
        try:
            df = pd.read_excel(file, dtype=object)
            df.fillna("", inplace=True)
            # 校验上传字段
            data_li = []
            n = 2
            for k, row in df.iterrows():
                row = row.to_dict()
                verify_dict = {
                    "name": {
                        "name": "名称",
                        "required": True
                    },
                    "type": {
                        "name": "类型",
                        "required": True
                    },
                    "conn_conf": {
                        "name": "连接配置",
                        "required": True
                    }
                }
                not_valid = validate_params(row, verify_dict)
                if not_valid:
                    not_valid = {
                        'code': 400,
                        'msg': f'第{n}行{not_valid}'
                    }
                    return not_valid
                data_li.append(row)
                n += 1
            # 名称 判重逻辑
            name_list = [row.get('name', '') for row in data_li]
            print(name_list)
            if name_list != []:
                exist_obj = db.session.query(DataSource).filter(
                    DataSource.name.in_(name_list),
                    DataSource.del_flag == 0).first()
                if exist_obj:
                    return gen_json_response(code=400, msg='字段"名称"已存在')
            # 循环导入
            for row in data_li:
                obj = DataSource()
                for key in row:
                    if key in ['conn_conf', 'ext_params']:
                        setattr(obj, key, json.dumps(row[key], ensure_ascii=False, indent=2))
                    else:
                        setattr(obj, key, row[key])
                obj.id = gen_uuid(res_type='base')
                set_insert_user(obj)
                db.session.add(obj)
                db.session.commit()
                db.session.flush()
            return gen_json_response(code=200, msg='导入成功', extends={'success': True})
        except Exception as e:
            return gen_json_response(code=500, msg=f'导入错误{e}')

    def exportXls(self, req_dict):
        '''
        导出excel
        '''
        selections = req_dict.get('selections', '')
        ids = selections.split(',')
        obj_list = db.session.query(DataSource).filter(DataSource.id.in_(ids)).all()
        result = []
        for obj in obj_list:
            dic = serialize_datasource_model(obj, ser_type='list')
            result.append(dic)
        df = pd.DataFrame(result)
        print(df)
        # 使用字节流存储
        output = io.BytesIO()
        # 保存文件
        df.to_excel(output, index=False)
        # 文件seek位置，从头(0)开始
        output.seek(0)
        return output

    def connTest(self, req_dict):
        '''
        连接测试
        '''
        conn_type = req_dict.get('type')
        conn_conf = req_dict.get('conn_conf')
        model_info = {
            'source': {
                "name": "",
                "type": conn_type,
                "conn_conf": conn_conf,
                "ext_params": {}
            },
            'model': {},
            'extract_info': {
                'batch_size': 1,
                'extract_rules': []
            }
        }
        flag, reader = get_reader_model(model_info)
        if flag:
            flag, res = reader.connect()
            if flag:
                return gen_json_response(msg=res)
            else:
                return gen_json_response(code=400, msg=f'连接失败:{res}')
        else:
            return gen_json_response(code=400, msg=f'连接失败:{reader}')

    def syncModels(self, req_dict):
        '''
        自动建模
        '''
        datasource_id = req_dict.get('datasource_id')
        self_gen_datasource_model.apply_async(args=(datasource_id,))
        return gen_json_response(msg='同步成功', extends={'success': True})

    def get_datasource_types(self, req_dict):
        '''
        获取所有数据源类型
        '''
        try:

            registry = get_registry()
            available_sources = registry.list_available_sources()

            # 构建数据源类型列表
            datasource_types = []

            # 添加自定义数据源类型
            for source_type in available_sources['custom']:
                datasource_types.append({'label': source_type, 'value': source_type})

            # 添加MindsDB支持的数据源类型

            for source_type in available_sources['mindsdb_data']:
                source_type = source_type.replace('_handler', '')
                datasource_types.append({'label': source_type, 'value': source_type})

            # 排序并去重
            unique_types = {}
            for item in datasource_types:
                unique_types[item['value']] = item

            result = sorted(unique_types.values(), key=lambda x: x['label'])

            return gen_json_response(data=result)

        except Exception as e:
            return gen_json_response(code=400, msg=f"无法从etl2获取数据源类型: {e}")

    def get_datasource_config(self, req_dict):
        '''
        根据数据源类型获取连接配置表单
        '''
        datasource_type = req_dict.get('type')

        try:
            registry = get_registry()

            # 尝试从etl2 registry获取handler信息
            handler_info = registry.get_handler_info(datasource_type)
            if 'error' in handler_info:
                return gen_json_response(code=400, msg=f'不支持的数据源类型: {datasource_type}')

            # 根据handler的connection_args生成表单配置
            connection_args = handler_info.get('connection_args', {})
            connection_args_example = handler_info.get('connection_args_example', {})
            config = []

            # 使用connection_args生成表单，因为包含了实际的字段名
            if connection_args:
                for field_name, _value in connection_args.items():
                    field_info = connection_args.get(field_name, {})

                    # 根据字段类型和名称确定组件类型
                    component_type = self._determine_component_type(field_name, _value, field_info)

                    field_config = {
                        'label': self._generate_field_label(field_name, field_info),
                        'field': field_name,
                        'required': field_info.get('required', False),
                        'component': component_type
                    }
                    if 'description' in field_info:
                        field_config['description'] = field_info['description']
                    if 'placeholder' in field_info:
                        field_config['placeholder'] = field_info['placeholder']
                    if 'default' in field_info:
                        field_config['default'] = field_info['default']
                    example_value = connection_args_example.get(field_name)
                    # 设置默认值
                    if example_value is not None:
                        field_config['default'] = example_value

                    # 设置组件属性
                    if component_type == 'Number':
                        field_config['componentProps'] = {'min': 0}
                    elif component_type == 'Select':
                        field_config['componentProps'] = {'options': []}

                    config.append(field_config)

            # 如果没有生成任何字段，使用通用配置
            if not config:
                config = [
                    {'label': '连接配置', 'field': 'connection_config', 'required': True, 'component': 'JSONEditor', 'default': '{}'}
                ]

            return gen_json_response(data=config)

        except Exception as e:
            return gen_json_response(code=400, msg=f"无法获取数据源配置，使用默认配置: {e}")

    def _determine_component_type(self, field_name, example_value, field_info):
        """根据字段名和值确定组件类型"""
        field_name_lower = field_name.lower()

        # 优先使用connection_args中的type信息
        field_type = field_info.get('type')
        if field_type:
            # 根据MindsDB handler中的type字段确定组件类型
            field_type_lower = field_type.lower()
            if field_type_lower == 'pwd' or field_type_lower == 'password':
                # 密码类型，使用密码输入框
                return 'Password'
            elif field_type_lower == 'path':
                # 路径类型，使用普通输入框
                return 'Input'
            elif field_type_lower in ['string', 'str']:
                # 检查是否是特殊类型的字符串字段
                if 'password' in field_name_lower or 'secret' in field_name_lower or field_info.get('secret', False):
                    return 'Password'
                elif 'url' in field_name_lower or 'uri' in field_name_lower:
                    return 'Input'
                else:
                    return 'Input'
            elif field_type_lower in ['integer', 'int', 'number', 'float']:
                return 'Number'
            elif field_type_lower in ['boolean', 'bool']:
                return 'RadioGroup'
            elif field_type_lower in ['array', 'list', 'dict', 'object', 'json']:
                return 'JSONEditor'

        # 回退到基于字段名和值类型的判断
        if 'password' in field_name_lower or 'secret' in field_name_lower or field_info.get('secret', False):
            return 'Password'
        elif 'port' in field_name_lower:
            return 'Number'
        elif 'url' in field_name_lower or 'uri' in field_name_lower:
            return 'Input'
        elif isinstance(example_value, int):
            return 'Number'
        elif isinstance(example_value, float):
            return 'Number'
        elif isinstance(example_value, bool):
            return 'RadioGroup'
        elif isinstance(example_value, dict) or isinstance(example_value, list):
            return 'JSONEditor'
        else:
            return 'Input'

    def _generate_field_label(self, field_name, field_info):
        """生成字段标签"""
        # 优先使用MindsDB handler中的label信息
        if field_info.get('label'):
            # 将英文标签转换为中文（如果已知映射存在）
            english_label = field_info['label']
            label_mapping = {
                'User': '用户名',
                'Password': '密码',
                'Host': '服务器',
                'Port': '端口',
                'Database': '数据库',
                'Schema': '模式',
                'URI': '连接URI',
                'URL': '连接地址'
            }
            return label_mapping.get(english_label, english_label)

        # 回退到title信息
        if field_info.get('title'):
            return field_info['title']

        # 根据字段名生成友好标签
        field_name_mapping = {
            'host': '服务器',
            'port': '端口',
            'user': '用户名',
            'username': '用户名',
            'password': '密码',
            'database': '数据库',
            'database_name': '数据库名',
            'schema': '模式',
            'api_key': 'API密钥',
            'access_key': '访问密钥',
            'secret_key': '密钥',
            'region': '区域',
            'bucket': 'Bucket',
            'path': '路径',
            'endpoint': '端点',
            'hosts': '服务器地址',
            'cloud_id': 'Cloud ID',
            'sslmode': 'SSL模式'
        }

        return field_name_mapping.get(field_name, field_name.title())

