<template>
  <div>
    <!--引用表格-->
    <BasicTable @register="registerTable" :rowSelection="rowSelection">
      <!--插槽:table标题-->
      <template #tableTitle>
        <a-button v-auth="'dag:add'" type="primary" @click="handleAdd" preIcon="ant-design:plus-outlined"> 新增</a-button>
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
    <DagTaskModal @register="registerModal" @success="handleSuccess" />
    <DagRunningModal @register="registerDagRunningModal" @success="handleSuccess" />
    <taskHistoryDrawer @register="registerHistoryDrawer" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" name="taREDACTEDTask" setup>
  import { useRouter } from "vue-router";
  import { ref, computed, unref } from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { useModal } from '/@/components/Modal';
  import { useListPage } from '/@/hooks/system/useListPage';
  import { useDrawer } from '/@/components/Drawer';
  import DagTaskModal from './DagTaskModal.vue';
  import TaskHistoryDrawer from '../components/TaskHistoryDrawer.vue';
  import DagRunningModal from './dag-editor/components/DagRunningModal.vue';
  import { columns, searchFormSchema } from './dag_task.data';
  import {
    dagList,
    deleteOne,
    batchDelete,
    UpdateStatus,
    getImportUrl,
    getExportUrl,
    startTask
  } from '../task.api';
  const router = useRouter();
  const checkedKeys = ref<Array<string | number>>([]);
  //注册Modal
  const [registerModal, { openModal }] = useModal();
  const [registerDagRunningModal, { openModal: openDagRunningModal }] = useModal();
  // openDagRunningModal
  const [registerHistoryDrawer, { openDrawer: openHistoryDrawer }] = useDrawer();
  //注册table数据
  const { prefixCls, tableContext, onImportXls, onExportXls } = useListPage({
    tableProps: {
      title: 'dag任务',
      api: dagList,
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
        width: 340,
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
   * 编辑参数事件
   */
  function handleEditParams(record: Recordable) {
    console.log('open', record.id);
    router.push('/task/dag/detail?id=' + record.id);
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
    const res = await startTask({ id: record.id });
    openDagRunningModal(true, {
      task_id: record.id,
      running_id: res.task_uuid,
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
        label: '编辑',
        onClick: handleEdit.bind(null, record),
        auth: ['dag:edit'],
      },
      {
        label: '任务配置',
        onClick: handleEditParams.bind(null, record),
        auth: ['dag:edit'],
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
        auth: ['dag:copy'],
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
        auth: ['dag:status'],
      },
      {
        label: '删除',
        popConfirm: {
          title: '确定删除吗?',
          confirm: handleDelete.bind(null, record),
        },
        auth: ['dag:delete'],
      },
    ];
  }
</script>

<style scoped></style>
