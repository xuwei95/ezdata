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
    <ChunkModal @register="registerModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" name="chunk-Chunk" setup>
  import { ref, computed, unref, onMounted } from 'vue';
  import { useRoute } from 'vue-router';
  import { BasicTable, FormSchema, TableAction } from "/@/components/Table";
  import { useModal } from '/@/components/Modal';
  import { useListPage } from '/@/hooks/system/useListPage';
  import ChunkModal from './components/ChunkModal.vue';
  import { columns } from './chunk.data';
  import { list, deleteOne, batchDelete } from './chunk.api';
  import { allList as allDocumentList } from '@/views/rag/document/document.api';
  import { allList as allDataModelList } from '@/views/dataManage/dataModel/datamodel.api';
  const checkedKeys = ref<Array<string | number>>([]);
  const urlParams = new URLSearchParams(window.location.search);
  const defaultDocumentId = urlParams.get('document_id') || '';
  //注册Modal
  const [registerModal, { openModal }] = useModal();
  //查询数据
  const searchFormSchema: FormSchema[] = [
    {
      label: '关键词',
      field: 'content',
      component: 'Input',
    },
    {
      label: '类型',
      field: 'chunk_type',
      component: 'JSelectInput',
      // defaultValue: '知识段',
      componentProps: {
        options: [
          { label: '知识段', value: 'chunk' },
          { label: '问答对', value: 'qa' },
        ],
      },
    },
    {
      label: '状态',
      field: 'status',
      component: 'JSelectInput',
      // defaultValue: 1,
      componentProps: {
        options: [
          { label: '已同步', value: 1 },
          { label: '未同步', value: 0 },
        ],
      },
    },
    {
      label: '所属文档',
      field: 'document_id',
      component: 'ApiSelect',
      defaultValue: defaultDocumentId,
      dynamicDisabled: ({ values }) => {
        return !!values.id || defaultDocumentId != '';
      },
      componentProps: {
        api: allDocumentList,
        params: {},
        labelField: 'name',
        valueField: 'id',
      },
    },
    {
      label: '所属数据模型',
      field: 'datamodel_id',
      component: 'ApiSelect',
      componentProps: {
        api: allDataModelList,
        params: {},
        labelField: 'name',
        valueField: 'id',
      },
    },
  ];
  //注册table数据
  const { prefixCls, tableContext } = useListPage({
    tableProps: {
      title: '知识段管理',
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
    ];
  }
</script>

<style scoped></style>
