<template>
  <div>
    <!--引用表格-->
    <BasicTable @register="registerTable" :rowSelection="rowSelection">
      <template #tableTitle>
        <a-button type="primary" @click="handleRestartAllJob">重启所有定时任务</a-button>
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
        <TableAction :actions="getTableAction(record)" />
      </template>
      <!--字段回显插槽-->
      <template #htmlSlot="{ text }">
        <div v-html="text"></div>
      </template>
    </BasicTable>
    <!-- 表单区域 -->
    <JobModal @register="registerModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" name="worker-Worker" setup>
  import { ref } from 'vue';
  import { Modal } from 'ant-design-vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { useModal } from '/@/components/Modal';
  import { useListPage } from '/@/hooks/system/useListPage';
  import JobModal from './components/JobModal.vue';
  import { columns, searchFormSchema } from './job.data';
  import { list, batchDelete, deleteOne } from './job.api';
  import { resetAllJob } from '/@/views/task/task.api';
  const checkedKeys = ref<Array<string | number>>([]);
  //注册Modal
  const [registerModal, { openModal }] = useModal();
  //注册table数据
  const { prefixCls, tableContext, onImportXls, onExportXls } = useListPage({
    tableProps: {
      title: '定时job管理',
      api: list,
      columns,
      canResize: true,
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
   * 重启所有定时任务
   */
  async function handleRestartAllJob() {
    Modal.confirm({
      title: '重启确认',
      content: '确认重启所有定时任务？',
      okText: '确认',
      cancelText: '取消',
      async onOk() {
        await resetAllJob({});
        reload();
      },
    });
  }
  /**
   * 成功回调
   */
  function handleSuccess() {
    (selectedRowKeys.value = []) && reload();
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
   * 操作栏
   */
  function getTableAction(record) {
    return [
      {
        label: '删除',
        popConfirm: {
          title: '确定删除吗?',
          confirm: handleDelete.bind(null, record),
        },
        auth: ['job:delete'],
      },
    ];
  }
</script>

<style scoped></style>
