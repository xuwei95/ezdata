<template>
  <div>
    <BasicTable @register="registerTable">
      <template #tableTitle>
        <a-button type="primary" @click="handleApply" preIcon="ant-design:plus-outlined"> 申请接口</a-button>
      </template>
      <template #action="{ record }">
        <TableAction :actions="getTableAction(record)" />
      </template>
    </BasicTable>
    <ApiApplyModal @register="registerModal" @success="reload" :app_id="app_id" />
  </div>
</template>

<script lang="ts" setup>
  import { columns } from './api_token.data';
  import { list, UpdateStatus, deleteKey } from './api_token.api';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { onMounted, watch } from 'vue';
  import { useModal } from '/@/components/Modal';
  import ApiApplyModal from './ApiApplyModal.vue';
  const props = defineProps({
    app_id: { type: String, default: () => '' },
  });
  const [registerModal, { openModal: openModal }] = useModal();
  const [registerTable, { reload }] = useTable({
    api: list,
    rowKey: 'id',
    columns: columns,
    striped: true,
    showTableSetting: true,
    clickToRowSelect: false,
    bordered: true,
    showIndexColumn: false,
    tableSetting: { fullScreen: true },
    beforeFetch: (params) => {
      return Object.assign({ app_id: props.app_id }, params);
    },
    actionColumn: {
      width: 80,
      title: '操作',
      dataIndex: 'action',
      slots: { customRender: 'action' },
      fixed: 'right',
    },
  });
  /**
   * 申请
   */
  function handleApply() {
    openModal(true, {
      isUpdate: true,
      showFooter: true,
    });
  }
  /**
   * 更新状态事件
   */
  async function handleStatus(record: Recordable) {
    await UpdateStatus({ id: record.id }, reload);
  }
  /**
   * 删除事件
   */
  async function handleDelete(record: Recordable) {
    await deleteKey({ id: record.id }, reload);
  }
  /**
   * 操作栏
   */
  function getTableAction(record) {
    return [
      {
        label: record.status == 1 ? '禁用' : '启用',
        popConfirm: {
          title: '确定' + (record.status == 1 ? '禁用' : '启用') + '吗?',
          confirm: handleStatus.bind(null, record),
        },
      },
      {
        label: '删除',
        popConfirm: {
          title: '确定删除?',
          confirm: handleDelete.bind(null, record),
        },
      },
    ];
  }
  // 监听 data 变化
  onMounted(() => {
    watch(
      () => props.app_id,
      async () => {
        reload();
      },
      { deep: true, immediate: true }
    );
  });
</script>
