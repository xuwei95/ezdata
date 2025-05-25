<template>
  <div>
    <!--引用表格-->
    <BasicTable @register="registerTable" :rowSelection="rowSelection">
      <!--插槽:table标题-->
      <template #tableTitle>
        <a-button v-auth="'datamodel:add'" type="primary" @click="handleAdd" preIcon="ant-design:plus-outlined"> 新增</a-button>
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
    <DataModelModal @register="registerModal" @success="handleSuccess" />
    <!-- 字段管理区域 -->
    <DataModelFieldList @register="registerDrawer" />
  </div>
</template>

<script lang="ts" name="datamodel-DataModel" setup>
  import { ref, computed, unref } from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { useModal } from '/@/components/Modal';
  import { useDrawer } from '/@/components/Drawer';
  import { useListPage } from '/@/hooks/system/useListPage';
  import DataModelModal from './components/DataModelModal.vue';
  import DataModelFieldList from './components/DataModelFieldList/index.vue';
  import { columns, searchFormSchema } from './datamodel.data';
  import { list, deleteOne, batchDelete, operateOne, getImportUrl, getExportUrl } from './datamodel.api';
  const checkedKeys = ref<Array<string | number>>([]);
  //注册Modal
  const [registerModal, { openModal }] = useModal();
  //注册Drawer
  const [registerDrawer, { openDrawer }] = useDrawer();
  //注册table数据
  const { prefixCls, tableContext, onImportXls, onExportXls } = useListPage({
    tableProps: {
      title: '数据模型管理',
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
        width: 220,
        fixed: 'right',
      },
    },
    importConfig: {
      url: getImportUrl,
      success: handleSuccess,
    },
    exportConfig: {
      name: '数据模型管理导出结果',
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
   * 字段管理事件
   */
  function handleEditField(record: Recordable) {
    openDrawer(true, {
      record,
      showFooter: false,
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
   * 模型操作事件
   */
  async function handleModel(record, operate) {
    await operateOne({ id: record.id, operate: operate }, handleSuccess);
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
        auth: ['datamodel:edit'],
      },
      {
        label: '字段管理',
        onClick: handleEditField.bind(null, record),
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
        auth: ['datamodel:copy'],
      },
      {
        label: '详情',
        onClick: handleDetail.bind(null, record),
      },
      {
        label: '检查状态',
        onClick: handleModel.bind(null, record, 'status'),
      },
      {
        label: '训练知识库',
        onClick: handleModel.bind(null, record, 'train'),
      },
      {
        label: '创建模型',
        popConfirm: {
          title: '确定创建?',
          confirm: handleModel.bind(null, record, 'create'),
        },
        ifShow: record.status == 0 && (record.model_conf.auth_type.indexOf('create') != -1 || false),
      },
      {
        label: '删除模型',
        popConfirm: {
          title: '确定删除模型，删除后数据无法恢复。',
          confirm: handleModel.bind(null, record, 'delete'),
        },
        ifShow: record.status == 1 && (record.model_conf.auth_type.indexOf('delete') != -1 || false),
      },
      {
        label: '删除记录',
        popConfirm: {
          title: '确定删除该条记录?',
          confirm: handleDelete.bind(null, record),
        },
        auth: ['datamodel:delete'],
      },
    ];
  }
</script>

<style scoped></style>
