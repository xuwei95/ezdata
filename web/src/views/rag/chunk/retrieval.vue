<template>
  <div>
    <!--引用表格-->
    <BasicTable @register="registerTable">
      <!--字段回显插槽-->
      <template #htmlSlot="{ text }">
        <div v-html="text"></div>
      </template>
    </BasicTable>
  </div>
</template>

<script lang="ts" name="chunk-Chunk" setup>
  import { BasicTable } from '@/components/Table';
  import { useListPage } from '@/hooks/system/useListPage';
  import { retrievalColumns, retrievalFormSchema } from './chunk.data';
  import { retrieval } from './chunk.api';
  //注册table数据
  const { prefixCls, tableContext } = useListPage({
    tableProps: {
      title: '知识检索',
      api: retrieval,
      columns: retrievalColumns,
      canResize: true,
      showActionColumn: false,
      formConfig: {
        labelWidth: 120,
        schemas: retrievalFormSchema,
        autoSubmitOnEnter: true,
        showAdvancedButton: false,
        fieldMapToNumber: [],
        fieldMapToTime: [],
      },
    },
  });

  const [registerTable] = tableContext;
</script>

<style scoped></style>
