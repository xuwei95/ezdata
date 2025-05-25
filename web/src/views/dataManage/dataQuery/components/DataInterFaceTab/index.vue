<template>
  <!--引用表格-->
  <BasicTable @register="registerTable" :rowSelection="rowSelection">
    <!--插槽:table标题-->
    <template #tableTitle>
      <a-button type="primary" @click="handleApply" preIcon="ant-design:plus-outlined"> 申请接口</a-button>
<!--      <j-upload-button type="primary" preIcon="ant-design:import-outlined" @click="onImportXls">导入</j-upload-button>-->
<!--      <a-button type="primary" preIcon="ant-design:export-outlined" @click="onExportXls"> 导出</a-button>-->
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
  <DataInterFaceApplyModal @register="registerModal" @success="handleSuccess" :datamodel_id="model.id" />
  <DataInterFaceReviewModal @register="registerReviewModal" @success="handleSuccess" :datamodel_id="model.id" />
</template>

<script lang="ts" setup>
  import { watch, onMounted, ref, unref } from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { useModal } from '/@/components/Modal';
  import { useListPage } from '/@/hooks/system/useListPage';
  import DataInterFaceApplyModal from './DataInterFaceApplyModal.vue';
  import DataInterFaceReviewModal from './DataInterFaceReviewModal.vue';
  import { columns, searchFormSchema } from './data_interface.data';
  import { list, deleteOne, batchDelete, UpdateStatus, getImportUrl, getExportUrl } from './data_interface.api';
  const props = defineProps({
    data: { type: Object, default: () => ({}) },
    rootTreeData: { type: Array, default: () => [] },
  });
  const model = ref<object>({}); // 模型数据
  const modelFields = ref<any[]>([]); // 模型字段列表
  const checkedKeys = ref<Array<string | number>>([]);
  //注册Modal
  const [registerModal, { openModal }] = useModal();
  const [registerReviewModal, { openModal: openReviewModal }] = useModal();
  //注册table数据
  const { prefixCls, tableContext, onImportXls, onExportXls } = useListPage({
    tableProps: {
      title: '数据接口',
      api: list,
      searchInfo: {
        datamodel_id: props.data.id,
      },
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
    importConfig: {
      url: getImportUrl,
      success: handleSuccess,
    },
    exportConfig: {
      name: '数据接口导出结果',
      url: getExportUrl,
    },
  });

  const [registerTable, { setProps, reload }, { rowSelection, selectedRowKeys }] = tableContext;

  /**
   * 新增事件
   */
  function handleApply() {
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
   * 更新状态事件
   */
  async function handleStatus(record: Recordable) {
    await UpdateStatus({ id: record.id }, handleSuccess);
  }
  /**
   * 审核事件
   */
  function handleReview(record: Recordable) {
    openReviewModal(true, {
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
        auth: ['data_interface:edit'],
      },
      {
        label: '审核',
        onClick: handleReview.bind(null, record),
        auth: ['data_interface:verify'],
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
        label: record.status == 1 ? '禁用' : '启用',
        popConfirm: {
          title: '确定' + (record.status == 1 ? '禁用' : '启用') + '吗?',
          confirm: handleStatus.bind(null, record),
        },
        auth: ['data_interface:status'],
      },
      {
        label: '删除',
        popConfirm: {
          title: '确定删除吗?',
          confirm: handleDelete.bind(null, record),
        },
        auth: ['data_interface:delete'],
      },
    ];
  }
  // 获取列表数据
  function fetchData() {
    setProps({ searchInfo: { datamodel_id: model.value.id } });
    reload();
  }
  onMounted(() => {
    watch(
      () => props.data,
      async () => {
        let record = unref(props.data);
        if (typeof record !== 'object') {
          record = {};
        }
        model.value = record;
        modelFields.value = record.fields;
        await fetchData();
      },
      { deep: true, immediate: true }
    );
  });
</script>
