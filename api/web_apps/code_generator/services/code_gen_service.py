import json
import os.path
import zipfile
import io
from web_apps.code_generator.db_models import CodeGenModel, db
from web_apps.code_generator.generators.flask_backend_generator import FlaskCodeGen
from web_apps.code_generator.generators.vue3_antd_generator import Vue3AntdCodeGen


def export_codes_zip(file_list):
    '''
    导出代码zip包
    '''
    f = io.BytesIO()
    with zipfile.ZipFile(f, 'w', zipfile.ZIP_DEFLATED, False) as zf:
        for dic in file_list:
            zf.writestr(dic['path'], dic['content'])
    f.seek(0)
    return f


def gen_codes_file_list(data_li):
    '''
    生成文件列表
    :param data_li:
    :return:
    '''
    file_list = [i for i in data_li if i['type'] == 'file']
    for data_dic in data_li:
        if 'children' in data_dic:
            file_list.extend(gen_codes_file_list(data_dic['children']))
    return file_list


def export_single_file(dic):
    '''
    导出单个文件
    '''
    f = io.BytesIO()
    f.write(dic['content'].encode('utf-8'))
    f.seek(0)
    return f


class CodeGenerator(object):
    def __init__(self, params):
        '''
        代码生成器
        '''
        self.params = params
        print(self.params)
        self.backend_gen_type = params.get('backend_gen_type')
        self.frontend_gen_type = params.get('frontend_gen_type')
        if self.backend_gen_type == 1:
            self.backend_generator = FlaskCodeGen(params)
        else:
            self.backend_generator = None
        if self.frontend_gen_type == 1:
            self.frontend_generator = Vue3AntdCodeGen(params)
        else:
            self.frontend_generator = None

    def generate_all_codes(self):
        '''
        生成所有代码
        :return:
        '''
        backend_res = self.backend_generator.generate_all_codes()
        print(backend_res)
        frontend_res = self.frontend_generator.generate_all_codes()
        print(frontend_res)
        res_data = [backend_res, frontend_res]
        return res_data


if __name__ == '__main__':
    obj = db.session.query(CodeGenModel).filter(CodeGenModel.id == '5deb88593c024033ae6de2f9ed5e7806').first()
    print(obj)
    params = obj.to_dict()
    params['fields'] = json.loads(params['fields'])
    params['query_params'] = json.loads(params['query_params'])
    params['buttons'] = json.loads(params['buttons'])
    code_gen = CodeGenerator(params)
    print(code_gen)
    res_dic = code_gen.generate_all_codes()
    print(res_dic)
    file_list = gen_codes_file_list(res_dic)
    print(file_list)
    z = export_codes_zip(file_list)
    print(z)
    f = open('test.zip', 'wb')
    f.write(z.read())

