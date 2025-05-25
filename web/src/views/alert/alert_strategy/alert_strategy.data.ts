import { BasicColumn, FormSchema } from '/@/components/Table';
import { render } from '/@/utils/common/renderUtils';
//列表数据
export const columns: BasicColumn[] = [
  {
    title: 'ID',
    align: 'center',
    dataIndex: 'id',
    defaultHidden: true,
  },
  {
    title: '策略名称',
    align: 'center',
    dataIndex: 'name',
  },
  {
    title: '策略模版',
    align: 'center',
    dataIndex: 'template_code',
    customRender: ({ text }) => {
      return render.renderDict(text, 'alert_strategy_template');
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
    label: '策略模版',
    field: 'template_code',
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'alert_strategy_template',
      placeholder: '请选择模版类型',
      stringToNumber: true,
    },
  },
];
//表单数据
export const formSchema: FormSchema[] = [
  {
    label: '策略名称',
    field: 'name',
    required: true,
    component: 'Input',
    colProps: {
      style: {
        width: '500px',
      },
    },
  },
  {
    label: '策略模版',
    field: 'template_code',
    required: true,
    slot: 'template_code',
    component: 'Input',
  },
  {
    label: '简介描述',
    field: 'description',
    required: false,
    component: 'InputTextArea',
    colProps: {
      style: {
        width: '500px',
      },
    },
  },
  {
    label: '触发配置',
    field: 'trigger_conf',
    slot: 'trigger_conf',
    required: false,
    component: 'MonacoEditor',
    defaultValue: '{}',
    componentProps: {
      language: 'json',
    },
  },
  {
    label: '转发配置',
    field: 'forward_conf',
    slot: 'forward_conf',
    required: false,
    component: 'MonacoEditor',
    defaultValue: '[]',
    componentProps: {
      language: 'json',
    },
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
