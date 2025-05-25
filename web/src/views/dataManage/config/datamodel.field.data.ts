//表单数据
import { FormSchema } from '/@/components/Form';

export const baseTableFieldSchema: FormSchema[] = [
  {
    label: '字段类型',
    field: 'type',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'Text',
    componentProps: {
      options: [
        { label: 'DateTime时间', value: 'DateTime' },
        { label: 'TIMESTAMP时间戳', value: 'TIMESTAMP' },
        { label: 'Float浮点数', value: 'Float' },
        { label: 'Integer整数', value: 'Integer' },
        { label: 'Text字符串', value: 'Text' },
        { label: 'String有限长度字符串', value: 'String' },
      ],
    },
  },
  {
    label: '长度',
    field: 'length',
    required: true,
    component: 'InputNumber',
    defaultValue: 0,
  },
  {
    label: '默认值',
    field: 'default',
    required: false,
    component: 'Input',
    defaultValue: '',
  },
];

export const mysqlTableFieldSchema: FormSchema[] = [
  {
    label: '字段类型',
    field: 'type',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'Text',
    componentProps: {
      options: [
        { label: 'DateTime时间', value: 'DateTime' },
        { label: 'TIMESTAMP时间戳', value: 'TIMESTAMP' },
        { label: 'SmallInteger短整数', value: 'SmallInteger' },
        { label: 'Float浮点数', value: 'Float' },
        { label: 'Integer整数', value: 'Integer' },
        { label: 'Text字符串', value: 'Text' },
        { label: 'LONGTEXT长字符串', value: 'LONGTEXT' },
        { label: 'String有限长度字符串', value: 'String' },
      ],
    },
  },
  {
    label: '长度',
    field: 'length',
    required: true,
    component: 'InputNumber',
    defaultValue: 0,
  },
  {
    label: '是否主键',
    field: 'primary_key',
    required: true,
    defaultValue: 0,
    component: 'JSwitch',
    componentProps: {
      options: [1, 0],
    },
  },
  {
    label: '是否可空',
    field: 'nullable',
    required: true,
    defaultValue: 1,
    component: 'JSwitch',
    componentProps: {
      options: [1, 0],
    },
  },
  {
    label: '默认值',
    field: 'default',
    required: false,
    component: 'Input',
    defaultValue: '',
  },
];

export const ckTableFieldSchema: FormSchema[] = [
  {
    label: '字段类型',
    field: 'type',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'Text',
    componentProps: {
      options: [
        { label: 'DateTime时间', value: 'DateTime' },
        { label: 'TIMESTAMP时间戳', value: 'TIMESTAMP' },
        { label: 'Float浮点数', value: 'Float' },
        { label: 'Integer整数', value: 'Integer' },
        { label: 'String字符串', value: 'String' },
        { label: 'FixedString有限长度字符串', value: 'FixedString' },
      ],
    },
  },
  {
    label: '长度',
    field: 'length',
    required: true,
    component: 'InputNumber',
    defaultValue: 50,
    ifShow: ({ values }) => values.type == 'FixedString',
  },
  {
    label: '是否主键',
    field: 'primary_key',
    required: true,
    defaultValue: 0,
    component: 'JSwitch',
    componentProps: {
      options: [1, 0],
    },
  },
  {
    label: '是否可空',
    field: 'nullable',
    required: true,
    defaultValue: 1,
    component: 'JSwitch',
    componentProps: {
      options: [1, 0],
    },
  },
  {
    label: '默认值',
    field: 'default',
    required: false,
    component: 'Input',
    defaultValue: '',
  },
];

export const esIndexFieldSchema: FormSchema[] = [
  {
    label: '字段类型',
    field: 'type',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'text',
    componentProps: {
      options: [
        { label: 'text', value: 'text' },
        { label: 'keyword', value: 'keyword' },
        { label: 'float', value: 'float' },
        { label: 'integer', value: 'integer' },
        { label: 'long', value: 'long' },
        { label: 'date', value: 'date' },
        { label: 'nested', value: 'nested' },
      ],
    },
  },
  // {
  //   label: '时间类型',
  //   field: 'name',
  //   required: true,
  //   component: 'Input',
  //   defaultValue: '',
  //   ifShow: ({ values }) => values.type == 'date',
  // },
];

export const mongoCollectionFieldSchema: FormSchema[] = [
  {
    label: '字段类型',
    field: 'type',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'text',
    componentProps: {
      options: [
        { label: '字符串', value: 'text' },
        { label: '对象', value: 'object' },
        { label: '列表', value: 'list' },
        { label: '浮点数', value: 'float' },
        { label: '整数', value: 'integer' },
        { label: '日期', value: 'date' },
      ],
    },
  },
];

export const neo4jGraphFieldSchema: FormSchema[] = [
  {
    label: '字段类型',
    field: 'type',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'text',
    componentProps: {
      options: [
        { label: '字符串', value: 'text' },
        { label: '对象', value: 'object' },
        { label: '列表', value: 'list' },
        { label: '浮点数', value: 'float' },
        { label: '整数', value: 'integer' },
        { label: '日期', value: 'date' },
      ],
    },
  },
];

export const influxdbTableFieldSchema: FormSchema[] = [
  {
    label: '字段类型',
    field: 'type',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'field',
    componentProps: {
      options: [
        { label: '标签', value: 'tag' },
        { label: '字段', value: 'field' },
        { label: '时间', value: 'time' },
      ],
    },
  },
];
