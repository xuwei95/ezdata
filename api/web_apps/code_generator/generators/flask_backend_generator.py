from web_apps.code_generator.generators.templates.flask_backend import model_codes, services_codes, views_codes


class FlaskCodeGen(object):
    def __init__(self, params):
        self.params = params

    def gen_model_code(self):
        '''
        生成数据模型层代码
        :return:
        '''
        module_name = self.params.get('module_name')
        model_code = model_codes.gen_model_code(self.params)
        res_data = {
            'type': 'file',
            'title': 'db_models.py',
            'key': 'db_models.py',
            'language': 'python',
            'path': f'flask/{module_name}/db_models.py',
            'content': model_code
        }
        return res_data

    def gen_views_code(self):
        '''
        生成视图路由层代码
        :return:
        '''
        module_name = self.params.get('module_name')
        views_code = views_codes.gen_views_code(self.params)
        res_data = {
            'type': 'file',
            'title': 'views.py',
            'key': 'views.py',
            'language': 'python',
            'path': f'flask/{module_name}/views.py',
            'content': views_code
        }
        return res_data

    def gen_services_code(self):
        '''
        生成服务逻辑层代码
        :return:
        '''
        module_name = self.params.get('module_name')
        services_code = services_codes.gen_services_code(self.params)
        res_data = {
            'type': 'dir',
            'title': 'services',
            'key': 'services',
            'children': [
                {
                    'type': 'file',
                    'title': f'{module_name}_api_services.py',
                    'key': f'{module_name}_api_services.py',
                    'language': 'python',
                    'path': f'flask/{module_name}/services/{module_name}_api_services.py',
                    'content': services_code
                }
            ]
        }
        return res_data

    def generate_all_codes(self):
        '''
        组合生成模块整体代码
        :return:
        '''
        module_name = self.params.get('module_name')
        model_res = self.gen_model_code()
        views_res = self.gen_views_code()
        services_res = self.gen_services_code()
        res_data = {
            'type': 'dir',
            'title': 'flask',
            'key': 'flask',
            'children': [
                {
                    'type': 'dir',
                    'title': module_name,
                    'key': f"flask/{module_name}",
                    'children': [
                        model_res,
                        views_res,
                        services_res
                    ]
                }
            ]
        }
        return res_data


if __name__ == '__main__':
    import json
    from web_apps.code_generator.db_models import CodeGenModel, db
    obj = db.session.query(CodeGenModel).filter(CodeGenModel.id == '5deb88593c024033ae6de2f9ed5e7806').first()
    params = obj.to_dict()
    params['fields'] = json.loads(params['fields'])
    params['query_params'] = json.loads(params['query_params'])
    params['buttons'] = json.loads(params['buttons'])
    print(params)
    code_gen = FlaskCodeGen(params)
    res = code_gen.generate_all_codes()
    print(res)
