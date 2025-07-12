<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose defaultFullscreen showFooter :title="title" @cancel="handleClose" @close="handleClose">
    <a-row style="height: 100%; width: 100%">
      <a-col :span="14">
        <div id="graph-run" class="low-code-graph"></div>
      </a-col>
      <a-col :span="10">
        <a-card :style="{ width: '100%', height: '100%' }" title="任务节点">
          <div class="taREDACTEDinfo">
            <a-descriptions title="节点信息" bordered size="small">
              <a-descriptions-item label="节点id">{{ selectedNode.node_id || '' }}</a-descriptions-item>
              <a-descriptions-item label="节点名称">{{ selectedNode.label || '' }}</a-descriptions-item>
              <a-descriptions-item label="任务id">{{ selectedNode.task_id || '' }}</a-descriptions-item>
              <a-descriptions-item label="任务状态">{{ selectedNode.stauts || '' }}</a-descriptions-item>
              <a-descriptions-item label="开始时间">{{ selectedNode.start_time || '' }}</a-descriptions-item>
              <a-descriptions-item label="结束时间">{{ selectedNode.end_time || '' }}</a-descriptions-item>
              <a-descriptions-item label="重试次数">{{ selectedNode.retry_num || 0 }}</a-descriptions-item>
              <a-descriptions-item label="任务结果">{{ selectedNode.result || '' }}</a-descriptions-item>
              <a-descriptions-item label="worker">{{ selectedNode.worker || '' }}</a-descriptions-item>
            </a-descriptions>
          </div>
          <Authority value="task:log">
            <div class="log-info">
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
            </div>
          </Authority>
        </a-card>
      </a-col>
    </a-row>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, onUnmounted } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { Graph } from '@antv/x6';
  import FlowGraph from '/@/views/task/dag_task/dag-editor/components/graph/flow-graph';
  import { dagNodeStatus, getParamsById, taskLogs } from '/@/views/task/task.api';
  import Authority from "@/components/Authority/src/Authority.vue";
  const task_id = ref('');
  const running_id = ref('');
  const running_task_id = ref('');
  const selectedNode = ref('');
  const task_logs = ref([]);
  const timer = ref();
  const show_more = ref(false);
  let graph: Graph;
  /**
   * 初始化节点点击事件
   */
  const initNodeClickEvent = () => {
    graph.on('node:click', (node) => {
      let data = node.node.data;
      selectedNode.value = data;
      running_task_id.value = data.id;
      console.log('click777', data, selectedNode);
    });
  };
  /**
   * 初始化流程图绘制
   */
  const initFlowGraph = () => {
    graph = FlowGraph.create(document.getElementById('graph-run') as HTMLElement);
    initNodeClickEvent();
  };
  // 更新节点状态
  const fetchNodesStatus = async () => {
    // 加载任务节点状态
    const res = await dagNodeStatus({ id: task_id.value, running_id: running_id.value });
    if (res) {
      console.log(res);
      if (res.is_ok) {
        clearInterval(timer.value);
      }
      const child_list = res.child_list;
      child_list?.forEach((item) => {
        const node = graph.getCellById(item.node_id);
        const data = node.getData();
        node.setData({
          ...data,
        });
        node.setData({
          ...item,
        });
        console.log(item);
      });
      console.log('updateStatus', res);
    } else {
      console.log('error', res);
    }
  };
  const initGraphData = async () => {
    // 加载任务参数节点
    const res = await getParamsById({ id: task_id.value });
    if (res) {
      // 请求接口设置图节点和边
      const cell_list = res.params.cells;
      const cells = [];
      cell_list.forEach((item) => {
        if (item.shape === 'edge') {
          cells.push(graph.createEdge(item));
        } else {
          cells.push(graph.createNode(item));
        }
      });
      graph.resetCells(cells);
      // 画布局中
      const num = 1 - graph.zoom();
      num > 1 ? graph.zoom(num * -1) : graph.zoom(num);
      graph.centerContent();
      console.log('init', cells);
      timer.value = setInterval(() => {
        fetchNodesStatus();
      }, 2000);
    } else {
      console.log('error', res);
    }
  };
  const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
    setModalProps({ confirmLoading: false, showCancelBtn: true, showOkBtn: false });
    task_id.value = data.task_id;
    running_id.value = data.running_id;
    // 初始化图
    initFlowGraph();
    // 初始化任务dag节点参数
    await initGraphData();
  });
  //设置标题
  const title = 'dag运行详情';
  //表单提交事件
  async function handleClose() {
    try {
      clearInterval(timer.value);
      timer.value = '';
      console.log('close66666');
      //关闭弹窗
      closeModal();
    } finally {
      setModalProps({ confirmLoading: false });
    }
  }
  // 查询任务日志
  async function fetchLogs() {
    try {
      task_logs.value = [];
      console.log('logs', selectedNode.value);
      if (selectedNode.value.id) {
        const res_data = await taskLogs({ task_id: selectedNode.value.id, pagesize: 1000 });
        if (res_data) {
          console.log(res_data);
          task_logs.value = res_data.records;
        } else {
          console.log('error', res_data);
        }
      }
    } catch (error) {
      console.log('error', error);
    }
  }
  onUnmounted(() => {
    clearInterval(timer.value);
    console.log('distory66666');
    timer.value = '';
  });
</script>

<style lang="less" scoped>
  //.taREDACTEDinfo {
  //  height: 250px;
  //}
  .log-info {
    height: 550px;
  }
  .log-panel {
    height: 400px;
    color: white;
    overflow: scroll;
    background: #002a35;
  }
  .low-code-graph {
    width: 100%;
    height: 100%;
    min-height: 600px;
    flex: 1;
  }
  /** 时间和数字输入框样式 */
  :deep(.ant-input-number) {
    width: 100%;
  }

  :deep(.ant-calendar-picker) {
    width: 100%;
  }
</style>
