import { BasicColumn } from '/@/components/Table';
import { FormSchema } from '/@/components/Table';
import { h } from 'vue';
import { Icon } from '/@/components/Icon';
// import { duplicateCheck } from '../user/user.api';
import { ajaxGetDictItems } from './menu.api';
import { render } from '/@/utils/common/renderUtils';
// import { Select } from 'ant-design-vue';
// import { rules } from '/@/utils/helper/validator';

const isDir = (type) => type === 0;
const isMenu = (type) => type === 1;
const isButton = (type) => type === 2;

// 定义可选择的组件类型
export enum ComponentTypes {
  Default = 'layouts/default/index',
  IFrame = 'sys/iframe/FrameBlank',
}

export const columns: BasicColumn[] = [
  {
    title: '菜单名称',
    dataIndex: 'name',
    width: 200,
    align: 'left',
  },
  {
    title: '菜单类型',
    dataIndex: 'menu_type',
    width: 150,
    customRender: ({ text }) => {
      return render.renderDict(text, 'menu_type');
    },
  },
  {
    title: '图标',
    dataIndex: 'icon',
    width: 50,
    customRender: ({ record }) => {
      // @ts-ignore
      return h(Icon, { icon: record.icon });
    },
  },
  {
    title: '组件',
    dataIndex: 'component',
    align: 'left',
    width: 150,
  },
  {
    title: '路径',
    dataIndex: 'url',
    align: 'left',
    width: 150,
  },
  {
    title: '排序',
    dataIndex: 'sort_no',
    width: 50,
  },
];

export const searchFormSchema: FormSchema[] = [
  {
    field: 'name',
    label: '菜单名称',
    component: 'Input',
    colProps: { span: 8 },
  },
];

export const formSchema: FormSchema[] = [
  {
    label: 'id',
    field: 'id',
    component: 'Input',
    show: false,
  },
  {
    field: 'menu_type',
    label: '菜单类型',
    component: 'RadioButtonGroup',
    defaultValue: 0,
    componentProps: ({ formActionType, formModel }) => {
      return {
        options: [
          { label: '一级菜单', value: 0 },
          { label: '子菜单', value: 1 },
          { label: '按钮/权限', value: 2 },
        ],
        onChange: (e) => {
          const { updateSchema, clearValidate } = formActionType;
          const label = isButton(e) ? '按钮/权限' : '菜单名称';
          //清除校验
          clearValidate();
          updateSchema([
            {
              field: 'name',
              label: label,
            },
            {
              field: 'url',
              required: !isButton(e),
            },
          ]);
          //update-begin---author:wangshuai ---date:20220729  for：[VUEN-1834]只有一级菜单，才默认值，子菜单的时候，清空------------
          if (isMenu(e) && !formModel.id && formModel.component === 'layouts/RouteView') {
            formModel.component = '';
          }
          //update-end---author:wangshuai ---date:20220729  for：[VUEN-1834]只有一级菜单，才默认值，子菜单的时候，清空------------
        },
      };
    },
  },
  {
    field: 'name',
    label: '菜单名称',
    component: 'Input',
    required: true,
  },
  {
    field: 'parent_id',
    label: '上级菜单',
    component: 'TreeSelect',
    required: true,
    componentProps: {
      replaceFields: {
        title: 'name',
        key: 'id',
        value: 'id',
      },
      dropdownStyle: {
        maxHeight: '50vh',
      },
      getPopupContainer: (node) => node.parentNode,
    },
    ifShow: ({ values }) => !isDir(values.menu_type),
  },
  {
    field: 'url',
    label: '访问路径',
    component: 'Input',
    required: true,
    ifShow: ({ values }) => !(values.component === ComponentTypes.IFrame && values.internalOrExternal) && values.menu_type !== 2,
    // dynamicRules: ({ model, schema }) => {
    //   return rules.duplicateCheckRule('sys_permission', 'url', model, schema, true);
    // },
  },
  {
    field: 'component',
    label: '前端组件',
    component: 'Input',
    componentProps: {
      placeholder: '请输入前端组件',
    },
    defaultValue: 'layouts/RouteView',
    required: true,
    ifShow: ({ values }) => !isButton(values.menu_type),
  },
  {
    field: 'component_name',
    label: '组件名称',
    component: 'Input',
    componentProps: {
      placeholder: '请输入组件名称',
    },
    helpMessage: [
      '此处名称应和vue组件的name属性保持一致。',
      '组件名称不能重复，主要用于路由缓存功能。',
      '如果组件名称和vue组件的name属性不一致，则会导致路由缓存失效。',
      '非必填，留空则会根据访问路径自动生成。',
    ],
    defaultValue: '',
    ifShow: ({ values }) => !isButton(values.menu_type),
  },
  {
    field: 'frame_src',
    label: 'Iframe地址',
    component: 'Input',
    rules: [
      { required: true, message: '请输入Iframe地址' },
      { type: 'url', message: '请输入正确的url地址' },
    ],
    ifShow: ({ values }) => !isButton(values.menu_type) && values.component === ComponentTypes.IFrame,
  },
  {
    field: 'redirect',
    label: '默认跳转地址',
    component: 'Input',
    ifShow: ({ values }) => isDir(values.menu_type),
  },
  {
    field: 'perms',
    label: '授权标识',
    component: 'Input',
    ifShow: ({ values }) => isButton(values.menu_type),
    // dynamicRules: ({ model }) => {
    //   return [
    //     {
    //       required: false,
    //       validator: (_, value) => {
    //         return new Promise((resolve, reject) => {
    //           let params = {
    //             tableName: 'sys_permission',
    //             fieldName: 'perms',
    //             fieldVal: value,
    //             dataId: model.id,
    //           };
    //           duplicateCheck(params)
    //             .then((res) => {
    //               res.success ? resolve() : reject(res.message || '校验失败');
    //             })
    //             .catch((err) => {
    //               reject(err.message || '校验失败');
    //             });
    //         });
    //       },
    //     },
    //   ];
    // },
  },
  {
    field: 'perms_type',
    label: '授权策略',
    component: 'RadioGroup',
    defaultValue: '1',
    helpMessage: ['可见/可访问(授权后可见/可访问)', '可编辑(未授权时禁用)'],
    componentProps: {
      options: [
        { label: '可见/可访问', value: '1' },
        { label: '可编辑', value: '2' },
      ],
    },
    ifShow: ({ values }) => isButton(values.menu_type),
  },
  {
    field: 'status',
    label: '状态',
    component: 'RadioGroup',
    defaultValue: '1',
    componentProps: {
      options: [
        { label: '有效', value: '1' },
        { label: '无效', value: '0' },
      ],
    },
    ifShow: ({ values }) => isButton(values.menu_type),
  },
  {
    field: 'icon',
    label: '菜单图标',
    component: 'Input',
    // component: 'IconPicker',
    // componentProps: {
    //   mode: 'svg',
    // },
    ifShow: ({ values }) => !isButton(values.menu_type),
  },
  {
    field: 'sort_no',
    label: '排序',
    component: 'InputNumber',
    defaultValue: 1,
    ifShow: ({ values }) => !isButton(values.menu_type),
  },
  {
    field: 'route',
    label: '是否路由菜单',
    component: 'Switch',
    defaultValue: true,
    componentProps: {
      checkedChildren: '是',
      unCheckedChildren: '否',
    },
    ifShow: ({ values }) => !isButton(values.menu_type),
  },
  {
    field: 'hidden',
    label: '隐藏路由',
    component: 'Switch',
    defaultValue: 0,
    componentProps: {
      checkedChildren: '是',
      unCheckedChildren: '否',
    },
    ifShow: ({ values }) => !isButton(values.menu_type),
  },
  {
    field: 'hide_tab',
    label: '隐藏Tab',
    component: 'Switch',
    defaultValue: 0,
    componentProps: {
      checkedChildren: '是',
      unCheckedChildren: '否',
    },
    ifShow: ({ values }) => !isButton(values.menu_type),
  },
  {
    field: 'keep_alive',
    label: '是否缓存路由',
    component: 'Switch',
    defaultValue: false,
    componentProps: {
      checkedChildren: '是',
      unCheckedChildren: '否',
    },
    ifShow: ({ values }) => !isButton(values.menu_type),
  },
  {
    field: 'always_show',
    label: '聚合路由',
    component: 'Switch',
    defaultValue: false,
    componentProps: {
      checkedChildren: '是',
      unCheckedChildren: '否',
    },
    ifShow: ({ values }) => !isButton(values.menu_type),
  },
  {
    field: 'internal_or_external',
    label: '打开方式',
    component: 'Switch',
    defaultValue: false,
    componentProps: {
      checkedChildren: '外部',
      unCheckedChildren: '内部',
    },
    ifShow: ({ values }) => !isButton(values.menu_type),
  },
];

export const dataRuleColumns: BasicColumn[] = [
  {
    title: '规则名称',
    dataIndex: 'rule_name',
    width: 150,
  },
  {
    title: '规则字段',
    dataIndex: 'rule_column',
    width: 100,
  },
  {
    title: '规则值',
    dataIndex: 'rule_value',
    width: 100,
  },
];

export const dataRuleSearchFormSchema: FormSchema[] = [
  {
    field: 'rule_name',
    label: '规则名称',
    component: 'Input',
    colProps: { span: 6 },
  },
  {
    field: 'rule_value',
    label: '规则值',
    component: 'Input',
    colProps: { span: 6 },
  },
];

export const dataRuleFormSchema: FormSchema[] = [
  {
    label: 'id',
    field: 'id',
    component: 'Input',
    show: false,
  },
  {
    field: 'rule_name',
    label: '规则名称',
    component: 'Input',
    required: true,
  },
  {
    field: 'rule_column',
    label: '规则字段',
    component: 'Input',
    ifShow: ({ values }) => {
      return values.ruleConditions !== 'USE_SQL_RULES';
    },
  },
  {
    field: 'rule_conditions',
    label: '条件规则',
    required: true,
    component: 'ApiSelect',
    componentProps: {
      api: ajaxGetDictItems,
      params: { code: 'rule_conditions' },
      labelField: 'text',
      valueField: 'value',
      getPopupContainer: () => document.body,
    },
  },
  {
    field: 'rule_value',
    label: '规则值',
    component: 'Input',
    required: true,
  },
  {
    field: 'status',
    label: '状态',
    component: 'RadioButtonGroup',
    defaultValue: '1',
    componentProps: {
      options: [
        { label: '无效', value: '0' },
        { label: '有效', value: '1' },
      ],
    },
  },
];
