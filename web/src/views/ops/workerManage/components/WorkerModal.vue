<template>
  <BasicModal v-bind="$attrs" @register="registerModal" defaultFullScreen destroyOnClose showFooter :title="title" :width="'100%'" @ok="handleSubmit">
    <a-button @click="fetchData">刷新</a-button>
    <a-tabs defaultActiveKey="tasks">
      <a-tab-pane tab="任务" key="tasks" forceRender>
        <a-table bordered :columns="active_columns" :data-source="workerInfo.active">
          <template #bodyCell="{ column, text, record }">
            <template v-if="column.key === 'time_start'">
              {{ record.start_time }}
            </template>
            <template v-else-if="column.key === 'kwargs'">
              {{ record.kwargs }}
            </template>
            <template v-else-if="column.key === 'action'">
              <a-popconfirm
                title="确认停止任务?"
                @confirm="handleStopTask(record)"
              >
                <a>停止</a>
              </a-popconfirm>
            </template>
          </template>
        </a-table>
      </a-tab-pane>
      <a-tab-pane tab="队列" key="queues">
        <JDictSelectTag v-model:value="queue_name" placeholder="请输入队列" dictCode="celery_queue" style="width: 300px" />
        <a-button @click="handleAddQueue">添加</a-button>
        <a-table :columns="queues_columns" :data-source="workerInfo.active_queues">
          <template #bodyCell="{ column, text, record }">
            <template v-if="column.key === 'name'">
              {{ render.renderDict(text, 'celery_queue').children || text }}
            </template>
            <template v-if="column.key === 'action'">
              <a-popconfirm
                title="确认删除订阅队列?"
                @confirm="handleDelQueue(record)"
              >
                <a>删除</a>
              </a-popconfirm>
            </template>
          </template>
        </a-table>
      </a-tab-pane>
      <a-tab-pane tab="进程" key="pool">
        <div>
          Worker PID: {{ workerInfo.stats.pid }} <br/>
          进程 PID: {{ workerInfo.stats.pool.processes }} <br/>
          进程并发数: {{ workerInfo.stats.pool.processes.length }}
        </div>
        <div>
          <a-input-number v-model:value="concurrency" :min="1" :max="10" style="width: 200px" />
          <a-button @click="handleAddConcurrency">增加并发</a-button>
          <a-button @click="handleReduceConcurrency">减少并发</a-button>
        </div>
      </a-tab-pane>
    </a-tabs>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, unref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { getInfoById, stopTask, addQueue, delQueue, addConcurrency, reduceConcurrency } from '../worker.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { render } from '/@/utils/common/renderUtils';
  import { JDictSelectTag } from '/@/components/Form';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const isUpdate = ref(true);
  const workerInfo = ref({});
  const workerRecord = ref({});
  const queue_name = ref('');
  const concurrency = ref(1);
  //设置标题
  const title = 'worker详情';
  const active_columns = [
    {
      title: '进程pid',
      dataIndex: 'worker_pid',
      key: 'worker_pid',
    },
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '开始时间',
      dataIndex: 'time_start',
      key: 'time_start',
    },
    {
      title: '任务参数',
      dataIndex: 'kwargs',
      key: 'kwargs',
    },
    {
      title: '操作',
      key: 'action',
    },
  ];
  const queues_columns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '路由名称',
      dataIndex: 'routing_key',
      key: 'routing_key',
    },
    {
      title: '别名',
      dataIndex: 'alias',
      key: 'alias',
    },
    {
      title: '队列参数',
      dataIndex: 'queue_arguments',
      key: 'queue_arguments',
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
    },
  ];
  const { createMessage } = useMessage();
  //表单赋值
  const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
    setModalProps({ confirmLoading: false, showCancelBtn: !!data?.showFooter, showOkBtn: !!data?.showFooter });
    isUpdate.value = !!data?.isUpdate;
    if (unref(isUpdate)) {
      // 请求详情接口拿到详情数据
      workerRecord.value = data.record;
      await fetchData();
    }
  });
  async function fetchData() {
    try {
      const res_data = await getInfoById({ workername: workerRecord.value.hostname });
      if (res_data) {
        workerInfo.value = res_data.records[0];
      } else {
        console.log('error', res_data);
      }
    } catch (error) {
      console.log('error', error);
    }
  }
  /**
   * 删除任务
   */
  async function handleStopTask(record) {
    await stopTask({ task_id: record.id });
    await fetchData();
  }
  /**
   * 添加队列
   */
  async function handleAddQueue() {
    await addQueue({ workername: workerRecord.value.hostname, queue: queue_name.value });
    await fetchData();
  }
  /**
   * 删除队列
   */
  async function handleDelQueue(record) {
    console.log(record);
    await delQueue({ workername: workerRecord.value.hostname, queue: record.name });
    await fetchData();
  }
  /**
   * 增加并发
   */
  async function handleAddConcurrency() {
    await addConcurrency({ workername: workerRecord.value.hostname, concurrency: concurrency.value });
    await fetchData();
  }
  /**
   * 减少并发
   */
  async function handleReduceConcurrency() {
    await reduceConcurrency({ workername: workerRecord.value.hostname, concurrency: concurrency.value });
    await fetchData();
  }
  //表单提交事件
  async function handleSubmit(v) {
    try {
      setModalProps({ confirmLoading: true });
      //关闭弹窗
      closeModal();
      //刷新列表
      emit('success');
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
