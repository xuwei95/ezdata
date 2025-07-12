//表单数据
import { FormSchema } from '/@/components/Form';
export const akshareFormSchema: FormSchema[] = [];
export const ccxtFormSchema: FormSchema[] = [];
export const httpFormSchema: FormSchema[] = [
  {
    label: '连接地址',
    field: 'url',
    required: true,
    component: 'Input',
  },
  {
    label: '请求方式',
    field: 'method',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'get',
    componentProps: {
      options: [
        { label: 'GET', value: 'get' },
        { label: 'POST', value: 'post' },
        { label: 'PUT', value: 'put' },
        { label: 'DELETE', value: 'delete' },
      ],
    },
  },
  {
    label: '超时时长(s)',
    field: 'timeout',
    required: true,
    component: 'InputNumber',
    defaultValue: 30,
    componentProps: {
      min: 0,
    },
  },
  {
    label: '请求头',
    field: 'headers',
    required: true,
    defaultValue: '{}',
    component: 'MonacoEditor',
    componentProps: {
      language: 'json',
    },
  },
  {
    label: '请求体',
    field: 'req_body',
    required: true,
    defaultValue: '{}',
    component: 'MonacoEditor',
    componentProps: {
      language: 'json',
    },
  },
];

export const fileFormSchema: FormSchema[] = [
  {
    label: '文件地址',
    field: 'path',
    required: true,
    component: 'Input',
  },
];

export const minioFormSchema: FormSchema[] = [
  {
    label: 'url',
    field: 'url',
    required: true,
    component: 'Input',
  },
  {
    label: '用户名',
    field: 'username',
    required: true,
    component: 'Input',
  },
  {
    label: '密码',
    field: 'password',
    required: true,
    component: 'InputPassword',
  },
  {
    label: 'bucket',
    field: 'bucket',
    required: true,
    component: 'Input',
  },
];

export const redisFormSchema: FormSchema[] = [
  {
    label: '服务器',
    field: 'host',
    required: true,
    component: 'Input',
  },
  {
    label: '端口',
    field: 'port',
    required: true,
    component: 'InputNumber',
  },
  {
    label: '密码',
    field: 'password',
    required: true,
    component: 'InputPassword',
  },
  {
    label: '数据库',
    field: 'db',
    required: true,
    component: 'InputNumber',
  },
];

export const BaseDBFormSchema: FormSchema[] = [
  {
    label: '服务器',
    field: 'host',
    required: true,
    component: 'Input',
  },
  {
    label: '端口',
    field: 'port',
    required: true,
    component: 'InputNumber',
  },
  {
    label: '用户名',
    field: 'username',
    required: true,
    component: 'Input',
  },
  {
    label: '密码',
    field: 'password',
    required: true,
    component: 'InputPassword',
  },
  {
    label: '数据库',
    field: 'database_name',
    required: true,
    component: 'Input',
  },
];

export const esFormSchema: FormSchema[] = [
  {
    label: '连接地址',
    field: 'url',
    required: true,
    component: 'Input',
  },
  {
    label: '验证类型',
    field: 'auth_type',
    component: 'RadioGroup',
    defaultValue: 1,
    required: true,
    componentProps: {
      options: [
        { label: '无', value: 1, key: '1' },
        { label: '用户密码', value: 2, key: '2' },
      ],
    },
  },
  {
    label: '用户名',
    field: 'username',
    required: true,
    component: 'Input',
    ifShow: ({ values }) => values.auth_type == 2,
  },
  {
    label: '密码',
    field: 'password',
    required: true,
    component: 'InputPassword',
    ifShow: ({ values }) => values.auth_type == 2,
  },
];

export const mongodbFormSchema: FormSchema[] = [
  {
    label: '服务器',
    field: 'host',
    required: true,
    component: 'Input',
  },
  {
    label: '端口',
    field: 'port',
    required: true,
    component: 'InputNumber',
  },
  {
    label: '用户名',
    field: 'username',
    required: true,
    component: 'Input',
  },
  {
    label: '密码',
    field: 'password',
    required: true,
    component: 'InputPassword',
  },
  {
    label: '数据库',
    field: 'database_name',
    required: true,
    component: 'Input',
  },
];

export const neo4jFormSchema: FormSchema[] = [
  {
    label: '服务器',
    field: 'host',
    required: true,
    component: 'Input',
  },
  {
    label: '端口',
    field: 'port',
    required: true,
    component: 'InputNumber',
  },
  {
    label: '用户名',
    field: 'username',
    required: true,
    component: 'Input',
  },
  {
    label: '密码',
    field: 'password',
    required: true,
    component: 'InputPassword',
  },
];

export const influxdbFormSchema: FormSchema[] = [
  {
    label: '服务器',
    field: 'host',
    required: true,
    component: 'Input',
  },
  {
    label: '端口',
    field: 'port',
    required: true,
    component: 'InputNumber',
  },
  {
    label: '用户名',
    field: 'username',
    required: true,
    component: 'Input',
  },
  {
    label: '密码',
    field: 'password',
    required: true,
    component: 'InputPassword',
  },
  {
    label: '数据库',
    field: 'database',
    required: true,
    component: 'Input',
  },
];

export const prometheusFormSchema: FormSchema[] = [
  {
    label: '连接地址',
    field: 'url',
    required: true,
    component: 'Input',
  },
];

export const kafkaFormSchema: FormSchema[] = [
  {
    label: '连接地址',
    field: 'bootstrap_servers',
    required: true,
    component: 'Input',
  },
];
