<template>
  <div class="bg-white m-4 mr-0 overflow-hidden">
    <a-spin :spinning="loading">
      <!--数据模型树-->
      <BasicTree
        v-if="!treeReloading"
        title="数据模型列表"
        toolbar
        search
        showLine
        :checkStrictly="true"
        :clickRowToExpand="true"
        :treeData="treeData"
        :selectedKeys="selectedKeys"
        :expandedKeys="expandedKeys"
        :autoExpandParent="autoExpandParent"
        @select="onSelect"
        @expand="onExpand"
        @search="onSearch"
      />
    </a-spin>
  </div>
</template>

<script lang="ts" setup>
  import { inject, nextTick, ref } from 'vue';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { BasicTree } from '/@/components/Tree';
  import { queryModelTree } from '../dataquery.api';
  const prefixCls = inject('prefixCls');
  const emit = defineEmits(['select']);
  const { createMessage } = useMessage();
  let loading = ref<boolean>(false);
  // 数据模型树列表数据
  let treeData = ref<any[]>([]);
  // 当前展开的项
  let expandedKeys = ref<any[]>([]);
  // 当前选中的项
  let selectedKeys = ref<any[]>([]);
  // 是否自动展开父级
  let autoExpandParent = ref<boolean>(true);
  // 树组件重新加载
  let treeReloading = ref<boolean>(false);
  // 加载信息
  function loadTreeData() {
    loading.value = true;
    treeData.value = [];
    queryModelTree()
      .then((res) => {
        if (Array.isArray(res)) {
          treeData.value = res;
          autoExpandParentNode();
        }
      })
      .finally(() => (loading.value = false));
  }
  loadTreeData();
  // 自动展开父节点，只展开一级
  function autoExpandParentNode() {
    let keys: Array<any> = [];
    treeData.value.forEach((item, index) => {
      if (item.children && item.children.length > 0) {
        if (index === 0) {
          // 默认选中第一个子节点
          setSelectedKey(item.children[0].id, item.children[0]);
        }
        keys.push(item.key);
      }
    });
    if (keys.length > 0) {
      reloadTree();
      expandedKeys.value = keys;
    }
  }
  // 重新加载树组件，防止无法默认展开数据
  async function reloadTree() {
    await nextTick();
    treeReloading.value = true;
    await nextTick();
    treeReloading.value = false;
  }
  /**
   * 设置当前选中的行
   */
  function setSelectedKey(key: string, data?: object) {
    selectedKeys.value = [key];
    if (data) {
      emit('select', data);
    }
  }
  // 搜索事件
  function onSearch(value: string) {
    if (value) {
      loading.value = true;
      queryModelTree({ keyWord: value })
        .then((result) => {
          if (Array.isArray(result)) {
            treeData.value = result;
          } else {
            createMessage.warning('未查询到信息');
            treeData.value = [];
          }
        })
        .finally(() => (loading.value = false));
    } else {
      loadTreeData();
    }
  }
  // 树选择事件
  function onSelect(selKeys, event) {
    if (selKeys.length > 0 && selectedKeys.value[0] !== selKeys[0]) {
      setSelectedKey(selKeys[0], event.selectedNodes[0]);
    } else {
      // 这样可以防止用户取消选择
      setSelectedKey(selectedKeys.value[0]);
    }
  }
  // 树展开事件
  function onExpand(keys) {
    expandedKeys.value = keys;
    autoExpandParent.value = false;
  }
</script>
<style lang="less" scoped>
  /*升级antd3后，查询框与树贴的太近，样式优化*/
  ::v-deep(.jeecg-tree-header) {
    margin-bottom: 6px;
  }
</style>
