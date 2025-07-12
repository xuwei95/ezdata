<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose showFooter :title="title" :width="'800px'" @ok="handleSubmit">
    <a-tooltip title="刷新">
      <a-button type="primary" shape="circle" size="large" @click="fetchLogs">
        <Icon icon="ant-design:redo-outlined" />
      </a-button>
    </a-tooltip>
    系统日志前缀：<a-switch v-model:checked="show_more" />
    <div class="log-panel">
      <div v-if="task_logs.length > 0">
        <li v-for="item in task_logs" :key="item._id" class="infinite-list-item">
          <span v-if="show_more">
            {{ item['asctime'] + ' ' + item.filename + ' [' + item.lineno + '] ' + item.levelname + ':' + item.message }}
          </span>
          <span v-else>
            {{ item.message }}
          </span>
        </li>
      </div>
      <div v-else>暂无数据</div>
    </div>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { taskLogs } from '../../task.api';
  import Icon from '/@/components/Icon/src/Icon.vue';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const task_logs = ref([]);
  const task_id = ref('');
  const show_more = ref(false);
  //表单赋值
  const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
    //重置表单
    setModalProps({ confirmLoading: false, showCancelBtn: !!data?.showFooter, showOkBtn: !!data?.showFooter });
    task_id.value = data.data.id;
    // 请求日志接口
    await fetchLogs();
  });
  //设置标题
  const title = '任务日志';
  async function fetchLogs() {
    try {
      const res_data = await taskLogs({ task_id: task_id.value, pagesize: 1000 });
      if (res_data) {
        console.log(res_data);
        task_logs.value = res_data.records;
      } else {
        console.log('error', res_data);
      }
    } catch (error) {
      console.log('error', error);
    }
  }
  async function handleSubmit(v) {
    // 刷新列表
    emit('success');
    //关闭弹窗
    closeModal();
  }
</script>

<style lang="less" scoped>
  .log-panel {
    height: 500px;
    color: white;
    overflow: scroll;
    background: #002a35;
  }
  /** 时间和数字输入框样式 */
  :deep(.ant-input-number) {
    width: 100%;
  }
  :deep(.ant-calendar-picker) {
    width: 100%;
  }
</style>
