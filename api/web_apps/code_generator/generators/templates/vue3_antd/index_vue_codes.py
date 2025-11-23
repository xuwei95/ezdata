import json
from utils.common_utils import get_json_value


def gen_columns_code(params):
    '''
    生成表格列字段
    :param params:
    :return:
    '''
    fields = params.get('fields', [])
    list_fields = [i for i in fields if i['list_show'] == 1]
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


def gen_index_vue_code(params):
    '''
    生成主文件代码
    :param params:
    :return:
    '''
    base_code = """
<template>
  <div>
    <!--引用表格-->
    <BasicTable @register="registerTable" :rowSelection="rowSelection">
      <!--插槽:table标题-->
      <template #tableTitle>
        <a-button type="primary" @click="handleAdd" preIcon="ant-design:plus-outlined"> 新增</a-button>
        ${tableTitleButtonCode}
        <a-dropdown v-if="selectedRowKeys.length > 0">
          <template #overlay>
            <a-menu>
              <a-menu-item key="1" @click="batchHandleDelete">
                <Icon icon="ant-design:delete-outlined" />
                删除
              </a-menu-item>${overlayButtonCode}
            </a-menu>
          </template>
          <a-button>
            批量操作
            <Icon icon="mdi:chevron-down" />
          </a-button>
        </a-dropdown>
      </template>
      <!--操作栏-->
      <template #action="{ record }">
        <TableAction :actions="getTableAction(record)"${hasactionDropDownButtonsCode} />
      </template>
      <!--字段回显插槽-->
      <template #htmlSlot="{ text }">
        <div v-html="text"></div>
      </template>
    </BasicTable>
    <!-- 表单区域 -->
    <${model_value}${modal_type} @register="register${modal_type}" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" name="${module_name}-${model_value}" setup>
  import { ref, computed, unref } from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { use${modal_type} } from '/@/components/${modal_type}';
  import { useListPage } from '/@/hooks/system/useListPage';
  import ${model_value}${modal_type} from './components/${model_value}${modal_type}.vue';
  import { columns, searchFormSchema } from './${module_name}.data';
  import { list, deleteOne, batchDelete${other_api_funcs_code} } from './${module_name}.api';
  const checkedKeys = ref<Array<string | number>>([]);
  //注册${modal_type}
  const [register${modal_type}, { open${modal_type} }] = use${modal_type}();
  //注册table数据
  const { prefixCls, tableContext${other_api_code_funcs} } = useListPage({
    tableProps: {
      title: '${title}',
      api: list,
      columns,
      canResize: false,
      formConfig: {
        //labelWidth: 120,
        schemas: searchFormSchema,
        autoSubmitOnEnter: true,
        showAdvancedButton: true,
        fieldMapToNumber: [],
        fieldMapToTime: [],
      },
      actionColumn: {
        width: 200,
        fixed: 'right',
      },
    },
    ${ImportAndExportConfCode}
  });

  const [registerTable, { reload }, { rowSelection, selectedRowKeys }] = tableContext;

  /**
   * 新增事件
   */
  function handleAdd() {
    open${modal_type}(true, {
      isUpdate: false,
      showFooter: true,
    });
  }
  /**
   * 编辑事件
   */
  function handleEdit(record: Recordable) {
    open${modal_type}(true, {
      record,
      isUpdate: true,
      showFooter: true,
    });
  }
  /**
   * 详情
   */
  function handleDetail(record: Recordable) {
    open${modal_type}(true, {
      record,
      isUpdate: true,
      showFooter: false,
    });
  }
  /**
   * 删除事件
   */
  async function handleDelete(record) {
    await deleteOne({ id: record.id }, handleSuccess);
  }
  /**
   * 批量删除事件
   */
  async function batchHandleDelete() {
    await batchDelete({ ids: selectedRowKeys.value }, handleSuccess);
  }
  /**
   * 成功回调
   */
  function handleSuccess() {
    (selectedRowKeys.value = []) && reload();
  }
  /**
   * 操作栏
   */
  function getTableAction(record) {
    return [
      ${actionButtonsCode}
    ];
  }
  ${actionDropDownButtonsCode}
</script>

<style scoped></style>

    """
    title = params.get('title')
    buttons = params.get('buttons', [])
    has_dropdown = [i for i in buttons if i['slot'] == 'actionDropDown'] != []
    if has_dropdown:
        hasactionDropDownButtonsCode = ' :dropDownActions="getDropDownAction(record)"'
        actionDropDownButtonsCode = """
  /**
   * 下拉操作栏
   */
  function getDropDownAction(record) {
    return [
      ${actionDropDownButtonsCode}
    ];
  }""".strip()
        res_code = base_code.replace('${hasactionDropDownButtonsCode}', hasactionDropDownButtonsCode)
        res_code = res_code.replace('${actionDropDownButtonsCode}', actionDropDownButtonsCode)
    else:
        hasactionDropDownButtonsCode = ''
        res_code = base_code.replace('${hasactionDropDownButtonsCode}', hasactionDropDownButtonsCode)
    tableTitleButtonCode = ''
    overlayButtonCode = ''
    actionButtonsCode = ''
    actionDropDownButtonsCode = ''
    other_api_funcs_code = ''
    other_api_code_funcs = ''
    ImportAndExportConfCode = ''
    for button in buttons:
        if button['function'] == 'handleDelete':
            c = """
      {
        label: '删除',
        popConfirm: {
          title: '确定删除吗?',
          confirm: handleDelete.bind(null, record),
        },
      },""".strip()
            # 删除按钮
            if button['slot'] == 'action':
                actionButtonsCode += c + '\n      '
            else:
                actionDropDownButtonsCode += c + '\n      '
        if button['function'] == 'handleDetail':
            c = """
      {
        label: '详情',
        onClick: handleDetail.bind(null, record),
      },""".strip()
            # 详情按钮
            if button['slot'] == 'action':
                actionButtonsCode += c + '\n      '
            else:
                actionDropDownButtonsCode += c + '\n      '
        if button['function'] == 'handleEdit':
            c = """
      {
        label: '编辑',
        onClick: handleEdit.bind(null, record),
      },""".strip()
            # 编辑按钮
            if button['slot'] == 'action':
                actionButtonsCode += c + '\n      '
            else:
                actionDropDownButtonsCode += c + '\n      '
        if button['function'] == 'onExportXls':
            other_api_funcs_code += ', getExportUrl'
            other_api_code_funcs += ', onExportXls'
            ImportAndExportConfCode += """
    exportConfig: {
      name: '%s导出结果',
      url: getExportUrl,
    },""" % title.strip()
            # 导出按钮
            if button['slot'] == 'tableTitle':
                c = """
        <a-button type="primary" preIcon="ant-design:export-outlined" @click="onExportXls"> 导出</a-button>"""
                tableTitleButtonCode += c + '\n'
            else:
                c = """
              <a-menu-item key="onExportXls" @click="onExportXls">
                <Icon icon="ant-design:export-outlined" />
                导出
              </a-menu-item>"""
                overlayButtonCode += c
        if button['function'] == 'onImportXls':
            other_api_funcs_code += ', getImportUrl'
            other_api_code_funcs += ', onImportXls'
            ImportAndExportConfCode += """
    importConfig: {
      url: getImportUrl,
      success: handleSuccess,
    },""".strip()
            # 导入按钮
            c = """
        <j-upload-button type="primary" preIcon="ant-design:import-outlined" @click="onImportXls">导入</j-upload-button>"""
            tableTitleButtonCode += c
    res_code = res_code.replace('${tableTitleButtonCode}', tableTitleButtonCode.strip())
    res_code = res_code.replace('${overlayButtonCode}', overlayButtonCode)
    res_code = res_code.replace('${actionButtonsCode}', actionButtonsCode.strip())
    res_code = res_code.replace('${actionDropDownButtonsCode}', actionDropDownButtonsCode.strip())
    res_code = res_code.replace('${other_api_funcs_code}', other_api_funcs_code)
    res_code = res_code.replace('${other_api_code_funcs}', other_api_code_funcs)
    res_code = res_code.replace('${ImportAndExportConfCode}', ImportAndExportConfCode)
    title = params.get('title')
    module_name = params['module_name']
    model_value = params['model_value']
    modal_type_map = {
        1: 'Modal',
        2: 'Drawer'
    }
    modal_type = params['modal_type']
    modal_type = modal_type_map.get(modal_type)
    res_code = res_code.replace('${title}', title)
    res_code = res_code.replace('${modal_type}', modal_type)
    res_code = res_code.replace('${model_value}', model_value)
    res_code = res_code.replace('${module_name}', module_name).strip() + '\n'
    return res_code


if __name__ == '__main__':
    from web_apps.code_generator.db_models import CodeGenModel, db
    obj = db.session.query(CodeGenModel).filter(CodeGenModel.id == '5deb88593c024033ae6de2f9ed5e7806').first()
    params = obj.to_dict()
    params['fields'] = json.loads(params['fields'])
    params['query_params'] = json.loads(params['query_params'])
    params['buttons'] = json.loads(params['buttons'])
    print(params)
    index_vue_code = gen_index_vue_code(params)
    print(index_vue_code)
    f = open('out/index.vue', 'w')
    f.write(index_vue_code)
