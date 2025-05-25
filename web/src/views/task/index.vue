<template>
  <div>
    <!--引用表格-->
    <BasicTable @register="registerTable" :rowSelection="rowSelection">
      <!--插槽:table标题-->
      <template #tableTitle>
        <a-button v-auth="''" type="primary" @click="handleAdd" preIcon="ant-design:plus-outlined"> 新增</a-button>
<!--        <j-upload-button type="primary" preIcon="ant-design:import-outlined" @click="onImportXls">导入</j-upload-button>-->
<!--        <a-button type="primary" preIcon="ant-design:export-outlined" @click="onExportXls"> 导出</a-button>-->
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
    <TaskModal @register="registerModal" @success="handleSuccess" />
    <taskHistoryDrawer @register="registerHistoryDrawer" @success="handleSuccess" />
    <TaskLogsModal @register="registerTaskLogModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" name="taREDACTEDTask" setup>
  import { ref, computed, unref } from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { useModal } from '/@/components/Modal';
  import { useDrawer } from '/@/components/Drawer';
  import { useListPage } from '/@/hooks/system/useListPage';
  import { usePermission } from '/@/hooks/web/usePermission';
  import TaskModal from './components/TaskModal.vue';
  import TaskHistoryDrawer from './components/TaskHistoryDrawer.vue';
  import TaskLogsModal from './components/taskHistory/taskLogModal.vue';
  import { columns, searchFormSchema } from './task.data';
  import { list, deleteOne, batchDelete, UpdateStatus, getImportUrl, getExportUrl, startTask } from './task.api';
  import { useMessage } from "@/hooks/web/useMessage";
  const checkedKeys = ref<Array<string | number>>([]);
  //注册Modal
  const [registerModal, { openModal }] = useModal();
  const [registerTaskLogModal, { openModal: openTaskLogModal }] = useModal();
  const [registerHistoryDrawer, { openDrawer: openHistoryDrawer }] = useDrawer();
  const { createMessage } = useMessage();
  const { hasPermission } = usePermission();
  //注册table数据
  const { prefixCls, tableContext, onImportXls, onExportXls } = useListPage({
    tableProps: {
      title: '任务',
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
        width: 260,
        fixed: 'right',
      },
    },
    importConfig: {
      url: getImportUrl,
      success: handleSuccess,
    },
    exportConfig: {
      name: '任务导出结果',
      url: getExportUrl,
    },
  });

  const [registerTable, { reload }, { rowSelection, selectedRowKeys }] = tableContext;

  /**
   * 新增事件
   */
  function handleAdd() {
    openModal(true, {
      isUpdate: false,
      isCopy: false,
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
      isCopy: false,
      showFooter: true,
    });
  }
  /**
   * 复制任务
   */
  function handleCopy(record: Recordable) {
    openModal(true, {
      record,
      isUpdate: true,
      isCopy: true,
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
   * 执行历史
   */
  function handleHistory(record: Recordable) {
    openHistoryDrawer(true, {
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
  async function handleStart(record) {
    const res = await startTask({ id: record.id, trigger: 'once' });
    createMessage.success('任务发送成功！');
    if (hasPermission(['task:log'])) {
      openTaskLogModal(true, {
        data: { id: res.task_uuid },
        isUpdate: true,
        showFooter: true,
      });
    }
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
        label: '手动执行',
        popConfirm: {
          title: '确定手动单次触发?',
          confirm: handleStart.bind(null, record),
        },
      },
    ];
  }
  /**
   * 下拉操作栏
   */
  function getDropDownAction(record) {
    return [
      {
        label: '复制',
        onClick: handleCopy.bind(null, record),
      },
      {
        label: '执行历史',
        onClick: handleHistory.bind(null, record),
      },
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
