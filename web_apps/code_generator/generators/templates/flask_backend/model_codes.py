import json


def gen_fields_code(params):
    '''
    字段列表代码
    :param params:
    :return:
    '''
    base_code = """
    """
    fields = params.get('fields')
    for field in fields:
        print(field)
    res_code = base_code
    return res_code


def gen_default_code(col, gen_type='text'):
    '''
    获取默认值代码
    '''
    default_value = col.get('default_value')
    if default_value == [[], '[]']:
        return ", default='[]'" if gen_type == 'text' else []
    if default_value in [{}, '{}']:
        return ", default='{}'" if gen_type == 'text' else {}
    elif default_value in [None, '']:
        return ", default=''"
    elif default_value == 'server_default:CURRENT_TIMESTAMP':
        return ", server_default=db.text('CURRENT_TIMESTAMP')"
    elif default_value == 'server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP':
        return ", server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')"
    else:
        if gen_type == 'text':
            return f", default='{default_value}'"
        else:
            return f", default={default_value}"


def gen_model_code(params):
    '''
    生成数据模型代码
    :param params:
    :return:
    '''
    template_code = """
'''
${title}数据模型
'''
from web_apps import db
${import_model_code}


class ${model_value}(${extend_model}):
    '''
    ${module_name}表
    '''
    __tablename__ = '${table_name}'
    ${fields_code}
    ${other_model_code}

if __name__ == '__main__':
    db.create_all()
    db.session.flush()
    """
    fields = params['fields']
    extend_base_model = params.get('extend_base_model')
    if extend_base_model == 1:
        extend_model = 'BaseModel'
        import_model_code = 'from models import BaseModel'
        other_model_code = ''
        # 继承基础模型，系统字段不需生成
        sys_fields = ['description', 'sort_no', 'del_flag', 'create_by', 'create_time', 'update_by', 'update_time']
        fields = [i for i in fields if i['field'] not in sys_fields]
    else:
        extend_model = 'db.Model'
        import_model_code = 'import datetime'
        other_model_code = """  
    def to_dict(self, data_type='str'):
        '''
        转为字典
        :return:
        '''
        value = {}
        for column in self.__table__.columns:
            attribute = getattr(self, column.name)
            if isinstance(attribute, datetime.datetime) and data_type == 'str':
                attribute = str(attribute)
            value[column.name] = attribute
        return value
        """
    template_code = template_code.replace('${extend_model}', extend_model)
    template_code = template_code.replace('${import_model_code}', import_model_code)
    template_code = template_code.replace('${other_model_code}', other_model_code)
    field_arr = []
    for field in fields:
        c_type = field['field_type']
        if c_type == 'String':
            c_code = f"db.String({field['length']})"
        else:
            c_code = f"db.{c_type}"
        default_code = gen_default_code(field, gen_type='text' if c_type in ['Text', 'String'] else '')
        if field['primary_key'] == 1:
            primary_code = f", primary_key=True"
            field['nullable'] = 0
        else:
            primary_code = ''
        column_code = f"{field['field']} = db.Column({c_code}{primary_code}, nullable={field['nullable'] == 1}{default_code}, comment='{field['label']}')"
        field_arr.append(column_code)
    fields_code = '\n    '.join(i for i in field_arr)
    template_code = template_code.replace('${fields_code}', fields_code)
    for k in ['title', 'module_name', 'model_value', 'table_name']:
        v = params.get(k)
        print(k, v)
        template_code = template_code.replace('${%s}' % k, v)
    template_code = template_code.strip() + '\n'
    print(template_code)
    return template_code


if __name__ == '__main__':
    from web_apps.code_generator.db_models import CodeGenModel, db
    obj = db.session.query(CodeGenModel).filter(CodeGenModel.id == '5deb88593c024033ae6de2f9ed5e7806').first()
    params = obj.to_dict()
    params['fields'] = json.loads(params['fields'])
    params['query_params'] = json.loads(params['query_params'])
    params['buttons'] = json.loads(params['buttons'])
    params['extend_base_model'] = 0
    print(params)
    model_code = gen_model_code(params)
    print(model_code)
    f = open('out/db_models.py', 'w')
    f.write(model_code)
