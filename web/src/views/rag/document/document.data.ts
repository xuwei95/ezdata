import { BasicColumn, FormSchema } from '/@/components/Table';
import { render } from '/@/utils/common/renderUtils';
import { allList as allDataSetList } from '../dataset/dataset.api';
// 定义映射变量
let dataSetMap: Map<string, string>;
// 获取映射
Promise.all([allDataSetList({})])
  .then(([dataSetList]) => {
    dataSetMap = new Map(dataSetList.map((item) => [item.id, item.name]));
  })
  .catch((error) => {
    console.error('Failed to fetch mappings:', error);
  });

// 数据源类型下拉选项
export const documentTypeOptions = [
  { label: '上传文件', value: 'upload_file' },
  { label: '网络抓取', value: 'website_crawl' },
  // { label: 'notion导入', value: 'notion_import' },
];
const uploadFileFormSchema: FormSchema[] = [
  {
    label: '文件地址',
    field: 'upload_file',
    required: true,
    component: 'JUpload',
    componentProps: {
      fileMax: 1,
    },
  },
];

const websiteCrawlFormSchema: FormSchema[] = [
  {
    label: 'url地址',
    field: 'url',
    required: true,
    component: 'Input',
  },
  {
    label: '抓取方式',
    field: 'provider',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'base',
    componentProps: {
      options: [
        { label: '普通模式', value: 'base' },
        { label: 'firecrawl', value: 'firecrawl' },
      ],
    },
  },
  {
    label: '抓取策略',
    field: 'mode',
    required: true,
    component: 'JSelectInput',
    defaultValue: 'scrape',
    componentProps: {
      options: [
        { label: '抓取当页', value: 'scrape' },
        { label: '递归抓取', value: 'crawl' },
      ],
    },
  },
];
const notionImportFormSchema: FormSchema[] = [
  {
    label: 'notion地址',
    field: 'path',
    required: true,
    component: 'Input',
  },
];
// 数据源连接配置表单字典
export const metaDataFormSchemaMap = {
  upload_file: uploadFileFormSchema,
  website_crawl: websiteCrawlFormSchema,
  notion_import: notionImportFormSchema,
};

//列表数据
export const columns: BasicColumn[] = [
  {
    title: '主键',
    align: 'center',
    dataIndex: 'id',
    defaultHidden: true,
    width: 300,
  },
  {
    title: '名称',
    align: 'center',
    dataIndex: 'name',
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
    title: '文档类型',
    align: 'center',
    dataIndex: 'document_type',
    customRender: ({ text }) => {
      return render.renderDict(text, 'document_type');
    },
  },
  {
    title: '状态',
    align: 'center',
    dataIndex: 'status',
    customRender: ({ text }) => {
      if (text == 1) {
        return '待训练';
      } else if (text == 2) {
        return '训练中';
      } else if (text == 3) {
        return '训练成功';
      } else if (text == 4) {
        return '训练失败';
      }
    },
  },
  {
    title: '简介描述',
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
    width: 200,
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
    width: 200,
  },
];
