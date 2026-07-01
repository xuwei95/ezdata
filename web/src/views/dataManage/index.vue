<template>
  <div class="app-container data-manage">
    <splitpanes class="default-theme" style="height: calc(100vh - 120px)">
      <!-- 左:数据源 → 数据模型 树 -->
      <pane size="22" min-size="15">
        <div class="left-panel">
          <div class="left-toolbar">
            <el-button type="primary" size="small" icon="Plus" @click="sourceModalRef.open()">新建数据源</el-button>
            <el-button size="small" icon="Refresh" circle @click="reloadTree" />
          </div>
          <el-tree ref="treeRef" :load="loadNode" lazy node-key="key" :props="{ label: 'label', isLeaf: 'isLeaf' }"
            highlight-current @node-click="onNodeClick" class="src-tree">
            <template #default="{ data }">
              <span class="tree-node">
                <el-icon v-if="data.nodeType === 'source'"><Coin /></el-icon>
                <el-icon v-else><Grid /></el-icon>
                <span class="label">{{ data.label }}</span>
                <span v-if="data.nodeType === 'source'" class="dot" :class="data.status" />
              </span>
            </template>
          </el-tree>
        </div>
      </pane>

      <!-- 右:Tab -->
      <pane>
        <div class="right-panel" v-if="current">
          <el-tabs v-model="activeTab" class="right-tabs">
            <el-tab-pane label="基本信息" name="info">
              <!-- 数据源信息 -->
              <template v-if="current.nodeType === 'source'">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="名称">{{ current.raw.name }}</el-descriptions-item>
                  <el-descriptions-item label="编码">{{ current.raw.code }}</el-descriptions-item>
                  <el-descriptions-item label="类型">{{ current.raw.sourceType }}</el-descriptions-item>
                  <el-descriptions-item label="族">{{ current.raw.family }}</el-descriptions-item>
                  <el-descriptions-item label="状态">
                    <el-tag :type="current.raw.status === 'ok' ? 'success' : current.raw.status === 'failed' ? 'danger' : 'info'">
                      {{ current.raw.status }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="能力">
                    <el-tag v-for="c in capsOf(current.raw.sourceType)" :key="c" size="small" class="cap">{{ c }}</el-tag>
                  </el-descriptions-item>
                </el-descriptions>
                <div style="margin-top: 12px">
                  <el-button icon="Connection" @click="testConn(current.raw)">测试连接</el-button>
                  <el-button icon="Edit" @click="sourceModalRef.open(current.raw)">编辑</el-button>
                  <el-button type="primary" icon="Plus" @click="openModelModal(current.raw)">从表新建模型</el-button>
                  <el-button type="danger" icon="Delete" @click="removeSource(current.raw)">删除</el-button>
                </div>
              </template>
              <!-- 数据模型信息 -->
              <template v-else>
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="名称">{{ current.raw.name }}</el-descriptions-item>
                  <el-descriptions-item label="对象">{{ current.raw.objectName }}</el-descriptions-item>
                  <el-descriptions-item label="数据源">{{ current.raw.datasourceCode }}</el-descriptions-item>
                  <el-descriptions-item label="授权">{{ current.raw.auth }}</el-descriptions-item>
                  <el-descriptions-item label="描述" :span="2">{{ current.raw.remark || '—' }}</el-descriptions-item>
                </el-descriptions>
                <div style="margin-top: 12px">
                  <el-button type="primary" icon="Edit" @click="openEditModel(current.raw)">编辑模型(描述/字段说明)</el-button>
                  <el-button type="danger" icon="Delete" @click="removeModel(current.raw)">删除</el-button>
                </div>
                <vxe-table :data="current.raw.fields || []" height="300" border style="margin-top: 12px">
                  <vxe-column type="seq" width="60" />
                  <vxe-column field="name" title="字段" />
                  <vxe-column field="type" title="类型" />
                  <vxe-column field="nullable" title="可空" width="70" />
                  <vxe-column field="comment" title="业务说明" />
                </vxe-table>
              </template>
            </el-tab-pane>

            <el-tab-pane label="数据查询" name="query"
              v-if="current.nodeType === 'model' && capsOf(current.sourceType).includes('READ')">
              <DataQueryTab :model="current.raw" />
            </el-tab-pane>

            <el-tab-pane label="数据接口" name="api"
              v-if="current.nodeType === 'model' && capsOf(current.sourceType).includes('GEN_API')">
              <DataInterfaceTab :model="current.raw" />
            </el-tab-pane>

            <el-tab-pane label="知识库" name="rag">
              <KnowledgeBaseTab :model="current.raw" :node-type="current.nodeType" />
            </el-tab-pane>
          </el-tabs>
        </div>
        <el-empty v-else description="请选择左侧数据源 / 数据模型" />
      </pane>
    </splitpanes>

    <!-- 新建数据源 -->
    <DataSourceModal ref="sourceModalRef" @ok="reloadTree" />

    <!-- 新建 / 编辑数据模型 -->
    <el-dialog :title="modelModal.id ? '编辑数据模型' : '从表新建数据模型'" v-model="modelModal.visible"
      width="760px" append-to-body>
      <el-form label-width="90px">
        <el-form-item label="表/索引" v-if="!modelModal.id">
          <el-select v-model="modelModal.table" filterable placeholder="选择表" style="width: 100%"
            @change="onTableChange">
            <el-option v-for="t in modelModal.tables" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="对象" v-else>{{ modelModal.objectName }}</el-form-item>
        <el-form-item label="模型名称">
          <el-input v-model="modelModal.name" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="modelModal.remark" type="textarea" :rows="4"
            placeholder="该表的业务描述,帮助 AI 理解(如:订单主表,记录每笔交易;关键字段口径:status=PAID 已支付、amount 单位分)" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="saveModel">确定</el-button>
        <el-button @click="modelModal.visible = false">取消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="DataManage">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'
import DataSourceModal from './components/DataSourceModal.vue'
import DataQueryTab from './components/DataQueryTab.vue'
import DataInterfaceTab from './components/DataInterfaceTab.vue'
import KnowledgeBaseTab from './components/KnowledgeBaseTab.vue'
import {
  getSourceTypes, listSource, testSource, delSource, listTables, listColumns,
  listModel, addModel, getModel, updateModel, delModel,
} from '@/api/dataManage/data'

const treeRef = ref()
const sourceModalRef = ref()
const current = ref(null)
const activeTab = ref('info')
const capsMap = ref({})

onMounted(async () => {
  const res = await getSourceTypes()
  capsMap.value = Object.fromEntries((res.data || []).map((t) => [t.sourceType, t.capabilities || []]))
})

const capsOf = (type) => capsMap.value[type] || []

// 懒加载树:level0 = 数据源;source 节点 = 其数据模型
async function loadNode(node, resolve) {
  if (node.level === 0) {
    const res = await listSource({ pageNum: 1, pageSize: 200 })
    return resolve((res.rows || []).map((s) => ({
      key: 's_' + s.id, label: s.name, nodeType: 'source', status: s.status, raw: s, isLeaf: false,
    })))
  }
  if (node.data.nodeType === 'source') {
    const res = await listModel({ datasourceCode: node.data.raw.code, pageNum: 1, pageSize: 200 })
    return resolve((res.rows || []).map((m) => ({
      key: 'm_' + m.id, label: m.name, nodeType: 'model', sourceType: node.data.raw.sourceType, raw: m, isLeaf: true,
    })))
  }
  return resolve([])
}

function reloadTree() {
  current.value = null
  if (treeRef.value) {
    treeRef.value.store.root.loaded = false
    treeRef.value.store.root.expand()
  }
}

async function onNodeClick(data) {
  if (data.nodeType === 'model') {
    // 拉最新模型详情(含 fields)
    const m = (await getModel(data.raw.id)).data
    current.value = { nodeType: 'model', sourceType: data.sourceType, raw: m }
  } else {
    current.value = { nodeType: 'source', raw: data.raw }
  }
  // 保持当前 tab(切换模型时不跳回"基本信息");仅当该 tab 对新节点不可用时才回退 info
  const st = current.value.sourceType || current.value.raw?.sourceType
  const caps = capsOf(st)
  const isModel = current.value.nodeType === 'model'
  const tabOk = { info: true, rag: true, query: isModel && caps.includes('READ'), api: isModel && caps.includes('GEN_API') }
  if (!tabOk[activeTab.value]) activeTab.value = 'info'
}

async function testConn(src) {
  const res = await testSource({ id: src.id })
  res.data.success ? ElMessage.success('连接成功') : ElMessage.error('连接失败: ' + res.data.message)
}

async function removeSource(src) {
  await ElMessageBox.confirm(`删除数据源「${src.name}」?`, '提示', { type: 'warning' })
  await delSource(src.id)
  ElMessage.success('删除成功')
  reloadTree()
}

// ---- 新建 / 编辑模型 ----
const modelModal = reactive({
  visible: false, id: '', source: null, tables: [], table: '', name: '', remark: '', objectName: '', fields: [],
})

async function openModelModal(src) {
  Object.assign(modelModal, {
    visible: true, id: '', source: src, table: '', name: '', remark: '', objectName: '', fields: [],
  })
  modelModal.tables = (await listTables(src.id)).data || []
}
// 编辑已有模型:只改业务名和描述(结构/字段以实时 introspect 为准,不在此维护)
function openEditModel(m) {
  Object.assign(modelModal, {
    visible: true, id: m.id, source: null, table: '', name: m.name, remark: m.remark || '',
    objectName: m.objectName, fields: m.fields || [],
  })
}
async function onTableChange(table) {
  modelModal.name = table
  modelModal.fields = (await listColumns(modelModal.source.id, table)).data || []
}
async function saveModel() {
  if (modelModal.id) {
    await updateModel({ id: modelModal.id, name: modelModal.name, remark: modelModal.remark })
    ElMessage.success('已保存')
  } else {
    if (!modelModal.table) { ElMessage.warning('请选择表'); return }
    await addModel({
      name: modelModal.name, datasourceCode: modelModal.source.code, kind: 'table',
      objectName: modelModal.table, dbSchema: (modelModal.source.config || {}).database || '',
      remark: modelModal.remark, fields: modelModal.fields, auth: 'query,extract,api',
    })
    ElMessage.success('模型创建成功')
  }
  modelModal.visible = false
  reloadTree()
}

async function removeModel(m) {
  await ElMessageBox.confirm(`删除数据模型「${m.name}」?`, '提示', { type: 'warning' })
  await delModel(m.id)
  ElMessage.success('删除成功')
  reloadTree()
}

</script>

<style scoped lang="scss">
.data-manage { padding: 10px; }
.left-panel { height: 100%; border-right: 1px solid #ebeef5; padding-right: 6px; }
.left-toolbar { display: flex; gap: 6px; padding: 6px 4px; }
.right-panel { padding: 0 12px; }
.tree-node { display: flex; align-items: center; gap: 6px; }
.tree-node .label { font-size: 13px; }
.tree-node .dot { width: 8px; height: 8px; border-radius: 50%; background: #c0c4cc; }
.tree-node .dot.ok { background: #67c23a; }
.tree-node .dot.failed { background: #f56c6c; }
.cap { margin-right: 4px; }
</style>
