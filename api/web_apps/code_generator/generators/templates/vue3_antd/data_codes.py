import json
from utils.common_utils import get_json_value


def gen_columns_code(params):
    '''
    生成表格列字段
    :param params:
    :return:
    '''
    fields = params.get('fields', [])
    list_fields = [i for i in fields if i['table_show'] == 1]
    base_code_list = []
    for field in list_fields:
        if field.get('customRender') == 1:
            customRenderCode = """
    customRender: ({ text }) => {
      return text;
    },"""
        else:
            customRenderCode = ""
        code = """
  {
    title: '%s',
    align: 'center',
    dataIndex: '%s',%s
  },""" % (field['label'], field['field'], customRenderCode)
        base_code_list.append(code)
    res_code = ''.join(base_code_list)
    return res_code


def gen_query_params_code(params):
    '''
    生成查询字段数据
    :param params:
    :return:
    '''
    query_params = params.get('query_params', [])
    base_code_list = []
    for field in query_params:
        if field.get('componentProps') != '{}':
            try:
                props = json.loads(field.get('componentProps'))
                componentProps = """
    componentProps: {
"""
                for k in props:
                    value = get_json_value(props[k])
                    componentProps += f"      {k}: {value},\n"
                componentProps += "    },"
            except Exception as e:
                componentProps = ""
        else:
            componentProps = ""
        if field.get('colProps') != '{}':
            props = json.loads(field.get('colProps'))
            colProps = """
    colProps: {
"""
            for k in props:
                value = get_json_value(props[k])
                colProps += f"      {k}: {value},\n"
            colProps += "    },"
        else:
            colProps = ""
        code = """
  {
    label: '%s',
    field: '%s',
    component: '%s',%s%s
  },""" % (field['label'], field['field'], field['component'], componentProps, colProps)
        base_code_list.append(code)
    res_code = ''.join(base_code_list)
    return res_code


def gen_form_code(params):
    '''
    生成编辑表单字段数据
    :param params:
    :return:
    '''
    fields = params.get('fields', [])
    list_fields = [i for i in fields if i['edit_show'] == 1 and i['field'] != 'id']
    base_code_list = []
    for field in list_fields:
        required = 'true' if field['nullable'] == 0 else 'false'
        if field.get('componentProps') != '{}':
            try:
                props = json.loads(field.get('componentProps'))
                componentProps = """
    componentProps: {
"""
                for k in props:
                    value = get_json_value(props[k])
                    componentProps += f"      {k}: {value},\n"
                componentProps += "    },"
            except Exception as e:
                componentProps = ""
        else:
            componentProps = ""
        code = """
  {
    label: '%s',
    field: '%s',
    required: %s,
    component: '%s',%s
  },""" % (field['label'], field['field'], required, field['component'], componentProps)
        base_code_list.append(code)
    res_code = ''.join(base_code_list).strip()
    return res_code


def gen_data_code(params):
    '''
    生成数据代码
    :param params:
    :return:
    '''
    base_code = """
import { BasicColumn, FormSchema } from '/@/components/Table';
import { render } from "/@/utils/common/renderUtils";
import { rules } from '/@/utils/helper/validator';
//列表数据
export const columns: BasicColumn[] = [
  ${columns_code}
];
//查询数据
export const searchFormSchema: FormSchema[] = [
  ${query_params_code}
];
//表单数据
export const formSchema: FormSchema[] = [
  ${form_code}
  // TODO 主键隐藏字段，目前写死为ID
  {
    label: '',
    field: 'id',
    component: 'Input',
    show: false,
  },
];

/**
 * 流程表单调用这个方法获取formSchema
 * @param param
 */
export function getBpmFormSchema(_formData): FormSchema[] {
  // 默认和原始表单保持一致 如果流程中配置了权限数据，这里需要单独处理formSchema
  return formSchema;
}
    """
    columns_code = gen_columns_code(params)
    query_params_code = gen_query_params_code(params)
    form_code = gen_form_code(params)
    res_code = base_code.replace('${columns_code}', columns_code.strip())
    res_code = res_code.replace('${query_params_code}', query_params_code.strip())
    res_code = res_code.replace('${form_code}', form_code).strip() + '\n'
    return res_code


if __name__ == '__main__':
    from web_apps.code_generator.db_models import CodeGenModel, db
    obj = db.session.query(CodeGenModel).filter(CodeGenModel.id == '5deb88593c024033ae6de2f9ed5e7806').first()
    params = obj.to_dict()
    params['fields'] = json.loads(params['fields'])
    params['query_params'] = json.loads(params['query_params'])
    params['buttons'] = json.loads(params['buttons'])
    print(params)
    data_code = gen_data_code(params)
    print(data_code)
    f = open('out/data.ts', 'w')
    f.write(data_code)
