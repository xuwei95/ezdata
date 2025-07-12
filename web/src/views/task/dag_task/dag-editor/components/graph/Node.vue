<template>
  <div class="low-code-node" :class="status">
    <img :src="img" alt="" />
    <span class="label">{{ label }}</span>
    <span class="status">
      <img v-if="status === 'success'" :src="image.success" alt="" />
      <img v-else-if="status === 'failed'" :src="image.failed" alt="" />
      <img v-else-if="status === 'running'" :src="image.running" alt="" />
    </span>
  </div>
</template>

<script>
  // 此组件用vue2写，感觉渲染效率要比vue3快一些
  export default {
    // 此处接收graph和node两个参数值，属于vue的祖孙通信方式之一
    inject: ['getGraph', 'getNode'],
    data() {
      return {
        img: '',
        label: '',
        status: '',
        template_code: '',
        params: {},
        // 图片信息
        image: {
          logo: 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*evDjT5vjkX0AAAAAAAAAAAAAARQnAQ',
          success: 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*6l60T6h8TTQAAAAAAAAAAAAAARQnAQ',
          failed: 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*SEISQ6My-HoAAAAAAAAAAAAAARQnAQ',
          running: 'https://gw.alipayobjects.com/mdn/rms_43231b/afts/img/A*t8fURKfgSOgAAAAAAAAAAAAAARQnAQ',
        },
      };
    },
    mounted() {
      // eslint-disable-next-line @typescript-eslint/no-this-alias
      const self = this;
      // 获取到拖拽放置的节点实例
      const node = this.getNode();
      const graph = this.getGraph();
      // 获取到节点实例初始化的值，这个值是通过createNode时添加的data值
      const nodeData = node.getData();
      console.log('init data666', nodeData);
      // 进行赋值
      this.img = nodeData?.img;
      this.label = nodeData?.label;
      this.status = nodeData?.status;
      this.template_code = nodeData?.template_code;
      this.params = nodeData?.params;
      // 监听数据改变事件，这个是x6提供的方法，必须是这种格式，勿动，回调中可以进行修改
      // current 为当前新的值
      // eslint-disable-next-line no-shadow
      node.on('change:data', ({ current }) => {
        console.log('current666', current);
        self.img = current?.img;
        self.label = current?.label;
        self.status = current?.status;
        self.template_code = current?.template_code;
        self.params = current?.params;
        const edges = graph.getIncomingEdges(node);
        const { status } = node.getData();
        edges?.forEach((edge) => {
          // 运行状态动画
          if (status === 'running') {
            edge.attr('line/strokeDasharray', 5);
            edge.attr('line/style/animation', 'low-code-running-line 30s infinite linear');
          } else {
            edge.attr('line/strokeDasharray', '');
            edge.attr('line/style/animation', '');
          }
        });
      });
    },
  };
</script>

<style>
  .low-code-node {
    display: flex;
    align-items: center;
    width: 100%;
    height: 100%;
    background-color: #fff;
    border: 1px solid #c2c8d5;
    border-left: 4px solid #5f95ff;
    border-radius: 4px;
    box-shadow: 0 2px 5px 1px rgba(0, 0, 0, 0.06);
  }

  .low-code-node img {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    margin-left: 8px;
  }

  .low-code-node .label {
    display: inline-block;
    flex-shrink: 0;
    min-width: 104px;
    margin-left: 8px;
    color: #666;
    font-size: 12px;
  }

  .low-code-node .status {
    flex-shrink: 0;
  }

  .low-code-node.success {
    border-left: 4px solid #52c41a;
  }

  .low-code-node.failed {
    border-left: 4px solid #ff4d4f;
  }

  .low-code-node.running {
    border-left: 4px solid #ead671;
  }

  .low-code-node.running .status img {
    animation: low-code-node-spin 1s linear infinite;
  }

  .x6-node-selected .low-code-node {
    /* border-color: #1890ff; */
    border-radius: 2px;
    box-shadow: 0 0 0 4px #d4e8fe;
  }

  .x6-node-selected .low-code-node.success {
    border-color: #52c41a;
    border-radius: 2px;
    box-shadow: 0 0 0 4px #ccecc0;
  }

  .x6-node-selected .low-code-node.failed {
    border-color: #ff4d4f;
    border-radius: 2px;
    box-shadow: 0 0 0 4px #fedcdc;
  }

  .x6-edge:hover path:nth-child(2) {
    stroke: #1890ff;
    stroke-width: 1px;
  }

  .x6-edge-selected path:nth-child(2) {
    stroke: #1890ff;
    stroke-width: 1.5px !important;
  }

  @keyframes low-code-running-line {
    to {
      stroke-dashoffset: -1000;
    }
  }

  @keyframes low-code-node-spin {
    from {
      transform: rotate(0deg);
    }

    to {
      transform: rotate(360deg);
    }
  }
</style>
