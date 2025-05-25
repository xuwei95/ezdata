<template>
  <div>
    <!--引用表格-->
    <BasicTable @register="registerTable" >
      <!--字段回显插槽-->
      <template #htmlSlot="{ text }">
        <div v-html="text"></div>
      </template>
    </BasicTable>
  </div>
</template>

<script lang="ts" name="worker-Worker" setup>
  import { BasicTable, useTable, TableAction } from '/@/components/Table';
  import { useModal } from '/@/components/Modal';
  import { useListPage } from '/@/hooks/system/useListPage';
  import { columns, searchFormSchema } from './log.data';
  import { list } from './log.api';
  //注册table数据
  const { prefixCls, tableContext } = useListPage({
    tableProps: {
      // title: '日志管理',
      rowKey: '_id',
      api: list,
      columns,
      canResize: false,
      showActionColumn: false,
      formConfig: {
        //labelWidth: 120,
        schemas: searchFormSchema,
        autoSubmitOnEnter: true,
        showAdvancedButton: true,
        fieldMapToNumber: [],
        fieldMapToTime: [],
      },
    },
  });

  const [registerTable, { reload }] = tableContext;
</script>

<style scoped></style>
