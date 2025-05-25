<template>
  <div v-if="nodeInfo && nodeInfo.params">
    <a-form ref="nodeForm" :model="nodeInfo" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }" :rules="rules">
      <a-form-item label="节点id" name="id">
        {{ node_id }}
      </a-form-item>
      <a-form-item label="任务模版" name="template_code">
        {{ nodeInfo.params.template_code }}
      </a-form-item>
      <a-form-item label="节点名称" name="label">
        <a-input v-model:value="nodeInfo.label" style="width: 300px" />
      </a-form-item>
      <a-form-item label="重试次数" name="retry">
        <a-input-number v-model:value="nodeInfo.params.retry" min="0" style="width: 300px" />
      </a-form-item>
      <a-form-item label="重试间隔" name="countdown">
        <a-input-number v-model:value="nodeInfo.params.countdown" min="0" style="width: 300px" />(秒)
      </a-form-item>
      <a-form-item label="失败策略" name="error_type">
        <a-radio-group v-model:value="nodeInfo.params.error_type" name="radioGroup" style="width: 300px">
          <a-radio value="break">跳过</a-radio>
          <a-radio value="throw">中断</a-radio>
        </a-radio-group>
      </a-form-item>
    </a-form>
    <div style="width: 400px; text-align: center">
      <a-button @click="handleSubmit" type="primary">确认</a-button>
    </div>
  </div>
</template>

<script lang="ts" setup>
  import { watch, onMounted, ref } from 'vue';
  // Emits声明
  const emit = defineEmits(['submit']);
  const props = defineProps({
    data: { type: Object, default: () => ({}) },
    rootTreeData: { type: Array, default: () => [] },
  });
  const nodeInfo = ref({});
  const node_id = ref('');
  const nodeForm = ref(null);
  function setData(data) {
    node_id.value = data.id;
    nodeInfo.value = data.data;
    console.log('set Data', data, nodeInfo.value);
  }
  //表单提交事件
  async function handleSubmit() {
    try {
      const node_info = nodeInfo.value;
      console.log('submit666', node_info);
      emit('submit', node_info);
    } finally {
    }
  }
  onMounted(() => {
    watch(
      () => props.data,
      () => setData(props.data),
      { immediate: true }
    );
  });
</script>
