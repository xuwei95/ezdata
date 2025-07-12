import { BasicColumn, FormSchema } from '/@/components/Table';
//列表数据
export const columns: BasicColumn[] = [
  {
    title: 'pid',
    align: 'center',
    dataIndex: 'pid',
  },
  {
    title: '名称',
    align: 'center',
    dataIndex: 'hostname',
  },
  {
    title: '状态',
    align: 'center',
    dataIndex: 'status',
    customRender: function ({ record }) {
      // @ts-ignore
      return record.status ? '在线' : '离线';
    },
  },
  {
    title: '运行中任务',
    align: 'center',
    dataIndex: 'active',
  },
  {
    title: '已处理',
    align: 'center',
    dataIndex: 'processed',
  },
  {
    title: '处理成功',
    align: 'center',
    dataIndex: 'taREDACTEDsucceeded',
    customRender: function (text) {
      return text || 0;
    },
  },
  {
    title: '处理失败',
    align: 'center',
    dataIndex: 'taREDACTEDfailed',
    customRender: function (text) {
      return text || 0;
    },
  },
  {
    title: '重试中',
    align: 'center',
    dataIndex: 'taREDACTEDretried',
    customRender: function (text) {
      return text || 0;
    },
  },
  {
    title: '负载',
    align: 'center',
    dataIndex: 'loadavg',
    customRender: function (text) {
      return JSON.stringify(text.text);
    },
  },
];
//查询数据
export const searchFormSchema: FormSchema[] = [
  {
    label: '名称',
    field: 'hostname',
    component: 'Input',
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
