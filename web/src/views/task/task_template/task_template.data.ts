import { BasicColumn, FormSchema } from '/@/components/Table';
import { render } from '/@/utils/common/renderUtils';
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
    title: '模版名称',
    align: 'center',
    dataIndex: 'name',
  },
  {
    title: '模版编码',
    align: 'center',
    dataIndex: 'code',
  },
  {
    title: '模版图标',
    dataIndex: 'icon',
    width: 120,
    customRender: render.renderImage,
  },
  {
    title: '表单类型',
    align: 'center',
    dataIndex: 'type',
    customRender: ({ text }) => {
      return text == 1 ? '内置组件' : '动态配置';
    },
  },
  {
    title: '执行器类型',
    align: 'center',
    dataIndex: 'runner_type',
    customRender: ({ text }) => {
      return text == 1 ? '内置执行器' : '动态代码';
    },
  },
  {
    title: '任务组件',
    align: 'center',
    dataIndex: 'component',
    customRender: ({ text }) => {
      return render.renderDict(text, 'task_components');
    },
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
    label: '模版类型',
    field: 'type',
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'task_template_type',
      placeholder: '请选择模版类型',
      stringToNumber: true,
    },
  },
  {
    label: '模版编码',
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
    label: '模版名称',
    field: 'name',
    required: true,
    component: 'Input',
  },
  {
    label: '模版编码',
    field: 'code',
    required: true,
    component: 'Input',
    dynamicDisabled: ({ values }) => {
      return !!values.id;
    },
  },
  {
    label: '模版图标',
    field: 'icon',
    component: 'JImageUpload',
    componentProps: {
      fileMax: 1,
    },
  },
  {
    label: '表单类型',
    field: 'type',
    required: true,
    component: 'RadioGroup',
    defaultValue: 1,
    componentProps: {
      options: [
        { label: '内置组件', value: 1 },
        { label: '动态配置', value: 2 },
      ],
    },
  },
  {
    label: '任务组件',
    field: 'component',
    required: true,
    component: 'JDictSelectTag',
    defaultValue: 'PythonTask',
    componentProps: {
      dictCode: 'task_components',
      placeholder: '请选择任务组件类型',
      stringToNumber: false,
    },
    ifShow: ({ values }) => values.type == 1,
  },
  {
    label: '模版配置',
    field: 'params',
    required: true,
    component: 'MonacoEditor',
    defaultValue: '[]',
    componentProps: {
      language: 'json',
      height: '300px',
    },
    ifShow: ({ values }) => values.type == 2,
  },
  {
    label: '执行器类型',
    field: 'runner_type',
    required: true,
    component: 'RadioGroup',
    defaultValue: 1,
    componentProps: {
      options: [
        { label: '内置执行器', value: 1 },
        { label: '动态代码', value: 2 },
      ],
    },
  },
  {
    label: '执行器代码',
    field: 'runner_code',
    required: true,
    component: 'MonacoEditor',
    defaultValue:
      'def run(params, logger):\n' +
      "    '''\n" +
      '    任务执行函数\n' +
      '    :param params: 任务参数\n' +
      '    :param logger: 日志logger\n' +
      '    :return:\n' +
      "    '''\n" +
      '    logger.info(str(params))',
    componentProps: {
      language: 'python',
      height: '300px',
    },
    ifShow: ({ values }) => values.runner_type == 2,
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
