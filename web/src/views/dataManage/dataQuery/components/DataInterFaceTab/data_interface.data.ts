import { BasicColumn, FormSchema } from '/@/components/Table';
//列表数据
export const columns: BasicColumn[] = [
  {
    title: '接口名称',
    align: 'center',
    dataIndex: 'name',
  },
  {
    title: 'api_key',
    align: 'center',
    dataIndex: 'api_key',
    width: 300,
  },
  {
    title: '状态',
    align: 'center',
    dataIndex: 'status',
    customRender: ({ text }) => {
      return text == 1 ? '启用' : '禁用';
    },
  },
  {
    title: '描述',
    align: 'center',
    dataIndex: 'description',
  },
  {
    title: '失效时间',
    align: 'center',
    dataIndex: 'valid_time',
  },
  {
    title: '申请人',
    align: 'center',
    dataIndex: 'apply_user',
  },
  {
    title: '申请时间',
    align: 'center',
    dataIndex: 'apply_time',
  },
  {
    title: '审核人',
    align: 'center',
    dataIndex: 'review_user',
  },
  {
    title: '审核时间',
    align: 'center',
    dataIndex: 'review_time',
  },
];
//查询数据
export const searchFormSchema: FormSchema[] = [];
//表单数据
export const formApplySchema: FormSchema[] = [
  {
    label: '接口名称',
    field: 'name',
    required: true,
    component: 'Input',
  },
  // {
  //   label: '字段列表',
  //   field: 'valid_fields',
  //   required: true,
  //   component: 'JSelectMultiple',
  //   defaultValue: '*',
  //   componentProps: {
  //     options: [
  //       { label: '全部字段', value: '*' },
  //     ],
  //   },
  // },
  {
    label: '申请时长',
    field: 'apply_time_length',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'forever',
    componentProps: {
      options: [
        { label: '永久', value: 'forever' },
        { label: '5分钟', value: '300s' },
        { label: '一小时', value: '1h' },
        { label: '一天', value: '1d' },
        { label: '一周', value: '1W' },
        { label: '1月', value: '1M' },
        { label: '1年', value: '1Y' },
      ],
    },
  },
  {
    label: '申请说明',
    field: 'apply_caption',
    required: false,
    component: 'InputTextArea',
    defaultValue: '',
  },
  // TODO 主键隐藏字段，目前写死为ID
  {
    label: '',
    field: 'id',
    component: 'Input',
    show: false,
  },
];

//表单数据
export const formReviewSchema: FormSchema[] = [
  {
    label: '接口名称',
    field: 'name',
    required: true,
    component: 'Input',
  },
  // {
  //   label: '字段列表',
  //   field: 'valid_fields',
  //   required: true,
  //   component: 'JSelectMultiple',
  //   defaultValue: '*',
  //   componentProps: {
  //     options: [
  //       { label: '全部字段', value: '*' },
  //     ],
  //   },
  // },
  {
    label: '审核时长',
    field: 'review_time_length',
    required: true,
    component: 'JSelectInput',
    defaultValue: '1d',
    componentProps: {
      options: [
        { label: '永久', value: 'forever' },
        { label: '5分钟', value: '300s' },
        { label: '一天', value: '1d' },
        { label: '一周', value: '1W' },
        { label: '1月', value: '1M' },
        { label: '1年', value: '1Y' },
      ],
    },
  },
  {
    label: '审核说明',
    field: 'review_caption',
    required: false,
    component: 'InputTextArea',
    defaultValue: '',
  },
  // TODO 主键隐藏字段，目前写死为ID
  {
    label: '',
    field: 'id',
    component: 'Input',
    show: false,
  },
];

//表单数据
export const formSchema: FormSchema[] = [
  {
    label: '接口名称',
    field: 'name',
    required: true,
    component: 'Input',
  },
  {
    label: '字段列表',
    field: 'valid_fields',
    required: true,
    component: 'JSelectMultiple',
    defaultValue: '*',
    componentProps: {
      options: [
        { label: '全部字段', value: '*' },
      ],
    },
  },
  {
    label: '申请时长',
    field: 'apply_time_length',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'forever',
    componentProps: {
      options: [
        { label: '永久', value: 'forever' },
        { label: '一小时', value: '1h' },
        { label: '一天', value: '1d' },
        { label: '一周', value: '1W' },
        { label: '1月', value: '1M' },
        { label: '1年', value: '1Y' },
      ],
    },
  },
  {
    label: '申请说明',
    field: 'apply_caption',
    required: false,
    component: 'InputTextArea',
    defaultValue: '',
  },
  {
    label: '审核时长',
    field: 'review_time_length',
    required: true,
    component: 'JSelectInput',
    defaultValue: '1d',
    componentProps: {
      options: [
        { label: '永久', value: 'forever' },
        { label: '5分钟', value: '300s' },
        { label: '一天', value: '1d' },
        { label: '一周', value: '1W' },
        { label: '1月', value: '1M' },
        { label: '1年', value: '1Y' },
      ],
    },
  },
  {
    label: '审核说明',
    field: 'review_caption',
    required: false,
    component: 'InputTextArea',
    defaultValue: '',
  },
  // TODO 主键隐藏字段，目前写死为ID
  {
    label: '',
    field: 'id',
    component: 'Input',
    show: false,
  },
];
