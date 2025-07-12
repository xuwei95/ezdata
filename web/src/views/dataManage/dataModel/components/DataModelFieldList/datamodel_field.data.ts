import { BasicColumn, FormSchema } from '/@/components/Table';
// import { render } from "/@/utils/common/renderUtils";
// import { rules } from '/@/utils/helper/validator';
//列表数据
export const columns: BasicColumn[] = [
  {
    title: '字段名',
    align: 'center',
    dataIndex: 'field_name',
  },
  {
    title: '字段值',
    align: 'center',
    dataIndex: 'field_value',
  },
  {
    title: '类型',
    align: 'center',
    dataIndex: 'ext_params',
    customRender: ({ text }) => {
      return text['type'] || '';
    },
  },
  {
    title: '是否同步',
    align: 'center',
    dataIndex: 'is_sync',
    customRender: ({ text }) => {
      return text == 1 ? '是' : '否';
    },
  },
  {
    title: '描述',
    align: 'center',
    dataIndex: 'description',
  },
];
//查询数据
export const searchFormSchema: FormSchema[] = [
  {
    label: '字段名',
    field: 'field_name',
    component: 'Input',
  },
  {
    label: '字段值',
    field: 'field_value',
    component: 'Input',
  },
];
//表单数据
export const formSchema: FormSchema[] = [
  {
    label: '字段名',
    field: 'field_name',
    required: true,
    component: 'Input',
  },
  {
    label: '字段值',
    field: 'field_value',
    required: true,
    component: 'Input',
  },
  {
    label: '描述',
    field: 'description',
    required: false,
    component: 'InputTextArea',
  },
  {
    label: '拓展参数',
    field: 'ext_params',
    slot: 'ext_params',
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
