from web_apps.code_generator.generators.templates.vue3_antd import api_codes, data_codes, index_vue_codes, modal_codes


class Vue3AntdCodeGen(object):
    def __init__(self, params):
        self.params = params

    def gen_data_code(self):
        '''
        生成数据代码
        :return:
        '''
        module_name = self.params.get('module_name')
        data_code = data_codes.gen_data_code(self.params)
        res_data = {
            'type': 'file',
            'title': f'{module_name}.data.ts',
            'key': f'{module_name}.data.ts',
            'language': 'typescript',
            'path': f'vue3_antd/{module_name}/{module_name}.data.ts',
            'content': data_code
        }
        return res_data

    def gen_api_code(self):
        '''
        生成api代码
        :return:
        '''
        module_name = self.params.get('module_name')
        api_code = api_codes.gen_api_code(self.params)
        res_data = {
            'type': 'file',
            'title': f'{module_name}.api.ts',
            'key': f'{module_name}.api.ts',
            'language': 'typescript',
            'path': f'vue3_antd/{module_name}/{module_name}.api.ts',
            'content': api_code
        }
        return res_data

    def gen_modal_code(self):
        '''
        生成编辑弹窗代码
        :return:
        '''
        modal_type_map = {1: 'Modal', 2: 'Drawer'}
        module_name = self.params.get('module_name')
        modal_type = self.params.get('modal_type', 1)
        modal_type = modal_type_map.get(modal_type)
        modal_code = modal_codes.gen_modal_code(self.params)
        model_value = self.params.get('model_value')
        res_data = {
            'type': 'dir',
            'title': 'components',
            'key': 'components',
            'children': [
                {
                    'type': 'file',
                    'title': f'{model_value}{modal_type}.vue',
                    'key': f'{model_value}{modal_type}.vue',
                    'language': 'vue',
                    'path': f'vue3_antd/{module_name}/components/{model_value}{modal_type}.vue',
                    'content': modal_code
                }
            ]
        }
        return res_data

    def gen_index_vue_code(self):
        '''
        生成主页面代码
        :return:
        '''
        module_name = self.params.get('module_name')
        index_vue_code = index_vue_codes.gen_index_vue_code(self.params)
        res_data = {
            'type': 'file',
            'title': f'index.vue',
            'key': f'index.vue',
            'language': 'vue',
            'path': f'vue3_antd/{module_name}/index.vue',
            'content': index_vue_code
        }
        return res_data

    def generate_all_codes(self):
        '''
        组合生成模块整体代码
        :return:
        '''
        module_name = self.params.get('module_name')
        data_res = self.gen_data_code()
        api_res = self.gen_api_code()
        modal_res = self.gen_modal_code()
        index_vue_res = self.gen_index_vue_code()
        res_data = {
            'type': 'dir',
            'title': 'vue3_antd',
            'key': 'vue3_antd',
            'children': [
                {
                    'type': 'dir',
                    'title': f'{module_name}',
                    'key': f'vue3_antd/{module_name}',
                    'children': [
                        modal_res,
                        data_res,
                        api_res,
                        index_vue_res
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
    code_gen = Vue3AntdCodeGen(params)
    res = code_gen.generate_all_codes()
    print(res)
