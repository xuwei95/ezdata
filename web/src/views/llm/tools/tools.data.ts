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
    title: '工具名称',
    align: 'center',
    dataIndex: 'name',
    width: 200,
  },
  {
    title: '工具代码',
    align: 'center',
    dataIndex: 'code',
    width: 180,
  },
  {
    title: '类型',
    align: 'center',
    dataIndex: 'type',
    width: 120,
    customRender: ({ text }) => {
      const typeMap = {
        mcp: 'MCP工具',
      };
      return typeMap[text] || text;
    },
  },
  {
    title: '描述',
    align: 'center',
    dataIndex: 'description',
    ellipsis: true,
  },
  {
    title: '状态',
    align: 'center',
    dataIndex: 'status',
    width: 100,
    customRender: ({ text }) => {
      return text == 1 ? '启用' : '禁用';
    },
  },
  {
    title: '创建者',
    align: 'center',
    dataIndex: 'create_by',
    width: 120,
  },
  {
    title: '创建时间',
    align: 'center',
    dataIndex: 'create_time',
    width: 180,
  },
];

//查询数据
export const searchFormSchema: FormSchema[] = [
  {
    label: '工具名称',
    field: 'keyword',
    component: 'Input',
    colProps: { span: 6 },
  },
  {
    label: '工具类型',
    field: 'type',
    component: 'Select',
    colProps: { span: 6 },
    componentProps: {
      options: [
        { label: '全部', value: '' },
        { label: 'MCP工具', value: 'mcp' },
      ],
    },
  },
];
