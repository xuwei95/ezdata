<template>
  <BasicDrawer v-bind="$attrs" @register="registerDrawer" destroyOnClose showFooter title="api列表" :width="'800px'">
    <ApiTokenList :app_id="app_id" />
  </BasicDrawer>
</template>

<script lang="ts" name="taskHistoryDrawer" setup>
  import { ref } from 'vue';
  import { BasicDrawer, useDrawerInner } from '/@/components/Drawer';
  import ApiTokenList from './ApiTokenList.vue';
  let app_id = ref('');
  const [registerDrawer] = useDrawerInner(async (data) => {
    app_id.value = data.record.id;
    console.log('app_id', app_id, data);
  });
</script>

<style scoped></style>
