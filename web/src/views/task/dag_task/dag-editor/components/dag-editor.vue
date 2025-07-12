<template>
  <div v-show="showMenu" style="z-index: 999">
    <div id="stencil" class="low-code-stencil"></div>
  </div>
  <div class="low-code-editor-wrapper">
    <div class="low-code-container">
      <div class="low-code-toolbar">
        <a-button @click="showMenu = !showMenu">
          <template #icon>
            <icon-play-arrow />
          </template>
          {{ showMenu ? '收起组件菜单' : '展开组件菜单' }}
        </a-button>
        <a-button v-auth="'dag_detail:run'" @click="toolbarClick('play')">
          <template #icon>
            <icon-play-arrow />
          </template>
          运行
        </a-button>
        <a-button :disabled="!canUndo" @click="toolbarClick('undo')">
          <template #icon>
            <icon-undo />
          </template>
          撤销
        </a-button>
        <a-button :disabled="!canRedo" @click="toolbarClick('redo')">
          <template #icon>
            <icon-redo />
          </template>
          还原
        </a-button>
        <a-button v-auth="'dag_detail:delete'" @click="toolbarClick('clear')">
          <template #icon>
            <icon-eraser />
          </template>
          删除选中
        </a-button>
        <a-button @click="toolbarClick('centerFn')">
          <template #icon>
            <icon-save />
          </template>
          适应屏幕
        </a-button>
        <a-button @click="toolbarClick('save')">
          <template #icon>
            <icon-save />
          </template>
          保存
        </a-button>
      </div>
      <div id="graph" class="low-code-graph"></div>
    </div>
  </div>
  <DagRunningModal @register="registerModal" @success="handleSuccess" />
</template>

<script setup lang="ts">
  import { onMounted, reactive, ref } from 'vue';
  import { Graph, Addon } from '@antv/x6';
  import FlowGraph from './graph/flow-graph';
  import { MenuGroup } from '../components/graph/types';
  import { dagMenu, saveOrUpdate, getParamsById, startTask } from '../../../task.api';
  import { useRoute } from 'vue-router';
  import { ExclamationCircleOutlined } from '@ant-design/icons-vue';
  import { createVNode } from 'vue';
  import { Modal } from 'ant-design-vue';
  import { useModal } from '/@/components/Modal';
  import DagRunningModal from '../components/DagRunningModal.vue';
  //注册Modal
  const [registerModal, { openModal }] = useModal();
  // 任务id
  const task_id = ref('');
  // 运行的任务实例id
  const running_id = ref('');
  const route = useRoute();

  const emits = defineEmits([
    'getGraph',
    'nodeClick',
    'nodeDbClick',
    'play',
    'refresh',
    'redo',
    'undo',
    'clear',
  ]);
  let showMenu = ref<boolean>(false);
  let menuData = reactive<MenuGroup[]>([]);
  // 是否可以还原
  const canRedo = ref<boolean>(false);
  // 是否可以撤销
  const canUndo = ref<boolean>(false);
  // 以下均为x6的对象
  let history: any = null;
  let graph: Graph;
  let stencil: Addon.Stencil;

  /**
   * 初始化节点点击事件
   */
  const initNodeClickEvent = () => {
    graph.on('node:click', (node) => {
      emits('nodeClick', node);
    });
    graph.on('node:dblclick', (node) => {
      emits('nodeDbClick', node);
    });
    // 节点移入画面时绑定节点并打开任务配置弹窗
    graph.on('node:added', (node) => {
      emits('nodeClick', node);
      emits('nodeDbClick', node);
    });
  };
  /**
   * 初始化历史记录变化事件监听
   */
  const initHistoryStore = () => {
    history = graph.history;
    history.on('change', () => {
      canRedo.value = history.canRedo();
      canUndo.value = history.canUndo();
    });
  };
  /**
   * 初始化流程图绘制
   */
  const initFlowGraph = () => {
    graph = FlowGraph.create(document.getElementById('graph') as HTMLElement);
    stencil = FlowGraph.initStencil(
      document.getElementById('stencil') as HTMLElement,
      menuData as any[]
    );
    emits('getGraph', graph);
    initNodeClickEvent();
    initHistoryStore();
  };
  const playRun = async () => {
    const res = await startTask({ id: task_id.value, trigger: 'once' });
    // 测试运行，绑定running_id
    running_id.value = res.task_uuid || '';
    openModal(true, {
      task_id: task_id.value,
      running_id: running_id.value,
      isUpdate: true,
      showFooter: true,
    });
  };
  // 工具栏类型及其事件处理回调
  const optTypes = {
    // 播放
    play: async () => {
      // 将图谱内容的节点和边转成json结构
      const graphJSON = graph.toJSON();
      // 保存参数
      await saveOrUpdate({ id: task_id.value, params: graphJSON, is_scheduler: false }, true);
      await playRun();
    },
    // 复原
    redo: () => {
      graph.redo();
      emits('redo');
    },
    // 回撤
    undo: () => {
      graph.undo();
      emits('undo');
    },
    // 适应屏幕
    centerFn: () => {
      const num = 1 - graph.zoom();
      num > 1 ? graph.zoom(num * -1) : graph.zoom(num);
      graph.centerContent();
    },
    // 删除选中节点
    clear: () => {
      Modal.confirm({
        title: '删除确认',
        icon: createVNode(ExclamationCircleOutlined),
        content: createVNode('div', { style: 'color:red;' }, '确认删除选中?'),
        onOk() {
          const cells = graph.getSelectedCells();
          if (cells && cells.length) {
            graph.removeCells(cells);
          }
          emits('clear');
        },
        onCancel() {
          console.log('Cancel');
        },
        class: 'test',
      });
    },
    // 保存
    save: async () => {
      // 将图谱内容的节点和边转成json结构
      const graphJSON = graph.toJSON();
      await saveOrUpdate({ id: task_id.value, params: graphJSON }, true);
    },
  };

  /**
   * 工具栏点击事件处理
   * @param type
   */
  const toolbarClick = (type: any) => {
    // eslint-disable-next-line no-unused-expressions
    optTypes[type] && optTypes[type]();
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
    } else {
      console.log('error', res);
    }
  };
  onMounted(async () => {
    // 加载任务菜单
    const res_data = await dagMenu({});
    if (res_data) {
      menuData = res_data;
    } else {
      console.log('error', res_data);
    }
    task_id.value = route.query.id;
    // 初始化图
    initFlowGraph();
    // 初始化任务dag节点参数
    await initGraphData();
  });
</script>

<style lang="less">
  .low-code-stencil {
    position: relative;
    width: 300px;
    height: 100%;
    z-index: 999;
    background-color: var(--color-bg-3);
  }
  .low-code-editor-wrapper {
    display: flex;
    width: 100%;
    height: 100%;
    padding: 8px 10px;
    background-color: var(--color-fill-2);

    .low-code-container {
      display: flex;
      flex: 1;
      flex-direction: column;
      height: 100%;
      background-color: var(--color-bg-3);

      .low-code-toolbar {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 40px;

        button {
          margin-left: 5px;
        }
      }

      .low-code-graph {
        width: 100%;
        height: 100%;
        flex: 1;
      }

      .x6-widget-minimap {
        position: absolute;
        right: 0;
      }
    }
  }
</style>
