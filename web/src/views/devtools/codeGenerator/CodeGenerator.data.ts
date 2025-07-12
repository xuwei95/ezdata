import { BasicColumn, FormSchema } from '/@/components/Table';
import { JVxeColumn, JVxeTypes } from "/@/components/jeecg/JVxeTable/src/types";
import {render} from "/@/utils/common/renderUtils";
// import { rules } from '/@/utils/helper/validator';
// import { render } from '/@/utils/common/renderUtils';
//列表数据
export const columns: BasicColumn[] = [
  {
    title: '项目名称',
    align: 'center',
    dataIndex: 'title',
  },
  {
    title: '模块文件名称',
    align: 'center',
    dataIndex: 'module_name',
  },
  {
    title: '模型名称',
    align: 'center',
    dataIndex: 'model_name',
  },
  {
    title: '模型值',
    align: 'center',
    dataIndex: 'model_value',
  },
  {
    title: '模型类型',
    align: 'center',
    dataIndex: 'model_type',
    customRender: ({ text }) => {
      return render.renderDict(text, 'code_gen_model_type');
    },
  },
  {
    title: '表名',
    align: 'center',
    dataIndex: 'table_name',
  },
  {
    title: '表描述',
    align: 'center',
    dataIndex: 'table_desc',
  },
  {
    title: '是否已同步数据库',
    align: 'center',
    dataIndex: 'is_sync',
    customRender: ({ text }) => {
      return text == 1 ? '是' : '否';
    },
  },
];
//查询数据
export const searchFormSchema: FormSchema[] = [
  {
    label: '项目名称',
    field: 'title',
    component: 'JInput',
    colProps: { span: 6 },
  },
  {
    label: '是否同步',
    field: 'is_sync',
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'code_gen_sync_status',
      placeholder: '请选择同步状态',
      stringToNumber: true,
    },
    colProps: { span: 6 },
  },
  {
    label: '模块文件名称',
    field: 'module_name',
    component: 'Input',
    colProps: { span: 6 },
  },
  {
    label: '模型名称',
    field: 'model_name',
    component: 'Input',
    colProps: { span: 6 },
  },
  {
    label: '表名',
    field: 'table_name',
    component: 'Input',
    colProps: { span: 6 },
  },
  {
    label: '模型类型',
    field: 'model_type',
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'code_gen_model_type',
      placeholder: '请选择模型类型',
      stringToNumber: true,
    },
    colProps: { span: 6 },
  },
];
//表单数据
export const formSchema: FormSchema[] = [
  {
    label: '项目名称',
    field: 'title',
    component: 'Input',
    required: true,
  },
  {
    label: '模块名称',
    field: 'module_name',
    component: 'Input',
    required: true,
  },
  {
    label: 'api前缀',
    field: 'api_prefix',
    component: 'Input',
    required: true,
  },
  {
    label: '模型名称',
    field: 'model_name',
    component: 'Input',
    required: true,
  },
  {
    label: '模型值',
    field: 'model_value',
    component: 'Input',
    required: true,
  },
  {
    label: '继承基类',
    field: 'extend_base_model',
    defaultValue: 1,
    required: true,
    component: 'RadioGroup',
    componentProps: {
      options: [
        { label: '继承', value: 1, key: '1' },
        { label: '不继承', value: 2, key: '2' },
      ],
    },
  },
  {
    label: '表名',
    field: 'table_name',
    component: 'Input',
    required: true,
  },
  {
    label: '表描述',
    field: 'table_desc',
    component: 'Input',
  },
  {
    label: '模型类型',
    field: 'model_type',
    required: true,
    defaultValue: 1,
    component: 'JDictSelectTag',
    componentProps: {
      dictCode: 'code_gen_model_type',
      placeholder: '请选择模型类型',
      stringToNumber: true,
    },
    // colProps: { span: 6 },
  },
  {
    label: '表单风格',
    field: 'form_style',
    component: 'JSelectInput',
    defaultValue: 1,
    required: true,
    componentProps: {
      options: [
        { label: '一列', value: 1, key: '1' },
        { label: '两列', value: 2, key: '2' },
        { label: '三列', value: 3, key: '3' },
        { label: '四列', value: 4, key: '4' },
      ],
    },
  },
  {
    label: '前端类型',
    field: 'frontend_gen_type',
    component: 'JDictSelectTag',
    defaultValue: 1,
    required: true,
    componentProps: {
      dictCode: 'code_gen_frontend_type',
      placeholder: '请选择前端生成代码类型',
      stringToNumber: true,
    },
  },
  {
    label: '后端类型',
    field: 'backend_gen_type',
    component: 'JDictSelectTag',
    defaultValue: 1,
    required: true,
    componentProps: {
      dictCode: 'code_gen_backend_type',
      placeholder: '请选择后端生成代码类型',
      stringToNumber: true,
    },
  },
  {
    label: '滚动条',
    field: 'is_scroll',
    component: 'RadioGroup',
    defaultValue: 1,
    required: true,
    componentProps: {
      options: [
        { label: '有', value: 1, key: '1' },
        { label: '无', value: 0, key: '0' },
      ],
    },
  },
  {
    label: '弹窗类型',
    field: 'modal_type',
    component: 'RadioGroup',
    defaultValue: 1,
    required: true,
    componentProps: {
      options: [
        { label: '弹窗', value: 1, key: '1' },
        { label: '抽屉', value: 2, key: '2' },
      ],
    },
  },
  {
    label: '弹窗宽度',
    field: 'modal_width',
    defaultValue: 800,
    required: true,
    component: 'InputNumber',
    componentProps: {
      placeholder: '请输入弹窗宽度(px)，为0则全屏',
    },
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

/**
 * 字段表格编辑信息
 * @param param
 */

export const FieldsEditColumns = [
  {
    title: 'ID',
    key: 'id',
    width: 120,
    type: JVxeTypes.normal,
    visible: false,
  },
  {
    title: '字段名',
    key: 'label',
    width: 240,
    type: JVxeTypes.input,
    defaultValue: '',
  },
  {
    title: '字段值',
    key: 'field',
    width: 240,
    type: JVxeTypes.input,
    defaultValue: '',
  },
  {
    title: '编辑组件',
    key: 'component',
    width: 240,
    type: JVxeTypes.select,
    // dictCode: 'jvex_component_types',
    options: [
      { title: '输入框', value: 'Input' },
      { title: '数字输入框', value: 'InputNumber' },
      { title: '下拉栏', value: 'JSelectInput' },
      { title: '多行文本框', value: 'InputTextArea' },
      { title: '字典选择器', value: 'JDictSelectTag' },
      { title: 'api选择器', value: 'ApiSelect' },
    ],
    allowSearch: true,
    defaultValue: 'Input',
  },
  {
    title: '组件配置',
    key: 'componentProps',
    width: 240,
    type: JVxeTypes.textarea,
    defaultValue: '{}',
  },
  {
    title: '字段类型',
    key: 'field_type',
    width: 240,
    type: JVxeTypes.select,
    // dictCode: 'field_types',
    options: [
      { title: 'DateTime时间', value: 'DateTime' },
      { title: 'TIMESTAMP时间戳', value: 'TIMESTAMP' },
      { title: 'SmallInteger短整数', value: 'SmallInteger' },
      { title: 'Float浮点数', value: 'Float' },
      { title: 'Integer整数', value: 'Integer' },
      { title: 'Text字符串', value: 'Text' },
      { title: 'String有限长度字符串', value: 'String' },
    ],
    allowSearch: true,
    defaultValue: 'Text',
  },
  {
    title: '默认值',
    key: 'default_value',
    width: 240,
    type: JVxeTypes.input,
    defaultValue: '',
  },
  {
    title: '长度',
    key: 'length',
    width: 240,
    type: JVxeTypes.inputNumber,
    defaultValue: 0,
  },
  {
    title: '是否主键',
    key: 'primary_key',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: false,
  },
  {
    title: 'json格式存取',
    key: 'is_json',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: false,
  },
  {
    title: '是否唯一',
    key: 'is_only',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: false,
  },
  {
    title: '是否可为null',
    key: 'nullable',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: true,
  },
  {
    title: '是否可编辑',
    key: 'editable',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: true,
  },
  {
    title: '是否可清空',
    key: 'clearable',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: false,
  },
  {
    title: '表格中展示',
    key: 'table_show',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: true,
  },
  {
    title: '是否自定义渲染',
    key: 'customRender',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: false,
  },
  {
    title: '编辑中展示',
    key: 'edit_show',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: true,
  },
  {
    title: '列表接口展示',
    key: 'list_show',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: true,
  },
  {
    title: '详情接口展示',
    key: 'detail_show',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: true,
  },
  {
    title: '全量列表接口展示',
    key: 'all_list_show',
    type: JVxeTypes.checkbox,
    width: 100,
    customValue: [1, 0], // true ,false
    defaultChecked: false,
  },
] as JVxeColumn[];

// 默认字段列表
export const defaultFields = [
  {
    label: '主键',
    field: 'id',
    component: 'Input',
    componentProps: '{}',
    field_type: 'String',
    default_value: '',
    length: 36,
    nullable: 1,
    primary_key: 1,
    is_only: 1,
    is_json: 0,
    clearable: 0,
    editable: 0,
    customRender: 0,
    list_show: 1,
    table_show: 1,
    edit_show: 0,
    detail_show: 1,
    all_list_show: 1,
  },
  {
    label: '创建者',
    field: 'create_by',
    component: 'Input',
    componentProps: '{}',
    field_type: 'String',
    default_value: '',
    length: 100,
    nullable: 1,
    primary_key: 0,
    is_only: 0,
    is_json: 0,
    clearable: 0,
    editable: 0,
    customRender: 0,
    list_show: 1,
    table_show: 1,
    edit_show: 0,
    detail_show: 1,
    all_list_show: 0,
  },
  {
    label: '创建时间',
    field: 'create_time',
    component: 'Input',
    componentProps: '{}',
    field_type: 'TIMESTAMP',
    default_value: 'server_default:CURRENT_TIMESTAMP',
    length: 0,
    nullable: 1,
    primary_key: 0,
    is_only: 0,
    is_json: 0,
    clearable: 0,
    editable: 0,
    list_show: 1,
    customRender: 0,
    table_show: 1,
    edit_show: 0,
    detail_show: 1,
    all_list_show: 0,
  },
  {
    label: '修改者',
    field: 'update_by',
    component: 'Input',
    componentProps: '{}',
    field_type: 'String',
    default_value: '',
    length: 100,
    nullable: 1,
    primary_key: 0,
    is_only: 0,
    is_json: 0,
    clearable: 0,
    editable: 0,
    customRender: 0,
    list_show: 1,
    table_show: 1,
    edit_show: 0,
    detail_show: 1,
    all_list_show: 0,
  },
  {
    label: '修改时间',
    field: 'update_time',
    component: 'Input',
    componentProps: '{}',
    field_type: 'TIMESTAMP',
    default_value: 'server_default:CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
    length: 0,
    nullable: 1,
    primary_key: 0,
    is_only: 0,
    is_json: 0,
    clearable: 0,
    editable: 0,
    customRender: 0,
    list_show: 1,
    table_show: 1,
    edit_show: 0,
    detail_show: 1,
    all_list_show: 0,
  },
  {
    label: '软删除标记',
    field: 'del_flag',
    component: 'InputNumber',
    componentProps: '{}',
    field_type: 'SmallInteger',
    default_value: 0,
    length: 0,
    nullable: 1,
    primary_key: 0,
    is_only: 0,
    is_json: 0,
    clearable: 0,
    editable: 0,
    customRender: 1,
    list_show: 1,
    table_show: 0,
    edit_show: 0,
    detail_show: 1,
    all_list_show: 0,
  },
  {
    label: '排序字段',
    field: 'sort_no',
    component: 'InputNumber',
    componentProps: '{}',
    field_type: 'Float',
    default_value: 1,
    length: 0,
    nullable: 1,
    primary_key: 0,
    is_only: 0,
    is_json: 0,
    clearable: 0,
    editable: 0,
    customRender: 0,
    list_show: 1,
    table_show: 0,
    edit_show: 0,
    detail_show: 1,
    all_list_show: 0,
  },
  {
    label: '简介描述',
    field: 'description',
    component: 'InputTextArea',
    componentProps: '{}',
    field_type: 'Text',
    default_value: '',
    length: 0,
    nullable: 1,
    primary_key: 0,
    is_only: 0,
    is_json: 0,
    clearable: 0,
    editable: 1,
    customRender: 0,
    list_show: 1,
    table_show: 1,
    edit_show: 1,
    detail_show: 1,
    all_list_show: 0,
  },
];
/**
 * 查询参数表格编辑信息
 * @param param
 */

export const QueryParamsEditColumns = [
  {
    title: 'ID',
    key: 'id',
    width: 120,
    type: JVxeTypes.normal,
    visible: false,
  },
  {
    title: '名称',
    key: 'label',
    width: 240,
    type: JVxeTypes.input,
    defaultValue: '',
  },
  {
    title: '字段',
    key: 'field',
    width: 240,
    type: JVxeTypes.input,
    defaultValue: '',
  },
  {
    title: '控件组件',
    key: 'component',
    width: 240,
    type: JVxeTypes.select,
    // dictCode: 'jvex_component_types',
    options: [
      { title: '输入框', value: 'Input' },
      { title: '数字输入框', value: 'InputNumber' },
      { title: '下拉栏', value: 'JSelectInput' },
      { title: '多行文本框', value: 'InputTextArea' },
      { title: '字典选择器', value: 'JDictSelectTag' },
      { title: 'api选择器', value: 'ApiSelect' },
    ],
    defaultValue: 'Input',
  },
  {
    title: '组件配置',
    key: 'componentProps',
    width: 240,
    type: JVxeTypes.textarea,
    defaultValue: '{}',
  },
  {
    title: '样式配置',
    key: 'colProps',
    width: 240,
    type: JVxeTypes.textarea,
    defaultValue: '{}',
  },
] as JVxeColumn[];

/**
 * 按钮参数表格编辑信息
 * @param param
 */

export const ButtonsEditColumns = [
  {
    title: 'ID',
    key: 'id',
    width: 120,
    type: JVxeTypes.normal,
    visible: false,
  },
  {
    title: '名称',
    key: 'name',
    width: 240,
    type: JVxeTypes.input,
    defaultValue: '按钮',
  },
  {
    title: '按钮位置',
    key: 'slot',
    width: 240,
    type: JVxeTypes.select,
    defaultValue: 'tableTitle',
    options: [
      { title: '隐藏/查询接口', value: 'hideApi' },
      { title: '表格上方', value: 'tableTitle' },
      { title: '选择后下拉栏', value: 'overlay' },
      { title: '操作拦', value: 'action' },
      { title: '操作拦下拉栏', value: 'actionDropDown' },
    ],
  },
  {
    title: '点击触发函数',
    key: 'function',
    width: 240,
    type: JVxeTypes.select,
    defaultValue: '',
    allowInput: true,
    options: [
      { title: '列表查询', value: 'list' },
      { title: '全量列表', value: 'getAllList' },
      { title: '新增', value: 'handleAdd' },
      { title: '编辑', value: 'handleEdit' },
      { title: '详情', value: 'handleDetail' },
      { title: '删除', value: 'handleDelete' },
      { title: '批量删除', value: 'batchHandleDelete' },
      { title: '导入', value: 'onImportXls' },
      { title: '导出', value: 'onExportXls' },
    ],
  },
  {
    title: '是否显示',
    key: 'is_show',
    width: 240,
    type: JVxeTypes.checkbox,
    customValue: [true, false], // true ,false
    defaultChecked: false,
  },
  {
    title: '绑定权限',
    key: 'permissions',
    width: 240,
    type: JVxeTypes.selectMultiple,
    allowInput: true,
    defaultValue: [],
    options: [],
  },
] as JVxeColumn[];

// 默认按钮列表
export const defaultButtons = [
  {
    name: '列表查询',
    slot: 'hideApi',
    function: 'list',
    is_show: false,
    permissions: [],
  },
  {
    name: '全量列表',
    slot: 'hideApi',
    function: 'getAllList',
    is_show: false,
    permissions: [],
  },
  {
    name: '详情',
    slot: 'actionDropDown',
    function: 'handleDetail',
    is_show: true,
    permissions: [],
  },
  {
    name: '新增',
    slot: 'tableTitle',
    function: 'handleAdd',
    is_show: true,
    permissions: [],
  },
  {
    name: '编辑',
    slot: 'action',
    function: 'handleEdit',
    is_show: true,
    permissions: [],
  },
  {
    name: '删除',
    slot: 'actionDropDown',
    function: 'handleDelete',
    is_show: true,
    permissions: [],
  },
  {
    name: '批量删除',
    slot: 'overlay',
    function: 'batchHandleDelete',
    is_show: true,
    permissions: [],
  },
  {
    name: '导入',
    slot: 'tableTitle',
    function: 'onImportXls',
    is_show: false,
    permissions: [],
  },
  {
    name: '导出',
    slot: 'tableTitle',
    function: 'onExportXls',
    is_show: false,
    permissions: [],
  },
];
