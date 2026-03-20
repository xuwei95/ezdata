import { BasicColumn, FormSchema } from '/@/components/Table';

const MODEL_TYPE_MAP = { chat: '对话', embedding: '向量' };

export const columns: BasicColumn[] = [
  {
    title: '提供商',
    align: 'center',
    dataIndex: 'provider',
    width: 120,
  },
  {
    title: '模型名称',
    align: 'center',
    dataIndex: 'name',
    width: 180,
  },
  {
    title: '模型代码',
    align: 'center',
    dataIndex: 'model_code',
    ellipsis: true,
  },
  {
    title: '类型',
    align: 'center',
    dataIndex: 'model_type',
    width: 100,
    customRender: ({ text }) => MODEL_TYPE_MAP[text] || text,
  },
  {
    title: 'Base URL',
    align: 'center',
    dataIndex: 'base_url',
    ellipsis: true,
  },
  {
    title: '默认',
    align: 'center',
    dataIndex: 'is_default',
    width: 70,
    customRender: ({ text }) => (text === 1 ? '✓' : ''),
  },
  {
    title: '状态',
    align: 'center',
    dataIndex: 'status',
    width: 80,
    customRender: ({ text }) => (text === 1 ? '启用' : '禁用'),
  },
  {
    title: '创建时间',
    align: 'center',
    dataIndex: 'create_time',
    width: 160,
  },
];

export const searchFormSchema: FormSchema[] = [
  {
    label: '提供商',
    field: 'provider',
    component: 'Select',
    colProps: { span: 6 },
    componentProps: { options: [] },
  },
  {
    label: '类型',
    field: 'model_type',
    component: 'Select',
    colProps: { span: 6 },
    componentProps: {
      options: [
        { label: '全部', value: '' },
        { label: '对话(chat)', value: 'chat' },
        { label: '向量(embedding)', value: 'embedding' },
      ],
    },
  },
  {
    label: '关键词',
    field: 'keyword',
    component: 'Input',
    colProps: { span: 6 },
    componentProps: { placeholder: '模型名称/代码' },
  },
];
