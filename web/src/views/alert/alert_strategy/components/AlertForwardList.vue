<template>
  <div class="m-4">
    <div v-for="(item, index) in forwardList" :key="index">
      <a-card title="转发配置" style="margin-bottom: 10px">
        <template #extra><a-button type="link" @click="delConf(index)">删除</a-button></template>
        <a-form
          :model="item"
          name="basic"
          :label-col="{ span: 4 }"
          :wrapper-col="{ span: 20 }"
          autocomplete="off"
        >
          <a-form-item
            label="转发类型"
            name="type"
            :rules="[{ required: true, message: '请选择转发类型' }]"
          >
            <a-select
              v-model:value="item.type"
              style="width: 300px"
              placeholder="请选择转发类型"
              :options="forwardTypeOptions"
            />
          </a-form-item>
          <a-form-item
            v-if="item.type === 'notice'"
            label="通知用户"
            name="user_list"
            :rules="[{ message: '请选择通知用户' }]"
          >
            <JSelectUser
              v-model:value="item.notice_users"
              placeholder="请选择通知用户"
            />
          </a-form-item>
          <a-form-item
            v-if="item.type === 'kafka'"
            label="kafka地址"
            name="bootstrap_servers"
            :rules="[{ required: true, message: '请输入kafka地址' }]"
          >
            <a-input
              v-model:value="item.bootstrap_servers"
              style="width: 600px"
              placeholder="请输入kafka地址"
            />
          </a-form-item>
          <a-form-item
            v-if="item.type === 'kafka'"
            label="kafka topic"
            name="topic"
            :rules="[{ required: true, message: '请输入kafka topic' }]"
          >
            <a-input
              v-model:value="item.topic"
              style="width: 600px"
              placeholder="请输入kafka topic"
            />
          </a-form-item>
          <a-form-item
            v-if="item.type === 'webhook'"
            label="webhook地址"
            name="webhook_url"
            :rules="[{ required: true, message: '请输入webhook地址' }]"
          >
            <a-input
              v-model:value="item.webhook_url"
              style="width: 600px"
              placeholder="请输入webhook地址"
            />
          </a-form-item>
          <a-form-item
            v-if="item.type === 'webhook'"
            label="请求方式"
            name="webhook_method"
            :rules="[{ required: true, message: '请选择请求方式' }]"
          >
            <a-select
              v-model:value="item.webhook_method"
              style="width: 300px"
              placeholder="请选择转发类型"
              :options="[
                { label: 'GET', value: 'GET' },
                { label: 'POST', value: 'POST' },
              ]"
            />
          </a-form-item>
          <a-form-item
            v-if="item.type === 'webhook'"
            label="请求头"
            name="webhook_header"
          >
            <MonacoEditor
              v-model:value="item.webhook_header"
              language="json"
              style="width: 600px"
            />
          </a-form-item>
        </a-form>
      </a-card>
    </div>
    <a-button type="primary" @click="addConf">添加</a-button>
  </div>
</template>
<script lang="ts" setup>
  import { onMounted, ref, watch } from 'vue';
  import JSelectUser from '/@/components/Form/src/jeecg/components/JSelectUser.vue';
  import MonacoEditor from '/@/components/Form/src/components/MonacoEditor/index.vue';
  const props = defineProps({
    forwardConf: {
      type: Object as PropType<Recordable>,
      default: () => ({}),
    },
  });
  const forwardTypeOptions = [
    { label: '告警转通知', value: 'notice' },
    { label: 'webhook转发', value: 'webhook' },
    { label: 'kafka转发', value: 'kafka' },
  ];
  const forwardList = ref([]);
  // 添加筛选规则
  function addConf() {
    forwardList.value.push({ type: 'notice' });
  }
  // 删除筛选规则
  function delConf(index) {
    forwardList.value.splice(index, 1);
  }
  // 重置参数
  async function initParams() {
    console.log(111, forwardList.value);
    forwardList.value = props.forwardConf;
    console.log(222, forwardList.value);
  }
  // 获取参数
  async function genParams() {
    // todo: 转发列表校验
    return forwardList.value;
  }
  onMounted(async () => {
    await initParams();
  });
  watch(
    () => props.forwardConf,
    () => {
      initParams();
    },
    { deep: true }
  );
  defineExpose({
    genParams,
  });
</script>
