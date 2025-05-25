import { BasicColumn, FormSchema } from '/@/components/Table';
import { allSourceList } from './datamodel.api';
import { render } from '/@/utils/common/renderUtils';
import { getAllDepartList } from '/@/views/system/user/user.api';
// import { rules } from '/@/utils/helper/validator';
//列表数据
export const columns: BasicColumn[] = [
  {
    title: 'ID',
    align: 'center',
    dataIndex: 'id',
    defaultHidden: true,
    width: 300,
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
    customRender: ({ text }) => {
      return render.renderDict(text, 'datamodel_type');
    },
  },
  {
    title: '模型状态',
    align: 'center',
    dataIndex: 'status',
    customRender: ({ text }) => {
      return text == 1 ? '已存在' : '未建立';
    },
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
  {
    title: '简介描述',
    align: 'center',
    dataIndex: 'description',
  },
];
//查询数据
export const searchFormSchema: FormSchema[] = [
  {
    label: '名称',
    field: 'name',
    component: 'Input',
  },
  {
    label: '所属数据源',
    field: 'datasource_id',
    component: 'ApiSelect',
    componentProps: {
      api: allSourceList,
      params: {},
      labelField: 'name',
      valueField: 'id',
    },
  },
  {
    label: '类型',
    field: 'type',
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'datamodel_type',
      placeholder: '请选择模型类型',
      stringToNumber: false,
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
    label: '所属数据源',
    field: 'datasource_id',
    slot: 'datasource_id',
    required: true,
    component: 'Input',
  },
  {
    label: '类型',
    field: 'type',
    required: true,
    slot: 'type',
    component: 'Input',
  },
  {
    label: '',
    field: 'model_conf',
    slot: 'model_conf',
    required: false,
    defaultValue: {},
    component: 'InputTextArea',
  },
  {
    label: '查询接口',
    field: 'can_interface',
    defaultValue: 0,
    required: true,
    component: 'RadioGroup',
    componentProps: {
      options: [
        { label: '开启', value: 1 },
        { label: '关闭', value: 0 },
      ],
    },
  },
  {
    label: '所属用户组',
    field: 'depart_list',
    component: 'ApiSelect',
    required: false,
    componentProps: {
      mode: 'multiple',
      api: getAllDepartList,
      labelField: 'depart_name',
      valueField: 'org_code',
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
    field: 'sort_no',
    label: '排序',
    component: 'InputNumber',
    defaultValue: 1,
  },
  {
    label: '简介描述',
    field: 'description',
    required: false,
    component: 'InputTextArea',
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
