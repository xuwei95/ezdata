import { BasicColumn, FormSchema } from '/@/components/Table';
import { render } from "/@/utils/common/renderUtils";
import { rules } from '/@/utils/helper/validator';
import { getAllDepartList } from '@/views/system/user/user.api';
//列表数据
export const columns: BasicColumn[] = [
  {
    title: '主键',
    align: 'center',
    dataIndex: 'id',
    defaultHidden: true,
  },
  {
    title: '名称',
    align: 'center',
    dataIndex: 'name',
  },
  {
    title: '类型',
    align: 'center',
    dataIndex: 'type',
  },
  {
    title: '状态',
    align: 'center',
    dataIndex: 'state',
    customRender: ({ text }) => {
      return text == 1 ? '启用' : '禁用';
    },
  },
  {
    title: '简介',
    align: 'center',
    dataIndex: 'description',
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
  },
];
//查询数据
export const searchFormSchema: FormSchema[] = [
  {
    label: '名称',
    field: 'name',
    component: 'Input',
  },
  {
    label: '类型',
    field: 'type',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'chat',
    componentProps: {
      options: [
        { label: '对话应用', value: 'chat' },
      ],
    },
  },
  {
    label: '关键词',
    field: 'content',
    component: 'Input',
  },
  {
    label: '状态',
    field: 'status',
    component: 'RadioGroup',
    defaultValue: 1,
    componentProps: {
      options: [
        { label: '启用', value: 1 },
        { label: '禁用', value: 0 },
      ],
    },
  },
];
//表单数据
export const formSchema: FormSchema[] = [
  {
    label: '名称',
    field: 'name',
    required: false,
    component: 'Input',
  },
  {
    label: '图标',
    field: 'icon',
    required: false,
    component: 'JImageUpload',
    componentProps: {
      fileMax: 1,
    },
  },
  {
    label: '类型',
    field: 'type',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'chat',
    componentProps: {
      options: [
        { label: '对话应用', value: 'chat' },
      ],
    },
  },
  {
    label: '状态',
    field: 'state',
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
    label: '所属用户组',
    field: 'depart_list',
    component: 'ApiSelect',
    required: false,
    componentProps: {
      width: '300px',
      mode: 'multiple',
      api: getAllDepartList,
      labelField: 'depart_name',
      valueField: 'org_code',
    },
  },
  {
    label: '简介',
    field: 'description',
    required: false,
    component: 'InputTextArea',
  },
  {
    label: '对话配置', // 对话配置
    field: 'chat_config',
    slot: 'chat_config',
    component: 'InputTextArea',
    defaultValue: {},
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
