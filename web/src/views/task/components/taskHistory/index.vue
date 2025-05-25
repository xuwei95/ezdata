<template>
  <div>
    <BasicTable @register="registerTable">
      <template #action="{ record }">
        <TableAction :actions="getTableAction(record)" />
      </template>
    </BasicTable>
    <TaskLogsModal @register="registerTaskLogModal" @success="reload" />
  </div>
</template>

<script lang="ts" setup>
  import { instanceList } from '../../task.api';
  import { instanceColumns } from '../../task.data';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { onMounted, watch } from 'vue';
  import { useModal } from '/@/components/Modal';
  import TaskLogsModal from './taskLogModal.vue';
  const props = defineProps({
    task_id: { type: String, default: () => '' },
    task_type: { type: String, default: () => 'task' },
  });
  const [registerTaskLogModal, { openModal: openTaskLogModal }] = useModal();
  const [registerTable, { reload }] = useTable({
    api: instanceList,
    rowKey: 'id',
    columns: instanceColumns,
    striped: true,
    showTableSetting: true,
    clickToRowSelect: false,
    bordered: true,
    showIndexColumn: false,
    tableSetting: { fullScreen: true },
    beforeFetch: (params) => {
      return Object.assign({ task_id: props.task_id, task_type: props.task_type }, params);
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
   * 查看日志
   */
  function handleLog(record) {
    console.log('log', record);
    openTaskLogModal(true, {
      data: record,
      isUpdate: true,
      showFooter: true,
    });
  }
  /**
   * 操作栏
   */
  function getTableAction(record) {
    return [
      {
        label: '查看日志',
        onClick: handleLog.bind(null, record),
        auth: ['task:log'],
      },
    ];
  }
  // 监听 data 变化
  onMounted(() => {
    watch(
      () => props.task_id,
      async () => {
        reload();
      },
      { deep: true, immediate: true }
    );
  });
</script>
