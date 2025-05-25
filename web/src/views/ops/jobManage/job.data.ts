import { BasicColumn, FormSchema } from '/@/components/Table';
//列表数据
export const columns: BasicColumn[] = [
  {
    title: 'id',
    align: 'center',
    dataIndex: 'id',
  },
  {
    title: '任务函数',
    align: 'center',
    dataIndex: 'kwargs',
    customRender: function (text) {
      return text.text.func || '';
    },
  },
  {
    title: '任务参数',
    align: 'center',
    dataIndex: 'kwargs',
    customRender: function (text) {
      return JSON.stringify(text.text.kwargs) || JSON.stringify(text.text);
    },
  },
  {
    title: '下次运行时间',
    align: 'center',
    dataIndex: 'next_run_time',
    width: 200,
  },
  {
    title: '触发方式',
    align: 'center',
    dataIndex: 'trigger',
  },
  {
    title: '触发参数',
    align: 'center',
    dataIndex: 'trigger',
    customRender: function ({ text, record }) {
      const trigger_info = {
        second: record.second || '',
        minute: record.minute || '',
        hour: record.hour || '',
        day: record.day || '',
        day_of_week: record.day_of_week || '',
        month: record.month || '',
        year: record.year || '',
      };
      return JSON.stringify(trigger_info);
    },
  },
];

//查询数据
export const searchFormSchema: FormSchema[] = [
  {
    label: 'id',
    field: 'id',
    component: 'Input',
  },
];

//表单数据
export const formSchema: FormSchema[] = [];

/**
 * 流程表单调用这个方法获取formSchema
 * @param param
 */
export function getBpmFormSchema(_formData): FormSchema[] {
  // 默认和原始表单保持一致 如果流程中配置了权限数据，这里需要单独处理formSchema
  return formSchema;
}
