<template>
  <a-row :class="['p-4', `${prefixCls}--box`]" type="flex" :gutter="10">
    <a-col :xxl="4" :lg="6" :sm="24" style="margin-bottom: 10px" v-show="isExpanded">
      <DataLeftTree ref="leftTree" @select="onTreeSelect" @rootTreeData="onRootTreeData" />
    </a-col>
    <div class="index-toggle-button-container">
      <div class="index-toggle-button-wrapper" @click="isExpanded = !isExpanded">
        <a-icon class="index-toggle-icon" v-if="isExpanded" type="left-outlined" />
        <a-icon class="index-toggle-icon" v-if="!isExpanded" type="right-outlined" />
      </div>
    </div>
    <a-col :xxl="isExpanded ? 19 : 23" :lg="isExpanded ? 17 : 23" :sm="23" style="margin-bottom: 10px">
      <div style="height: 100%; background-color: white">
        <a-tabs defaultActiveKey="data-query">
          <a-tab-pane tab="基本信息" key="base-info" style="position: relative">
            <div style="padding: 20px">
              <DataFormTab :data="modelData" />
            </div>
          </a-tab-pane>
          <a-tab-pane tab="数据查询" key="data-query">
            <div style="padding: 0 20px 20px">
              <DataQueryTab :data="modelData" />
            </div>
          </a-tab-pane>
          <a-tab-pane tab="数据分析" key="data-chat" style="position: relative">
            <div style="padding: 0 20px 20px; height: 100%">
              <DataChat :model_id="modelData.id" @cancel-model-switch="handleCancelModelSwitch" />
            </div>
          </a-tab-pane>
          <a-tab-pane tab="数据接口" key="data-interface">
            <div style="padding: 0 20px 20px">
              <DataInterFaceTab :data="modelData" />
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </a-col>
  </a-row>
</template>

<script lang="ts" setup name="data-model-query">
  import { provide, ref } from 'vue';
  import { useDesign } from '/@/hooks/web/useDesign';
  import { getInfoById } from './dataquery.api';
  import DataLeftTree from './components/DataLeftTree.vue';
  import DataFormTab from './components/DataInfoTab.vue';
  import DataQueryTab from './components/DataQueryTab.vue';
  import DataChat from './components/DataChat/index.vue';
  import DataInterFaceTab from './components/DataInterFaceTab/index.vue';

  const { prefixCls } = useDesign('model-query');
  provide('prefixCls', prefixCls);
  const isExpanded = ref<boolean>(true);
  // 给子组件定义一个ref变量
  const leftTree = ref();

  // 当前选中
  const modelData = ref({});
  const rootTreeData = ref<any[]>([]);

  // 左侧树选择后触发
  async function onTreeSelect(data) {
    console.log('onTreeSelect: ', data);
    if (data.type == 'datasource') {
      console.log('select source', data);
    } else {
      const res_data = await getInfoById({ id: data.value });
      if (res_data) {
        modelData.value = res_data;
      } else {
        console.log('error', res_data);
      }
    }
  }

  // 左侧树rootTreeData触发
  function onRootTreeData(data) {
    rootTreeData.value = data;
  }

  // 处理取消切换模型事件
  function handleCancelModelSwitch(modelId) {
    if (leftTree.value && modelId) {
      // 找到对应模型ID的树节点并恢复选中状态
      leftTree.value.restoreSelectedNode(modelId);
    }
  }
</script>

<style lang="less">
  @import './index.less';
  .index-toggle-button-container {
    text-align: center;
    line-height: 100%;
  }
  .index-toggle-button-wrapper {
    /* 初始样式 */
    display: inline-block;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .index-toggle-icon {
    margin-top: 300px;
    font-size: 24px; /* 初始字体大小 */
  }

  .index-toggle-button-wrapper:hover .index-toggle-icon {
    /* 悬停时图标的样式 */
    font-size: 40px; /* 放大字体 */
    animation: pulse 1s infinite alternate; /* 应用动画 */
  }

  /* 定义动画 */
  @keyframes pulse {
    from {
      transform: scale(1);
    }
    to {
      transform: scale(1.1);
    }
  }
</style>
