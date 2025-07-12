import { BasicColumn, FormSchema } from '/@/components/Table';
import { allList as allDataSourceList } from '@/views/dataManage/dataSource/datasource.api';
import { allList as allDataModelList } from '@/views/dataManage/dataModel/datamodel.api';
import { allList as allDocumentList } from '../document/document.api';
import { allList as allDataSetList } from '../dataset/dataset.api';

// 定义映射变量
let dataSourceMap: Map<string, string>;
let dataModelMap: Map<string, string>;
let documentMap: Map<string, string>;
let dataSetMap: Map<string, string>;

// 获取映射
Promise.all([allDataSourceList({}), allDataModelList({}), allDocumentList({}), allDataSetList({})])
  .then(([dataSourceList, dataModelList, documentList, dataSetList]) => {
    dataSourceMap = new Map(dataSourceList.map((item) => [item.id, item.name]));
    dataModelMap = new Map(dataModelList.map((item) => [item.id, item.name]));
    documentMap = new Map(documentList.map((item) => [item.id, item.name]));
    dataSetMap = new Map(dataSetList.map((item) => [item.id, item.name]));
  })
  .catch((error) => {
    console.error('Failed to fetch mappings:', error);
  });

// 定义列
export const columns: BasicColumn[] = [
  {
    title: 'ID',
    align: 'center',
    dataIndex: 'id',
    defaultHidden: true,
    width: 300,
  },
  {
    title: '内容',
    align: 'center',
    dataIndex: 'content',
    width: 1000,
  },
  {
    title: '类型',
    align: 'center',
    dataIndex: 'chunk_type',
    customRender: ({ text }) => {
      return text == 'qa' ? '问答对' : '知识段';
    },
  },
  {
    title: '所属数据集',
    align: 'center',
    dataIndex: 'dataset_id',
    customRender: ({ text }) => {
      return dataSetMap?.get(text) || text;
    },
  },
  {
    title: '所属文档',
    align: 'center',
    dataIndex: 'document_id',
    customRender: ({ text }) => {
      return documentMap?.get(text) || text;
    },
  },
  {
    title: '所属数据源',
    align: 'center',
    dataIndex: 'datasource_id',
    customRender: ({ text }) => {
      return dataSourceMap?.get(text) || text;
    },
  },
  {
    title: '所属数据模型',
    align: 'center',
    dataIndex: 'datamodel_id',
    customRender: ({ text }) => {
      return dataModelMap?.get(text) || text;
    },
  },
  {
    title: '状态',
    align: 'center',
    dataIndex: 'status',
    customRender: ({ text }) => {
      return text == 1 ? '已同步' : '未同步';
    },
  },
  {
    title: '标记状态',
    align: 'center',
    dataIndex: 'star_flag',
    customRender: ({ text }) => {
      return text == 1 ? '已标记' : '未标记';
    },
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
  {
    title: '简介描述',
    align: 'center',
    dataIndex: 'description',
  },
];

//检索数据
export const retrievalFormSchema: FormSchema[] = [
  {
    label: '提示词',
    field: 'query',
    component: 'Input',
    colProps: { span: 12 },
  },
  {
    label: '召回数量',
    field: 'k',
    component: 'InputNumber',
    defaultValue: 5,
    componentProps: {
      min: 1,
    },
    colProps: { span: 4 },
  },
  {
    label: '检索模式',
    field: 'retrieval_type',
    component: 'JSelectInput',
    defaultValue: 'vector',
    componentProps: {
      options: [
        { label: '语义', value: 'vector' },
        { label: '全文', value: 'keyword' },
        { label: '混合', value: 'all' },
      ],
    },
    // labelWidth: 110,
    colProps: { span: 4 },
  },
  {
    label: '分数过滤',
    field: 'score_threshold',
    component: 'InputNumber',
    defaultValue: 0.1,
    componentProps: {
      min: 0,
      //数值精度
      precision: 2,
      //步数
      step: 0.1,
    },
    colProps: { span: 4 },
  },
  {
    label: '所属数据集',
    field: 'dataset_id',
    component: 'ApiSelect',
    componentProps: {
      api: allDataSetList,
      mode: 'multiple',
      params: {},
      labelField: 'name',
      valueField: 'id',
    },
    colProps: { span: 6 },
  },
  {
    label: '所属数据模型',
    field: 'datamodel_id',
    component: 'ApiSelect',
    componentProps: {
      api: allDataModelList,
      mode: 'multiple',
      params: {},
      labelField: 'name',
      valueField: 'id',
    },
    colProps: { span: 6 },
  },
  {
    label: '结果重排',
    field: 'rerank',
    defaultValue: '0',
    component: 'JSwitch',
    componentProps: {
      options: ['1', '0'],
    },
    colProps: { span: 4 },
  },
  {
    label: '结果重排分数过滤',
    field: 'rerank_score_threshold',
    component: 'InputNumber',
    defaultValue: 0,
    componentProps: {
      min: 0,
      //数值精度
      precision: 2,
      //步数
      step: 0.1,
    },
    colProps: { span: 4 },
    ifShow: ({ values }) => values.rerank == '1',
  },
];

export const retrievalColumns: BasicColumn[] = [
  {
    title: '内容',
    align: 'center',
    dataIndex: 'page_content',
    width: 800,
  },
  {
    title: '分数',
    align: 'center',
    dataIndex: 'score',
    width: 100,
  },
  {
    title: '所属数据集',
    align: 'center',
    dataIndex: 'dataset_id',
    customRender: ({ text }) => {
      return dataSetMap?.get(text) || text;
    },
  },
  {
    title: '所属文档',
    align: 'center',
    dataIndex: 'document_id',
    customRender: ({ text }) => {
      return documentMap?.get(text) || text;
    },
  },
  {
    title: '所属数据源',
    align: 'center',
    dataIndex: 'datasource_id',
    customRender: ({ text }) => {
      return dataSourceMap?.get(text) || text;
    },
  },
  {
    title: '所属数据模型',
    align: 'center',
    dataIndex: 'datamodel_id',
    customRender: ({ text }) => {
      return dataModelMap?.get(text) || text;
    },
  },
];
