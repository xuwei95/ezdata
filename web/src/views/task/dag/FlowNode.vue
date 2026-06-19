<template>
  <div class="dag-node" :class="status">
    <span class="dur" v-if="dur">⏱ {{ dur }}</span>
    <el-icon class="ico"><Operation /></el-icon>
    <div class="body">
      <div class="name" :title="label">{{ label }}</div>
      <div class="tpl">{{ templateCode }}</div>
    </div>
    <span class="badge" :class="status" v-if="status">{{ statusText }}</span>
  </div>
</template>

<script setup name="DagFlowNode">
import { inject, ref, onMounted } from 'vue'

const getNode = inject('getNode')
const label = ref('')
const templateCode = ref('')
const status = ref('')
const dur = ref('')

const STATUS_TEXT = { PENDING: '排队', STARTED: '运行', SUCCESS: '成功', FAILURE: '失败', SKIPPED: '跳过' }
const statusText = ref('')

function sync(data) {
  label.value = data?.label || data?.name || '未命名'
  templateCode.value = data?.template_code || ''
  status.value = (data?.status || '').toLowerCase()
  statusText.value = STATUS_TEXT[data?.status] || ''
  dur.value = data?.dur || ''
}

onMounted(() => {
  const node = getNode()
  sync(node.getData())
  node.on('change:data', ({ current }) => sync(current))
})
</script>

<style scoped>
.dag-node {
  position: relative; display: flex; align-items: center; gap: 8px;
  width: 100%; height: 100%; padding: 0 10px; cursor: pointer;
  background: #fff; border: 1px solid #dcdfe6; border-left: 4px solid #409eff;
  border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,.08); box-sizing: border-box;
}
.dag-node:hover { border-color: #409eff; box-shadow: 0 2px 8px rgba(64,158,255,.25); }
.dag-node.success { border-left-color: #67c23a; }
.dag-node.failure { border-left-color: #f56c6c; }
.dag-node.started { border-left-color: #e6a23c; }
.dag-node.skipped { border-left-color: #909399; }
.dag-node .ico { color: #409eff; font-size: 18px; }
.dag-node .body { flex: 1; overflow: hidden; }
.dag-node .name { font-size: 13px; color: #303133; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dag-node .tpl { font-size: 11px; color: #909399; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dag-node .badge { font-size: 11px; padding: 0 6px; border-radius: 8px; color: #fff; }
.dag-node .badge.success { background: #67c23a; }
.dag-node .badge.failure { background: #f56c6c; }
.dag-node .badge.started { background: #e6a23c; }
.dag-node .badge.skipped { background: #909399; }
.dag-node .badge.pending { background: #c0c4cc; }
.dag-node .dur { position: absolute; top: -16px; left: 2px; font-size: 11px; color: #909399; white-space: nowrap; }
</style>
