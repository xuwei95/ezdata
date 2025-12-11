<template>
  <BasicDrawer v-bind="$attrs" @register="registerDrawer" destroyOnClose :title="title" :width="'900px'" @ok="handleSubmit">
    <!--引用表格-->
    <BasicTable @register="registerTable" :rowSelection="rowSelection">
      <!--插槽:table标题-->
      <template #tableTitle>
        <a-button type="primary" @click="handleAdd" preIcon="ant-design:plus-outlined"> 新增字段</a-button>
        <a-button type="primary" preIcon="ant-design:cloud-sync-outlined" @click="syncFields"> 同步模型字段</a-button>
<!--     <a-button type="primary" preIcon="ant-design:cloud-sync-outlined" @click="checkModelStatus"> 检查模型状态</a-button>-->
<!--        <j-upload-button type="primary" preIcon="ant-design:import-outlined" @click="onImportXls">导入字段</j-upload-button>-->
        <a-button type="primary" preIcon="ant-design:export-outlined" @click="onExportXls"> 导出字段</a-button>
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
  </BasicDrawer>
  <!-- 表单区域 -->
  <DataModelFieldModal @register="registerModal" @success="handleSuccess" :datamodel_id="datamodel_id" :model_type="model_type" />
</template>

<script lang="ts" name="datamodel_field-DataModelField" setup>
  import { ref, computed, unref } from 'vue';
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { useModal } from '/@/components/Modal';
  import { BasicDrawer, useDrawerInner } from '/@/components/Drawer';
  import { useListPage } from '/@/hooks/system/useListPage';
  import DataModelFieldModal from './components/DataModelFieldModal.vue';
  import { columns, searchFormSchema } from './datamodel_field.data';
  import { list, deleteOne, batchDelete, syncOne, getImportUrl, getExportUrl, syncModelFields } from './datamodel_field.api';
  import { ColEx } from '/@/components/Form/src/types';
  const checkedKeys = ref<Array<string | number>>([]);
  const datamodel_id = ref('');
  const model_type = ref('');
  //注册Modal
  const [registerModal, { openModal }] = useModal();
  const [registerDrawer] = useDrawerInner(async (data) => {
    datamodel_id.value = data.record.id;
    model_type.value = data.record.type;
    setProps({ searchInfo: { datamodel_id: unref(datamodel_id) } });
    reload();
  });
  // 自适应列配置
  const adaptiveColProps: Partial<ColEx> = {
    xs: 24, // <576px
    sm: 24, // ≥576px
    md: 24, // ≥768px
    lg: 12, // ≥992px
    xl: 12, // ≥1200px
    xxl: 8, // ≥1600px
  };
  //注册table数据
  const { prefixCls, tableContext, onImportXls, onExportXls } = useListPage({
    tableProps: {
      title: '数据模型字段',
      api: list,
      columns,
      canResize: false,
      formConfig: {
        //labelWidth: 120,
        baseColProps: adaptiveColProps,
        labelCol: {
          offset: 1,
          xs: 24,
          sm: 24,
          md: 24,
          lg: 9,
          xl: 7,
          xxl: 4,
        },
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
      name: '数据模型字段导出结果',
      url: getExportUrl,
    },
  });

  const [registerTable, { setProps, reload }, { rowSelection, selectedRowKeys }] = tableContext;

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
   * 同步字段
   */
  async function handleSync(record: Recordable) {
    await syncOne({ id: record.id }, handleSuccess);
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
   * 同步模型字段
   */
  async function syncFields() {
    await syncModelFields({ id: datamodel_id.value });
    reload();
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
      // {
      //   label: '同步字段',
      //   onClick: handleSync.bind(null, record),
      // },
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
