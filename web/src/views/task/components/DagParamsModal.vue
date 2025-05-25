<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose showFooter :title="title" :width="'800px'" @ok="handleSubmit">
    <div v-if="templateInfo.type === 1">
      <component ref="componentForm" :is="componentMap.get(templateInfo.component)" :taskParams="taskParams" :templateInfo="templateInfo" />
    </div>
    <div v-if="templateInfo.type === 2">
      <dynamicTaskForm ref="dynamicForm" :taskParams="taskParams" :templateInfo="templateInfo" />
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { getTemplateParams } from '../task.api';
  import dynamicTaskForm from './dynamicTaskForm.vue';
  import { componentMap } from './templates/index';
  const dynamicForm = ref(null);
  const componentForm = ref(null);
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  // 任务模版信息
  const templateInfo = ref({});
  // 任务参数
  const taskParams = ref({});
  const nodeInfo = ref({});
  const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
    setModalProps({ confirmLoading: false, showCancelBtn: !!data?.showFooter, showOkBtn: !!data?.showFooter });
    // 获取节点信息
    nodeInfo.value = data.data;
    console.log('modal', data, nodeInfo.value);
    taskParams.value = data.data.params.task_conf;
    console.log(taskParams.value, nodeInfo.value.params.template_code);
    // 请求接口拿到详情数据
    try {
      const res_data = await getTemplateParams({ code: nodeInfo.value.params.template_code });
      if (res_data) {
        // 重置任务组件及参数
        templateInfo.value = res_data;
        console.log(55555, res_data);
        console.log(66666, templateInfo.value.component, componentMap, componentMap.get(templateInfo.value.component));
      } else {
        console.log('error', res_data);
      }
    } catch (error) {
      console.log('error', error);
    }
  });
  //设置标题
  const title = '任务编辑';
  //表单提交事件
  async function handleSubmit(v) {
    try {
      setModalProps({ confirmLoading: true });
      if (templateInfo.value.type === 1) {
        taskParams.value = await componentForm.value.genTaskParams();
        console.log(1111111111, taskParams.value);
      } else {
        taskParams.value = await dynamicForm.value.genTaskParams();
        console.log(2222222222, taskParams.value);
      }
      const node_info = nodeInfo.value;
      node_info.params.task_conf = taskParams.value;
      console.log('node submit', node_info);
      // 更新节点信息
      emit('success', node_info);
      //关闭弹窗
      closeModal();
    } finally {
      setModalProps({ confirmLoading: false });
    }
  }
</script>

<style lang="less" scoped>
  /** 时间和数字输入框样式 */
  :deep(.ant-input-number) {
    width: 100%;
  }
  :deep(.ant-calendar-picker) {
    width: 100%;
  }
</style>
