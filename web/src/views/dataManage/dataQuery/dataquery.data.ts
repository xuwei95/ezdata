import { FormSchema, BasicColumn } from '/@/components/Table';
import { DescItem } from '/@/components/Description';

export const descSchema: DescItem[] = [
  {
    label: 'ID',
    field: 'id',
  },
  {
    label: '名称',
    field: 'name',
  },
  {
    label: '所属数据源',
    field: 'datasource_id',
  },
  {
    label: '简介描述',
    field: 'description',
  },
  {
    label: '模型配置',
    field: 'model_conf',
    render(val) {
      return JSON.stringify(val);
    },
  },
  {
    label: '额外参数',
    field: 'ext_params',
    render(val) {
      return JSON.stringify(val);
    },
  },
  {
    label: '是否可封装接口',
    field: 'can_interface',
    render(val) {
      return JSON.stringify(val);
    },
  },
  {
    label: '字段信息',
    field: 'fields',
    render(val) {
      return JSON.stringify(val);
    },
  },
];

// 基本信息表单Schema（详情只读）
export const infoFormSchema: FormSchema[] = [
  {
    label: 'ID',
    field: 'id',
    component: 'Input',
  },
  {
    label: '名称',
    field: 'name',
    component: 'Input',
  },
  {
    label: '所属数据源',
    field: 'datasource_id',
    component: 'Input',
  },
  {
    label: '模型类型',
    field: 'type',
    component: 'Input',
  },
  {
    label: '简介描述',
    field: 'description',
    component: 'InputTextArea',
  },
  {
    label: '模型配置',
    field: 'model_conf',
    component: 'MonacoEditor',
    componentProps: {
      language: 'json',
    },
  },
  {
    label: '额外参数',
    field: 'ext_params',
    component: 'MonacoEditor',
    componentProps: {
      language: 'json',
    },
  },
  {
    label: '是否可封装接口',
    field: 'can_interface',
    component: 'RadioGroup',
    componentProps: {
      options: [
        { label: '是', value: 1 },
        { label: '否', value: 0 },
      ],
    },
  },
];

// 字段列表表格列配置
export const fieldColumns: BasicColumn[] = [
  {
    title: '字段名',
    align: 'center',
    dataIndex: 'field_name',
    width: 150,
  },
  {
    title: '字段值',
    align: 'center',
    dataIndex: 'field_value',
    width: 150,
  },
  {
    title: '类型',
    align: 'center',
    dataIndex: 'ext_params',
    width: 120,
    customRender: ({ record }) => {
      return record.ext_params?.type || '';
    },
  },
  {
    title: '是否同步',
    align: 'center',
    dataIndex: 'is_sync',
    width: 100,
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

//表单数据
export const formSchema: FormSchema[] = [
  {
    label: '名称',
    field: 'name',
    required: true,
    component: 'Input',
  },
  {
    label: '所属数据源',
    field: 'datasource_id',
    slot: 'datasource_id',
    required: true,
    component: 'Input',
  },
  {
    label: '类型',
    field: 'type',
    required: true,
    slot: 'type',
    component: 'Input',
  },
  {
    label: '',
    field: 'model_conf',
    slot: 'model_conf',
    required: false,
    defaultValue: {},
    component: 'InputTextArea',
  },
  {
    label: '额外参数',
    field: 'ext_params',
    required: false,
    component: 'MonacoEditor',
    defaultValue: '{}',
    componentProps: {
      language: 'json',
    },
  },
  {
    label: '是否可封装接口',
    field: 'can_interface',
    defaultValue: 1,
    required: true,
    component: 'RadioGroup',
    componentProps: {
      options: [
        { label: '是', value: 1 },
        { label: '否', value: 0 },
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
