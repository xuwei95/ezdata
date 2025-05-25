import { BasicColumn, FormSchema } from '/@/components/Table';
import { render } from "/@/utils/common/renderUtils";
//列表数据
export const columns: BasicColumn[] = [
  {
    title: 'ID',
    align: 'center',
    dataIndex: 'id',
    defaultHidden: true,
  },
  {
    title: '算法名称',
    align: 'center',
    dataIndex: 'name',
  },
  {
    title: '算法编码',
    align: 'center',
    dataIndex: 'code',
  },
  {
    title: '算法类型',
    align: 'center',
    dataIndex: 'type',
    customRender: ({ text }) => {
      return render.renderDict(text, 'alg_type');
    },
  },
  {
    title: '表单类型',
    align: 'center',
    dataIndex: 'form_type',
    customRender: ({ text }) => {
      return text == 1 ? '组件型' : '配置型';
    },
  },
  {
    title: '算法组件',
    align: 'center',
    dataIndex: 'component',
  },
  {
    title: '状态',
    align: 'center',
    dataIndex: 'status',
    customRender: ({ text }) => {
      return text == 1 ? '启用' : '禁用';
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
    label: '算法类型',
    field: 'type',
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'alg_type',
      placeholder: '请选择算法类型',
      stringToNumber: false,
    },
  },
  {
    label: '算法编码',
    field: 'code',
    component: 'Input',
  },
  {
    label: '名称',
    field: 'name',
    component: 'Input',
  },
];
//表单数据
export const formSchema: FormSchema[] = [
  {
    label: '算法名称',
    field: 'name',
    required: true,
    component: 'Input',
  },
  {
    label: '算法编码',
    field: 'code',
    required: true,
    component: 'Input',
  },
  {
    label: '算法类型',
    field: 'type',
    required: true,
    component: 'JDictSelectTag',
    defaultValue: 'etl_algorithm',
    componentProps: {
      dictCode: 'alg_type',
      placeholder: '请选择算法类型',
      stringToNumber: false,
    },
  },
  {
    label: '表单类型',
    field: 'form_type',
    required: true,
    component: 'JDictSelectTag',
    defaultValue: 2,
    componentProps: {
      dictCode: 'alg_form_type',
      placeholder: '请选择表单类型',
      stringToNumber: true,
    },
  },
  {
    label: '算法组件',
    field: 'component',
    required: true,
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'alg_component',
      placeholder: '请选择表单类型',
      stringToNumber: true,
    },
    ifShow: ({ values }) => values.form_type == 1,
  },
  {
    label: '算法配置',
    field: 'params',
    required: true,
    component: 'MonacoEditor',
    componentProps: {
      language: 'json',
    },
    ifShow: ({ values }) => values.form_type == 2,
  },
  {
    label: '状态',
    field: 'status',
    required: true,
    component: 'RadioGroup',
    defaultValue: 1,
    componentProps: {
      options: [
        { label: '启用', value: 1 },
        { label: '禁用', value: 0 },
      ],
    },
  },
  {
    label: '排序',
    field: 'sort_no',
    required: true,
    defaultValue: 1,
    component: 'InputNumber',
  },
  {
    label: '描述',
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
