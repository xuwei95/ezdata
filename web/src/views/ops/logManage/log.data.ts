import { BasicColumn, FormSchema } from '/@/components/Table';
//列表数据
export const columns: BasicColumn[] = [
  {
    title: '_id',
    align: 'center',
    dataIndex: '_id',
    width: 200,
  },
  {
    title: '时间',
    align: 'center',
    dataIndex: 'asctime',
    width: 220,
  },
  {
    title: '用户',
    align: 'center',
    dataIndex: 'user_name',
  },
  {
    title: 'ip',
    align: 'center',
    dataIndex: 'ip',
  },
  {
    title: '日志等级',
    align: 'center',
    dataIndex: 'levelname',
  },
  {
    title: 'api路径',
    align: 'center',
    dataIndex: 'api_path',
  },
  {
    title: '请求参数',
    align: 'center',
    dataIndex: 'parameter',
  },
  {
    title: '响应时间',
    align: 'center',
    dataIndex: 'duration',
  },
];
//查询数据
export const searchFormSchema: FormSchema[] = [
  {
    label: '用户',
    field: 'user_name',
    component: 'Input',
  },
  {
    label: 'ip',
    field: 'ip',
    component: 'Input',
  },
  {
    label: 'api路径',
    field: 'api_path',
    component: 'Input',
  },
  {
    label: '日志等级',
    field: 'levelname',
    component: 'Input',
  },
  {
    label: '时间',
    field: 'time_range',
    component: 'RangePicker',
    componentProps: {
      'show-time': "{ format: 'HH:mm:ss' }",
      format: 'YYYY-MM-DD HH:mm:ss',
      valueFormat: 'YYYY-MM-DD HH:mm:ss',
      placeholder: ['开始时间', '结束时间'],
    },
  },
];
//表单数据
export const formSchema: FormSchema[] = [
  {
    label: 'pid',
    field: 'pid',
    required: false,
    component: 'Input',
  },
  {
    label: '名称',
    field: 'hostname',
    required: false,
    component: 'Input',
  },
  {
    label: '运行中任务',
    field: 'active',
    required: false,
    component: 'Input',
  },
  {
    label: '已处理',
    field: 'processed',
    required: false,
    component: 'Input',
  },
  {
    label: '状态',
    field: 'status',
    required: false,
    component: 'Input',
  },
  {
    label: '负载',
    field: 'loadavg',
    required: false,
    component: 'Input',
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
