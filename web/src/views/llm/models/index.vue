<template>
  <div>
    <BasicTable @register="registerTable">
      <template #tableTitle>
        <a-button type="primary" @click="handleAdd" preIcon="ant-design:plus-outlined">新增模型</a-button>
      </template>
      <template #action="{ record }">
        <TableAction :actions="getTableAction(record)" :dropDownActions="getDropDownAction(record)" />
      </template>
    </BasicTable>
    <ModelModal @register="registerModal" @success="handleSuccess" />
  </div>
</template>

<script lang="ts" setup>
  import { onMounted } from 'vue';
  import { BasicTable, TableAction } from '/@/components/Table';
  import { useModal } from '/@/components/Modal';
  import { useListPage } from '/@/hooks/system/useListPage';
  import ModelModal from './components/ModelModal.vue';
  import { columns, searchFormSchema } from './models.data';
  import { modelList, modelDelete, modelSetDefault, providerList } from './models.api';
  import { useMessage } from '/@/hooks/web/useMessage';

  const { createMessage } = useMessage();
  const [registerModal, { openModal }] = useModal();

  const { tableContext } = useListPage({
    tableProps: {
      title: '模型管理',
      api: modelList,
      columns,
      canResize: false,
      formConfig: {
        schemas: searchFormSchema,
        autoSubmitOnEnter: true,
        showAdvancedButton: false,
        fieldMapToNumber: [],
        fieldMapToTime: [],
      },
      actionColumn: { width: 200, fixed: 'right' },
    },
  });

  const [registerTable, { reload, getForm }] = tableContext;

  onMounted(async () => {
    try {
      const data = await providerList();
      const options = [
        { label: '全部', value: '' },
        ...(Array.isArray(data) ? data : []).map((p: any) => ({ label: p.name, value: p.code })),
      ];
      getForm().updateSchema([{ field: 'provider', componentProps: { options } }]);
    } catch (e) {}
  });

  function handleAdd() {
    openModal(true, { isUpdate: false, showFooter: true });
  }

  function handleEdit(record) {
    openModal(true, { isUpdate: true, record, showFooter: true });
  }

  function handleSuccess() {
    reload();
  }

  async function handleDelete(record) {
    try {
      await modelDelete({ id: record.id });
      createMessage.success('删除成功');
      reload();
    } catch (e: any) {
      createMessage.error(e?.message || '删除失败');
    }
  }

  async function handleSetDefault(record) {
    try {
      await modelSetDefault({ id: record.id });
      createMessage.success('设置成功');
      reload();
    } catch (e: any) {
      createMessage.error(e?.message || '设置失败');
    }
  }

  function getTableAction(record) {
    return [
      { label: '编辑', onClick: handleEdit.bind(null, record) },
      { label: '设为默认', onClick: handleSetDefault.bind(null, record) },
    ];
  }

  function handleCopy(record) {
    const copied = { ...record, id: '', name: record.name + ' 副本', is_default: 0 };
    openModal(true, { isUpdate: false, record: copied, showFooter: true });
  }

  function getDropDownAction(record) {
    return [
      { label: '复制', onClick: handleCopy.bind(null, record) },
      {
        label: '删除',
        popConfirm: {
          title: '确定删除该模型?',
          confirm: handleDelete.bind(null, record),
        },
      },
    ];
  }
</script>
