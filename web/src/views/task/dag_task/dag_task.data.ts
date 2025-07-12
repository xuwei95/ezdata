import { BasicColumn, FormSchema } from '/@/components/Table';
import { allAlertStrategyList } from '/@/views/alert/alert_strategy/alert_strategy.api';

//列表数据
export const columns: BasicColumn[] = [
  {
    title: '名称',
    align: 'center',
    dataIndex: 'name',
    width: 300,
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
    title: '运行模式',
    align: 'center',
    dataIndex: 'run_type',
    customRender: ({ text }) => {
      return text == 1 ? '分布式' : '单进程';
    },
  },
  {
    title: '触发方式',
    align: 'center',
    dataIndex: 'trigger_type',
    customRender: ({ text }) => {
      return text == 1 ? '单次' : '定时';
    },
  },
  {
    title: '定时设置',
    align: 'center',
    dataIndex: 'crontab',
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
    title: '描述',
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
    label: '优先级',
    field: 'priority',
    required: true,
    component: 'InputNumber',
    defaultValue: 1,
    componentProps: {
      style: 'width: 200px',
      min: 1,
    },
  },
  {
    label: '重试次数',
    field: 'retry',
    required: true,
    component: 'InputNumber',
    defaultValue: 0,
    componentProps: {
      style: 'width: 200px',
      min: 0,
    },
  },
  {
    label: '重试间隔(秒)',
    field: 'countdown',
    required: true,
    component: 'InputNumber',
    defaultValue: 0,
    componentProps: {
      style: 'width: 200px',
      min: 0,
    },
  },
  {
    label: '运行方式',
    field: 'run_type',
    required: true,
    component: 'RadioGroup',
    defaultValue: 1,
    componentProps: {
      options: [
        { label: '分布式', value: 1 },
        { label: '单进程', value: 2 },
      ],
    },
  },
  {
    label: '触发方式',
    field: 'trigger_type',
    required: true,
    component: 'RadioGroup',
    defaultValue: 1,
    componentProps: {
      options: [
        { label: '单次', value: 1 },
        { label: '定时', value: 2 },
      ],
    },
  },
  {
    label: '触发始末时间',
    field: 'trigger_date',
    component: 'RangePicker',
    componentProps: {
      'show-time': "{ format: 'HH:mm:ss' }",
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'YYYY-MM-DD HH:mm:ss',
      placeholder: ['开始时间', '结束时间'],
    },
    ifShow: ({ values }) => values.trigger_type == 2,
  },
  {
    label: '定时设置',
    field: 'crontab',
    required: true,
    component: 'JEasyCron',
    ifShow: ({ values }) => values.trigger_type == 2,
  },
  {
    label: '描述',
    field: 'description',
    required: false,
    component: 'InputTextArea',
  },
  {
    label: '失败告警策略',
    field: 'alert_strategy_ids',
    required: false,
    component: 'ApiSelect',
    defaultValue: '',
    componentProps: {
      api: allAlertStrategyList,
      mode: 'multiple',
      params: {
        template_code: 'TaskFailStrategy',
      },
      labelField: 'name',
      valueField: 'id',
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
