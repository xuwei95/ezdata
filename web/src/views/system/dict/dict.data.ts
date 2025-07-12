import { BasicColumn } from '/@/components/Table';
import { FormSchema } from '/@/components/Table';
// import { dictItemCheck } from './dict.api';
// import { rules } from '/@/utils/helper/validator';
export const columns: BasicColumn[] = [
  {
    title: '字典名称',
    dataIndex: 'dict_name',
    width: 240,
  },
  {
    title: '字典编码',
    dataIndex: 'dict_code',
    width: 240,
  },
  {
    title: '描述',
    dataIndex: 'description',
    // width: 120
  },
];

export const recycleBincolumns: BasicColumn[] = [
  {
    title: '字典名称',
    dataIndex: 'dict_name',
    width: 120,
  },
  {
    title: '字典编号',
    dataIndex: 'dict_code',
    width: 120,
  },
  {
    title: '描述',
    dataIndex: 'description',
    width: 120,
  },
];

export const searchFormSchema: FormSchema[] = [
  {
    label: '字典名称',
    field: 'dict_name',
    component: 'Input',
    colProps: { span: 6 },
  },
  {
    label: '字典编码',
    field: 'dict_code',
    component: 'Input',
    colProps: { span: 6 },
  },
];

export const formSchema: FormSchema[] = [
  {
    label: '',
    field: 'id',
    component: 'Input',
    show: false,
  },
  {
    label: '字典名称',
    field: 'dict_name',
    required: true,
    component: 'Input',
  },
  {
    label: '字典编码',
    field: 'dict_code',
    component: 'Input',
    dynamicDisabled: ({ values }) => {
      return !!values.id;
    },
    required: true,
    // dynamicRules: ({ model, schema }) => rules.duplicateCheckRule('sys_dict', 'dict_code', model, schema, true),
  },
  {
    label: '描述',
    field: 'description',
    component: 'Input',
  },
];

export const dictItemColumns: BasicColumn[] = [
  {
    title: '名称',
    dataIndex: 'name',
    width: 80,
  },
  {
    title: '数据值',
    dataIndex: 'value',
    width: 80,
  },
  {
    title: '拓展参数',
    dataIndex: 'extend',
    width: 180,
  },
];

export const dictItemSearchFormSchema: FormSchema[] = [
  {
    label: '名称',
    field: 'name',
    component: 'Input',
  },
  {
    label: '状态',
    field: 'status',
    component: 'JSelectInput',
    componentProps: {
      options: [
        { label: '启用', value: 1 },
        { label: '禁用', value: 0 },
      ],
    },
  },
];

export const itemFormSchema: FormSchema[] = [
  {
    label: '',
    field: 'id',
    component: 'Input',
    show: false,
  },
  {
    label: '名称',
    field: 'name',
    required: true,
    component: 'Input',
  },
  {
    label: '数据值',
    field: 'value',
    component: 'Input',
    required: true,
    // dynamicRules: ({ values, model }) => {
    //   return [
    //     {
    //       required: true,
    //       validator: (_, value) => {
    //         if (!value) {
    //           return Promise.reject('请输入数据值');
    //         }
    //         if (new RegExp("[`~!@#$^&*()=|{}'.<>《》/?！￥（）—【】‘；：”“。，、？]").test(value)) {
    //           return Promise.reject('数据值不能包含特殊字符！');
    //         }
    //         return new Promise<void>((resolve, reject) => {
    //           let params = {
    //             dictId: values.dictId,
    //             id: model.id,
    //             itemValue: value,
    //           };
    //           dictItemCheck(params)
    //             .then((res) => {
    //               res.success ? resolve() : reject(res.message || '校验失败');
    //             })
    //             .catch((err) => {
    //               reject(err.message || '验证失败');
    //             });
    //         });
    //       },
    //     },
    //   ];
    // },
  },
  {
    label: '描述',
    field: 'description',
    component: 'Input',
  },
  {
    field: 'sort_no',
    label: '排序',
    component: 'InputNumber',
    defaultValue: 1,
  },
  {
    field: 'status',
    label: '是否启用',
    defaultValue: 1,
    component: 'JDictSelectTag',
    componentProps: {
      type: 'radioButton',
      dictCode: 'dict_item_status',
      stringToNumber: true,
    },
  },
  {
    label: '拓展参数',
    field: 'extend',
    component: 'MonacoEditor',
    defaultValue: '{}',
    componentProps: {
      language: 'json',
    },
  },
];
