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
    <ChatAppModal @register="registerModal" @success="handleSuccess" />
    <ApiTokenDrawer @register="registerApiDrawer" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" name="chat_app-ChatApp" setup>
  import { ref, computed, unref } from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { useModal } from '/@/components/Modal';
  import { useListPage } from '/@/hooks/system/useListPage';
  import ChatAppModal from './components/ChatAppModal.vue';
  import { columns, searchFormSchema } from './chat_app.data';
  import { list, deleteOne, batchDelete } from './chat_app.api';
  import { useDrawer } from '@/components/Drawer';
  import ApiTokenDrawer from './components/ApiTokenDrawer/index.vue';
  import { router } from '/@/router';
  const checkedKeys = ref<Array<string | number>>([]);
  //注册Modal
  const [registerModal, { openModal }] = useModal();
  const [registerApiDrawer, { openDrawer: openApiDrawer }] = useDrawer();
  //注册table数据
  const { prefixCls, tableContext } = useListPage({
    tableProps: {
      title: '对话应用管理',
      api: list,
      columns,
      canResize: false,
      formConfig: {
        //labelWidth: 120,
        schemas: searchFormSchema,
        autoSubmitOnEnter: true,
        showAdvancedButton: false,
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
   * api列表
   */
  function handleApi(record: Recordable) {
    router.push({ path: '/ai/app/chat', query: { app_id: record.id } });
  }
   /**
   * 新增事件
   */
   function handleApiToken(record) {
    openApiDrawer(true, {
      record,
      isUpdate: false,
      showFooter: true,
    });
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
        label: '对话',
        onClick: handleApi.bind(null, record),
      },
    ];
  }
  /**
   * 下拉操作栏
   */
  function getDropDownAction(record) {
    return [
      {
        label: 'api列表',
        onClick: handleApiToken.bind(null, record),
      },
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
