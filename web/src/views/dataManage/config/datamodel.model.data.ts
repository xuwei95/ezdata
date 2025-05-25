//表单数据
import { FormSchema } from '/@/components/Form';
export const akshareSchema: FormSchema[] = [
  {
    label: '数据接口函数',
    field: 'method',
    required: true,
    component: 'JDictSelectTag',
    componentProps: {
      showSearch: true,
      dictCode: 'akshare_method',
      placeholder: '请选择数据接口函数',
      stringToNumber: false,
    },
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    defaultValue: 'query,extract',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
      ],
    },
  },
];

export const ccxtSchema: FormSchema[] = [
  {
    label: '交易所',
    field: 'exchange_id',
    required: true,
    component: 'Input',
    defaultValue: 'okx',
  },
  {
    label: '数据接口函数',
    field: 'method',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'fetch_ohlcv',
    componentProps: {
      options: [
        { label: '指定交易对和时间段的历史K线数据', value: 'fetch_ohlcv' },
        { label: '所有市场（交易对）的详情', value: 'load_markets' },
        { label: '指定交易对的市场行情信息', value: 'fetch_ticker' },
        { label: '指定交易对的最近交易记录', value: 'fetch_trades' },
        { label: '指定交易对的订单簿信息', value: 'fetch_order_book' },
        { label: '交易所的状态信息', value: 'fetch_status' },
      ],
    },
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    defaultValue: 'query,extract',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
      ],
    },
  },
];

export const httpSchema: FormSchema[] = [
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    defaultValue: 'query,extract',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
      ],
    },
  },
];

export const fileTableSchema: FormSchema[] = [
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    defaultValue: 'query,extract',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
        // {
        //   label: '数据装载',
        //   value: 'load',
        // },
      ],
    },
  },
];

export const redisKeySchema: FormSchema[] = [
  {
    label: 'redis_key',
    field: 'redis_key',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    defaultValue: 'query,extract',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
        {
          label: '数据装载',
          value: 'load',
        },
      ],
    },
  },
];

export const minioTableSchema: FormSchema[] = [
  {
    label: '文件名',
    field: 'name',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    defaultValue: 'query,extract',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
        {
          label: '数据装载',
          value: 'load',
        },
      ],
    },
  },
];

export const SqlSchema: FormSchema[] = [
  {
    label: '查询语句',
    field: 'sql',
    required: true,
    defaultValue: '',
    component: 'MonacoEditor',
    componentProps: {
      language: 'sql',
    },
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    defaultValue: 'query,extract',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '自定义sql查询',
          value: 'custom_sql',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
      ],
    },
  },
];

export const baseTableSchema: FormSchema[] = [
  {
    label: '表名',
    field: 'name',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '创建',
          value: 'create',
        },
        {
          label: '操作字段',
          value: 'edit_fields',
        },
        {
          label: '删除',
          value: 'delete',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
        {
          label: '数据装载',
          value: 'load',
        },
        {
          label: '添加数据',
          value: 'add_data',
        },
        {
          label: '修改数据',
          value: 'edit_data',
        },
        {
          label: '删除数据',
          value: 'delete_data',
        },
      ],
    },
  },
];

export const mysqlBinlogSchema: FormSchema[] = [
  {
    label: '监听数据库',
    field: 'listen_dbs',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '监听表',
    field: 'listen_tables',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '监听操作',
    field: 'only_events',
    required: true,
    component: 'JCheckbox',
    componentProps: {
      options: [
        {
          label: '写入',
          value: 'write',
        },
        {
          label: '更新',
          value: 'update',
        },
        {
          label: '删除',
          value: 'delete',
        },
      ],
    },
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    componentProps: {
      options: [
        {
          label: '数据抽取',
          value: 'extract',
        },
      ],
    },
  },
];

export const ckTableSchema: FormSchema[] = [
  {
    label: '表名',
    field: 'name',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '表引擎',
    field: 'engine',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'MergeTree',
    componentProps: {
      options: [
        { label: 'MergeTree', value: 'MergeTree', key: '1' },
        { label: 'ReplacingMergeTree', value: 'ReplacingMergeTree', key: '2' },
      ],
    },
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '创建',
          value: 'create',
        },
        {
          label: '操作字段',
          value: 'edit_fields',
        },
        {
          label: '删除',
          value: 'delete',
        },
        {
          label: '添加数据',
          value: 'add_data',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
        {
          label: '数据装载',
          value: 'load',
        },
      ],
    },
  },
];

export const esIndexSchema: FormSchema[] = [
  {
    label: '索引名',
    field: 'name',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '允许操作',
    field: 'auth_type',
    required: true,
    component: 'JCheckbox',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '创建',
          value: 'create',
        },
        {
          label: '操作字段',
          value: 'edit_fields',
        },
        {
          label: '删除',
          value: 'delete',
        },
        {
          label: '添加数据',
          value: 'add_data',
        },
        {
          label: '修改数据',
          value: 'edit_data',
        },
        {
          label: '删除数据',
          value: 'delete_data',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
        {
          label: '数据装载',
          value: 'load',
        },
      ],
    },
  },
];

export const mongoCollectionSchema: FormSchema[] = [
  {
    label: '名称',
    field: 'name',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '创建',
          value: 'create',
        },
        {
          label: '操作字段',
          value: 'edit_fields',
        },
        {
          label: '删除',
          value: 'delete',
        },
        {
          label: '添加数据',
          value: 'add_data',
        },
        {
          label: '修改数据',
          value: 'edit_data',
        },
        {
          label: '删除数据',
          value: 'delete_data',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
        {
          label: '数据装载',
          value: 'load',
        },
      ],
    },
  },
];

export const neo4jGraphSchema: FormSchema[] = [
  {
    label: '名称',
    field: 'name',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '创建',
          value: 'create',
        },
        {
          label: '操作字段',
          value: 'edit_fields',
        },
        {
          label: '删除',
          value: 'delete',
        },
        {
          label: '添加数据',
          value: 'add_data',
        },
        {
          label: '修改数据',
          value: 'edit_data',
        },
        {
          label: '删除数据',
          value: 'delete_data',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
        {
          label: '数据装载',
          value: 'load',
        },
      ],
    },
  },
];

export const influxdbTableSchema: FormSchema[] = [
  {
    label: '名称',
    field: 'name',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '添加数据',
          value: 'add_data',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
        {
          label: '数据装载',
          value: 'load',
        },
      ],
    },
  },
];

export const prometheusMetricSchema: FormSchema[] = [
  {
    label: '指标名称',
    field: 'name',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '添加数据',
          value: 'add_data',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
        // {
        //   label: '数据装载',
        //   value: 'load',
        // },
      ],
    },
  },
];

export const prometheusPromqlSchema: FormSchema[] = [
  {
    label: 'promql',
    field: 'promql',
    required: true,
    defaultValue: '',
    component: 'MonacoEditor',
    componentProps: {
      language: 'promql',
    },
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    componentProps: {
      options: [
        {
          label: '查询',
          value: 'query',
        },
        {
          label: '自定义查询',
          value: 'custom_sql',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
      ],
    },
  },
];

export const kafkaTopicSchema: FormSchema[] = [
  {
    label: '主题',
    field: 'name',
    required: true,
    component: 'Input',
    defaultValue: '',
  },
  {
    label: '拓展参数',
    field: 'ext_params',
    required: true,
    component: 'MonacoEditor',
    defaultValue: '{}',
    componentProps: {
      language: 'json',
    },
  },
  {
    label: '允许操作',
    field: 'auth_type',
    component: 'JCheckbox',
    componentProps: {
      options: [
        {
          label: '创建',
          value: 'create',
        },
        {
          label: '数据抽取',
          value: 'extract',
        },
        {
          label: '数据装载',
          value: 'load',
        },
      ],
    },
  },
];
