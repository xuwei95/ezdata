<template>
  <div class="low-code-editor-wrapper">
    <DagEditor
      ref="dagEditor"
      @node-click="nodeClick"
      @node-db-click="nodeDbClick"
      @get-graph="getGraph"
    />
    <div class="low-code-editor-settings">
      <a-card :style="{ width: '100%', height: '100%' }" title="任务节点">
        <a-tabs defaultActiveKey="base-info">
          <a-tab-pane tab="基本信息" key="base-info" style="position: relative">
            <div>
              <NodeInfoTab :data="selectedNode" @submit="handleSuccess" />
            </div>
          </a-tab-pane>
          <a-tab-pane tab="执行历史" key="history-info">
            <div>
              <taskHistory :task_id="selectedNode.id" :task_type="'node'" />
            </div>
          </a-tab-pane>
        </a-tabs>
      </a-card>
    </div>
  </div>
  <DagParamsModal @register="registerDagParamsModal" @success="handleSuccess" />
</template>

<script lang="ts" setup>
  // 业务层，仅处理业务数据，请求都放在该组件
  import { ref } from 'vue';
  import { Graph } from '@antv/x6';
  import DagEditor from './components/dag-editor.vue';
  import DagParamsModal from '../../components/DagParamsModal.vue';
  import NodeInfoTab from './components/NodeInfoTab.vue';
  import taskHistory from '../../components/taskHistory/index.vue';
  import { useModal } from '/@/components/Modal';
  import { useMessage } from '/@/hooks/web/useMessage';
  const selectedNode = ref('');
  const dagEditor = ref(null);
  const graph = ref<any>(null);
  const { createMessage } = useMessage();
  const getGraph = (instance: Graph) => {
    graph.value = instance;
  };
  const [registerDagParamsModal, { openModal: openDagParamsModal }] = useModal();
  // 单击节点事件
  const nodeClick = (obj: any) => {
    selectedNode.value = obj.node;
    const node = graph.value.getCellById(selectedNode.value.id);
    console.log('succ', graph, node);
    const data = node.getData();
    node.setData({
      ...data,
      status: status,
    });
    console.log('click666', selectedNode, selectedNode.value, obj.node);
  };
  // 双击节点事件
  const nodeDbClick = (obj: any) => {
    selectedNode.value = obj.node;
    console.log('db-click666', selectedNode, selectedNode.value, obj.node);
    openDagParamsModal(true, {
      data: selectedNode.value.data,
      isUpdate: true,
      showFooter: true,
    });
  };
  async function handleSuccess(record: Recordable) {
    console.log('update node', record);
    selectedNode.value.setData(record);
    console.log(selectedNode.value, graph);
    const node = graph.value.getCellById(selectedNode.value.id);
    console.log('succ', graph, node);
    node.setData(record);
    // graph.value.
    console.log('set', graph, node);
    createMessage.success('节点更新成功');
  }
</script>

<style scoped lang="less">
  .low-code-editor-wrapper {
    display: flex;
    min-width: 800px;
    width: 100%;
    height: 100%;

    .low-code-editor-settings {
      width: 600px;
      min-width: 600px;
    }
  }
</style>
