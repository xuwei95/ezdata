<template>
  <div>
    <!--引用表格-->
    <BasicTable @register="registerTable" :rowSelection="rowSelection">
      <!--插槽:table标题-->
      <template #tableTitle>
        <a-button type="primary" @click="handleAdd" preIcon="ant-design:plus-outlined"> 新增</a-button>
        <a-dropdown v-if="selectedRowKeys.length > 0">
          <template #overlay>
            <a-menu>
              <a-menu-item key="1" @click="batchHandleDelete">
                <Icon icon="ant-design:delete-outlined" />
                删除
              </a-menu-item>
            </a-menu>
          </template>
          <a-button>
            批量操作
            <Icon icon="mdi:chevron-down" />
          </a-button>
        </a-dropdown>
      </template>
      <!--操作栏-->
      <template #action="{ record }">
        <TableAction :actions="getTableAction(record)" :dropDownActions="getDropDownAction(record)" />
      </template>
      <!--字段回显插槽-->
      <template #htmlSlot="{ text }">
        <div v-html="text"></div>
      </template>
    </BasicTable>
    <!-- 表单区域 -->
    <DocumentModal @register="registerModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" name="document-Document" setup>
  import { ref } from 'vue';
  import { BasicTable, TableAction, FormSchema } from '/@/components/Table';
  import { useModal } from '/@/components/Modal';
  import { useListPage } from '/@/hooks/system/useListPage';
  import DocumentModal from './components/DocumentModal.vue';
  import { columns } from './document.data';
  import { list, deleteOne, batchDelete, train } from './document.api';
  import { useRouter } from 'vue-router';
  import { allList as allDataSetList } from '@/views/rag/dataset/dataset.api';
  const router = useRouter();
  const checkedKeys = ref<Array<string | number>>([]);
  //注册Modal
  const [registerModal, { openModal }] = useModal();
  const urlParams = new URLSearchParams(window.location.search);
  const defaultDatasetId = urlParams.get('dataset_id') || '';
  const searchFormSchema: FormSchema[] = [
    {
      label: '名称',
      field: 'name',
      component: 'Input',
    },
    {
      label: '所属数据集',
      field: 'dataset_id',
      component: 'ApiSelect',
      defaultValue: defaultDatasetId,
      dynamicDisabled: ({ values }) => {
        return !!values.id || defaultDatasetId != '';
      },
      componentProps: {
        api: allDataSetList,
        params: {},
        labelField: 'name',
        valueField: 'id',
      },
    },
    {
      label: '文档类型',
      field: 'document_type',
      component: 'JDictSelectTag',
      componentProps: {
        dictCode: 'document_type',
        placeholder: '请选择文档类型',
        stringToNumber: false,
      },
    },
    {
      label: '状态',
      field: 'status',
      component: 'JSelectInput',
      // defaultValue: 1,
      componentProps: {
        options: [
          { label: '待训练', value: 1 },
          { label: '训练中', value: 2 },
          { label: '训练成功', value: 3 },
          { label: '训练失败', value: 4 },
        ],
      },
    },
  ];
  //注册table数据
  const { prefixCls, tableContext } = useListPage({
    tableProps: {
      title: '文档管理',
      api: list,
      columns,
      canResize: false,
      formConfig: {
        //labelWidth: 120,
        schemas: searchFormSchema,
        autoSubmitOnEnter: true,
        showAdvancedButton: true,
        fieldMapToNumber: [],
        fieldMapToTime: [],
      },
      actionColumn: {
        width: 200,
        fixed: 'right',
      },
    },
  });

  const [registerTable, { reload }, { rowSelection, selectedRowKeys }] = tableContext;

  /**
   * 新增事件
   */
  function handleAdd() {
    openModal(true, {
      isUpdate: false,
      showFooter: true,
    });
  }
  /**
   * 编辑事件
   */
  function handleEdit(record: Recordable) {
    openModal(true, {
      record,
      isUpdate: true,
      showFooter: true,
    });
  }
  /**
   * 编辑知识段事件
   */
  function handleEditChunks(record: Recordable) {
    router.push('/rag/chunk?document_id=' + record.id);
  }
  /**
   * 训练知识库
   */
  async function handleTrain(record: Recordable) {
    await train({ id: record.id }, handleSuccess);
  }
  /**
   * 详情
   */
  function handleDetail(record: Recordable) {
    openModal(true, {
      record,
      isUpdate: true,
      showFooter: false,
    });
  }
  /**
   * 删除事件
   */
  async function handleDelete(record) {
    await deleteOne({ id: record.id }, handleSuccess);
  }
  /**
   * 批量删除事件
   */
  async function batchHandleDelete() {
    await batchDelete({ ids: selectedRowKeys.value }, handleSuccess);
  }
  /**
   * 成功回调
   */
  function handleSuccess() {
    (selectedRowKeys.value = []) && reload();
  }
  /**
   * 操作栏
   */
  function getTableAction(record) {
    return [
      {
        label: '编辑',
        onClick: handleEdit.bind(null, record),
      },
      {
        label: '知识段编辑',
        onClick: handleEditChunks.bind(null, record),
      },
    ];
  }
  /**
   * 下拉操作栏
   */
  function getDropDownAction(record) {
    return [
      {
        label: '详情',
        onClick: handleDetail.bind(null, record),
      },
      {
        label: '删除',
        popConfirm: {
          title: '确定删除吗?',
          confirm: handleDelete.bind(null, record),
        },
      },
      {
        label: '重新训练',
        popConfirm: {
          title: '确定重新训练?',
          confirm: handleTrain.bind(null, record),
        },
      },
    ];
  }
</script>

<style scoped></style>
