<template>
  <BasicDrawer v-bind="$attrs" @register="registerDrawer" destroyOnClose showFooter title="执行历史" :width="'800px'">
    <taskHistory :task_id="task_id" :task_type="'task'" />
  </BasicDrawer>
</template>

<script lang="ts" name="taskHistoryDrawer" setup>
  import { ref } from 'vue';
  import { BasicDrawer, useDrawerInner } from '/@/components/Drawer';
  import taskHistory from '../components/taskHistory/index.vue';
  let task_id = ref('');
  const [registerDrawer] = useDrawerInner(async (data) => {
    task_id.value = data.record.id;
    console.log('task_id', task_id, data);
  });
</script>

<style scoped></style>
