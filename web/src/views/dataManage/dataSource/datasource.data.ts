import { BasicColumn, FormSchema } from '/@/components/Table';
import { getDataSourceTypes } from './datasource.api';
// import { render } from "/@/utils/common/renderUtils";
// import { rules } from '/@/utils/helper/validator';
//列表数据
export const columns: BasicColumn[] = [
  {
    title: 'ID',
    align: 'center',
    dataIndex: 'id',
    width: 300,
    defaultHidden: true,
  },
  {
    title: '名称',
    align: 'center',
    dataIndex: 'name',
    width: 280,
  },
  {
    title: '类型',
    align: 'center',
    dataIndex: 'type',
  },
  {
    title: '连接状态',
    align: 'center',
    dataIndex: 'status',
    customRender: ({ text }) => {
      return text == 0 ? '失败' : '成功';
    },
  },
  {
    title: '描述',
    align: 'center',
    dataIndex: 'description',
  },
  {
    title: '创建者',
    align: 'center',
    dataIndex: 'create_by',
  },
  {
    title: '创建时间',
    align: 'center',
    dataIndex: 'create_time',
    width: 200,
  },
  {
    title: '修改者',
    align: 'center',
    dataIndex: 'update_by',
  },
  {
    title: '修改时间',
    align: 'center',
    dataIndex: 'update_time',
    width: 200,
  },
];
//查询数据
export const searchFormSchema: FormSchema[] = [
  {
    label: '数据源名称',
    field: 'name',
    component: 'Input',
  },
  {
    label: '数据源类型',
    field: 'type',
    component: 'ApiSelect',
    componentProps: {
      api: getDataSourceTypes,
      params: {},
      placeholder: '请选择数据源类型',
      labelField: 'label',
      valueField: 'value',
      showSearch: true,
      filterOption: (input, option) => {
        return (option?.label ?? '').toLowerCase().includes(input.toLowerCase());
      },
    },
  },
];
//表单数据
export const formSchema: FormSchema[] = [
  {
    label: '名称',
    field: 'name',
    required: true,
    component: 'Input',
  },
  {
    label: '类型',
    field: 'type',
    required: true,
    component: 'Input',
    slot: 'type',
    defaultValue: 'mysql',
  },
  {
    label: '', // 连接配置
    field: 'conn_conf',
    // required: true,
    slot: 'conn_conf',
    component: 'InputTextArea',
    defaultValue: {
      host: '127.0.0.1',
      port: 3306,
      username: '',
      password: '',
      database_name: '',
    },
  },
  {
    label: '额外参数',
    field: 'ext_params',
    required: false,
    component: 'MonacoEditor',
    defaultValue: '{}',
    componentProps: {
      language: 'json',
    },
  },
  {
    label: '自动建模',
    field: 'auto_gen',
    defaultValue: '0',
    component: 'JSwitch',
    componentProps: {
      options: ['1', '0'],
    },
    ifShow: ({ values }) => !values.id,
  },
  {
    label: '描述',
    field: 'description',
    required: false,
    component: 'InputTextArea',
  },
  {
    field: 'sort_no',
    label: '排序',
    component: 'InputNumber',
    defaultValue: 1,
  },
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
