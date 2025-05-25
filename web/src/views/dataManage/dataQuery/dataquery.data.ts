import { FormSchema } from '/@/components/Table';
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
    label: '模型配置',
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
