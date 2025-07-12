import { BasicColumn } from '/@/components/Table';
import { FormSchema } from '/@/components/Table';
import { getAllRolesList, getAllDepartList, getAllTenantList } from './user.api';
import { rules } from '/@/utils/helper/validator';
import { render } from '/@/utils/common/renderUtils';
export const columns: BasicColumn[] = [
  {
    title: '用户账号',
    dataIndex: 'username',
    width: 120,
  },
  {
    title: '用户姓名',
    dataIndex: 'nickname',
    width: 100,
  },
  {
    title: '头像',
    dataIndex: 'avatar',
    width: 120,
    customRender: render.renderAvatar,
  },
  {
    title: '性别',
    dataIndex: 'sex_dictText',
    width: 80,
    sorter: true,
  },
  {
    title: '生日',
    dataIndex: 'birthday',
    width: 100,
  },
  {
    title: '手机号',
    dataIndex: 'phone',
    width: 100,
  },
  {
    title: '部门',
    width: 150,
    dataIndex: 'depart_id_list_text',
  },
  {
    title: '状态',
    dataIndex: 'status_dictText',
    width: 80,
  },
];

export const recycleColumns: BasicColumn[] = [
  {
    title: '用户账号',
    dataIndex: 'username',
    width: 100,
  },
  {
    title: '用户姓名',
    dataIndex: 'nickname',
    width: 100,
  },
  {
    title: '头像',
    dataIndex: 'avatar',
    width: 80,
    customRender: render.renderImage,
  },
  {
    title: '性别',
    dataIndex: 'sex',
    width: 80,
    sorter: true,
    customRender: ({ text }) => {
      return render.renderDict(text, 'sex');
    },
  },
];

export const searchFormSchema: FormSchema[] = [
  {
    label: '账号',
    field: 'username',
    component: 'Input',
    colProps: { span: 6 },
  },
  // {
  //   label: '性别',
  //   field: 'sex',
  //   component: 'JDictSelectTag',
  //   componentProps: {
  //     dictCode: 'sex',
  //     placeholder: '请选择性别',
  //     stringToNumber: true,
  //   },
  //   colProps: { span: 6 },
  // },
  {
    label: '真实名称',
    field: 'nickname',
    component: 'Input',
    colProps: { span: 6 },
  },
  {
    label: '手机号码',
    field: 'phone',
    component: 'Input',
    colProps: { span: 6 },
  },
  {
    label: '用户状态',
    field: 'status',
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'user_status',
      placeholder: '请选择状态',
      stringToNumber: true,
    },
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
    label: '用户账号',
    field: 'username',
    component: 'Input',
    required: true,
    dynamicDisabled: ({ values }) => {
      return !!values.id;
    },
    // dynamicRules: ({ model, schema }) => rules.duplicateCheckRule('sys_user', 'username', model, schema, true),
  },
  {
    label: '登录密码',
    field: 'password',
    component: 'StrengthMeter',
    rules: [
      {
        required: true,
        message: '请输入登录密码',
      },
    ],
  },
  {
    label: '确认密码',
    field: 'confirmPassword',
    component: 'InputPassword',
    dynamicRules: ({ values }) => rules.confirmPassword(values, true),
  },
  {
    label: '用户姓名',
    field: 'nickname',
    required: true,
    component: 'Input',
  },
  {
    label: '工号',
    field: 'work_no',
    required: true,
    component: 'Input',
    // dynamicRules: ({ model, schema }) => rules.duplicateCheckRule('sys_user', 'work_no', model, schema, true),
  },
  {
    label: '职务',
    field: 'post_id_list',
    required: false,
    component: 'JSelectPosition',
    componentProps: {
      rowKey: 'code',
      labelKey: 'name',
    },
  },
  {
    label: '角色',
    field: 'role_id_list',
    component: 'ApiSelect',
    componentProps: {
      mode: 'multiple',
      api: getAllRolesList,
      labelField: 'role_name',
      valueField: 'id',
    },
  },
  {
    label: '所属部门',
    field: 'depart_id_list',
    component: 'ApiSelect',
    componentProps: {
      mode: 'multiple',
      api: getAllDepartList,
      labelField: 'depart_name',
      valueField: 'id',
    },
  },
  // {
  //   label: '所属部门',
  //   field: 'depart_id_list',
  //   component: 'JSelectDept',
  //   componentProps: ({ formActionType, formModel }) => {
  //     return {
  //       sync: false,
  //       checkStrictly: true,
  //       defaultExpandLevel: 2,
  //
  //       onSelect: (options, values) => {
  //         const { updateSchema } = formActionType;
  //         //所属部门修改后更新负责部门下拉框数据
  //         updateSchema([
  //           {
  //             field: 'depart_id_list',
  //             componentProps: { options },
  //           },
  //         ]);
  //         //所属部门修改后更新负责部门数据
  //         formModel.depart_id_list && (formModel.depart_id_list = formModel.depart_id_list.filter((item) => values.value.indexOf(item) > -1));
  //       },
  //     };
  //   },
  // },
  {
    label: '租户',
    field: 'tenant_id_list',
    component: 'ApiSelect',
    componentProps: {
      mode: 'multiple',
      api: getAllTenantList,
      numberToString: true,
      labelField: 'name',
      valueField: 'id',
    },
  },
  {
    label: '身份',
    field: 'user_identity',
    component: 'RadioGroup',
    defaultValue: 1,
    componentProps: ({ formModel }) => {
      return {
        options: [
          { label: '普通用户', value: 1, key: '1' },
          { label: '上级', value: 2, key: '2' },
        ],
        onChange: () => {
          formModel.userIdentity == 1 && (formModel.depart_id_list = []);
        },
      };
    },
  },
  {
    label: '负责部门',
    field: 'depart_id_list',
    component: 'Select',
    componentProps: {
      mode: 'multiple',
    },
    ifShow: ({ values }) => values.userIdentity == 2,
  },
  {
    label: '头像',
    field: 'avatar',
    component: 'JImageUpload',
    componentProps: {
      fileMax: 1,
    },
  },
  {
    label: '生日',
    field: 'birthday',
    component: 'DatePicker',
  },
  {
    label: '性别',
    field: 'sex',
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'sex',
      placeholder: '请选择性别',
      stringToNumber: true,
    },
  },
  {
    label: '邮箱',
    field: 'email',
    component: 'Input',
    rules: rules.rule('email', false),
  },
  {
    label: '手机号码',
    field: 'phone',
    component: 'Input',
    rules: [{ pattern: /^1[3|4|5|7|8|9][0-9]\d{8}$/, message: '手机号码格式有误' }],
    // dynamicRules: ({ model, schema }) => {
    //   return [
    //     { ...rules.duplicateCheckRule('sys_user', 'phone', model, schema, true)[0] },
    //     { pattern: /^1[3|4|5|7|8|9][0-9]\d{8}$/, message: '手机号码格式有误' },
    //   ];
    // },
  },
];

export const formPasswordSchema: FormSchema[] = [
  {
    label: '用户账号',
    field: 'username',
    component: 'Input',
    componentProps: { readOnly: true },
  },
  {
    label: '登录密码',
    field: 'password',
    component: 'StrengthMeter',
    componentProps: {
      placeholder: '请输入登录密码',
    },
    rules: [
      {
        required: true,
        message: '请输入登录密码',
      },
    ],
  },
  {
    label: '确认密码',
    field: 'confirmPassword',
    component: 'InputPassword',
    dynamicRules: ({ values }) => rules.confirmPassword(values, true),
  },
];

export const formAgentSchema: FormSchema[] = [
  {
    label: '',
    field: 'id',
    component: 'Input',
    show: false,
  },
  {
    field: 'username',
    label: '用户名',
    component: 'Input',
    componentProps: {
      readOnly: true,
      allowClear: false,
    },
  },
  {
    field: 'agentUserName',
    label: '代理人用户名',
    required: true,
    component: 'JSelectUser',
    componentProps: {
      rowKey: 'username',
      labelKey: 'realname',
      maxSelectCount: 10,
    },
  },
  {
    field: 'startTime',
    label: '代理开始时间',
    component: 'DatePicker',
    required: true,
    componentProps: {
      showTime: true,
      valueFormat: 'YYYY-MM-DD HH:mm:ss',
      placeholder: '请选择代理开始时间',
    },
  },
  {
    field: 'endTime',
    label: '代理结束时间',
    component: 'DatePicker',
    required: true,
    componentProps: {
      showTime: true,
      valueFormat: 'YYYY-MM-DD HH:mm:ss',
      placeholder: '请选择代理结束时间',
    },
  },
  {
    field: 'status',
    label: '状态',
    component: 'JDictSelectTag',
    defaultValue: '1',
    componentProps: {
      dictCode: 'valid_status',
      type: 'radioButton',
    },
  },
];
