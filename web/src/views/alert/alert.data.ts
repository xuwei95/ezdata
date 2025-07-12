import { BasicColumn, FormSchema } from '/@/components/Table';
import { render } from "/@/utils/common/renderUtils";
//列表数据
export const columns: BasicColumn[] = [
  {
    title: 'id',
    align: 'center',
    dataIndex: 'id',
    defaultHidden: true,
    width: 320,
  },
  {
    title: '告警策略id',
    align: 'center',
    dataIndex: 'strategy_id',
    defaultHidden: true,
    width: 320,
  },
  {
    title: '告警标题',
    align: 'center',
    dataIndex: 'title',
  },
  {
    title: '告警内容',
    align: 'center',
    dataIndex: 'content',
    width: 400,
  },
  {
    title: '告警等级',
    align: 'center',
    dataIndex: 'level',
    customRender: ({ text }) => {
      return render.renderDict(text, 'alert_level');
    },
  },
  {
    title: '告警状态',
    align: 'center',
    dataIndex: 'status',
    customRender: ({ text }) => {
      return render.renderDict(text, 'alert_status');
    },
  },
  {
    title: '规则编码',
    align: 'center',
    dataIndex: 'rule_id',
  },
  {
    title: '规则名称',
    align: 'center',
    dataIndex: 'rule_name',
  },
  {
    title: '告警业务',
    align: 'center',
    dataIndex: 'biz',
  },
  {
    title: '告警对象',
    align: 'center',
    dataIndex: 'source',
  },
  {
    title: '告警标签',
    align: 'center',
    dataIndex: 'tags',
  },
  {
    title: '告警指标',
    align: 'center',
    dataIndex: 'metric',
  },
  {
    title: '恢复时间',
    align: 'center',
    dataIndex: 'recover_time',
  },
  {
    title: '额外参数',
    align: 'center',
    dataIndex: 'ext_params',
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
    label: '告警标题',
    field: 'title',
    component: 'Input',
  },
  {
    label: '告警等级',
    field: 'level',
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'alert_level',
      placeholder: '请选择告警等级',
      stringToNumber: true,
    },
  },
  {
    label: '告警状态',
    field: 'status',
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'alert_status',
      placeholder: '请选择告警状态',
      stringToNumber: true,
    },
  },
  {
    label: '告警内容',
    field: 'content',
    component: 'Input',
  },
  {
    label: '创建时间',
    field: 'create_time',
    component: 'Input',
  },
];
//表单数据
export const formSchema: FormSchema[] = [
  {
    label: '告警策略id',
    field: 'strategy_id',
    required: false,
    component: 'Input',
  },
  {
    label: '告警标题',
    field: 'title',
    required: false,
    component: 'Input',
  },
  {
    label: '告警内容',
    field: 'content',
    required: false,
    component: 'InputTextArea',
  },
  {
    label: '告警等级',
    field: 'level',
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'alert_level',
      placeholder: '请选择告警等级',
      stringToNumber: true,
    },
  },
  {
    label: '告警状态',
    field: 'status',
    required: false,
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'alert_status',
      placeholder: '请选择告警状态',
      stringToNumber: true,
    },
  },
  {
    label: '规则编码',
    field: 'rule_id',
    required: false,
    component: 'Input',
  },
  {
    label: '规则名称',
    field: 'rule_name',
    required: false,
    component: 'Input',
  },
  {
    label: '告警业务',
    field: 'biz',
    required: false,
    component: 'Input',
  },
  {
    label: '告警对象',
    field: 'source',
    required: false,
    component: 'Input',
  },
  {
    label: '告警标签',
    field: 'tags',
    required: false,
    component: 'InputTextArea',
  },
  {
    label: '告警指标',
    field: 'metric',
    required: false,
    component: 'Input',
  },
  {
    label: '恢复时间',
    field: 'recover_time',
    required: false,
    component: 'Input',
  },
  {
    label: '额外参数',
    field: 'ext_params',
    required: false,
    component: 'Input',
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
