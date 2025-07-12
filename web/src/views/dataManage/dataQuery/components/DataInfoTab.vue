<template>
  <Description @register="registerDesc" />
</template>

<script lang="ts" setup>
  import { watch, onMounted } from 'vue';
  import { Description, useDescription } from '/@/components/Description/index';
  import { descSchema } from '../dataquery.data';
  const props = defineProps({
    data: { type: Object, default: () => ({}) },
    rootTreeData: { type: Array, default: () => [] },
  });
  const [registerDesc, { setDescProps }] = useDescription({
    data: props.data,
    schema: descSchema,
    column: 1,
    labelStyle: {
      width: '180px',
    },
  });
  function setData(data) {
    setDescProps({ data });
  }

  onMounted(() => {
    watch(
      () => props.data,
      () => setData(props.data),
      { immediate: true }
    );
  });
</script>
