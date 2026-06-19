<template>
  <el-dialog v-model="show" :title="`任务工作流 - ${dagName}`" fullscreen append-to-body
    :close-on-click-modal="false" @opened="onOpened" @close="onClose" class="dag-editor-dialog">
    <div class="dag-editor">
      <!-- 左:模板面板 -->
      <div class="palette">
        <div class="palette-title">任务组件(拖拽到画布)</div>
        <div v-for="t in templates" :key="t.code" class="palette-item" draggable="true"
          @dragstart="onDragStart($event, t)">
          <el-icon><Operation /></el-icon><span>{{ t.name }}</span>
        </div>
      </div>

      <!-- 中:画布 -->
      <div class="canvas-wrap">
        <div class="toolbar">
          <el-button-group>
            <el-button size="small" :disabled="!canUndo" icon="RefreshLeft" @click="graph.undo()">撤销</el-button>
            <el-button size="small" :disabled="!canRedo" icon="RefreshRight" @click="graph.redo()">重做</el-button>
          </el-button-group>
          <el-button size="small" icon="Delete" @click="removeSelected">删除选中</el-button>
          <el-button size="small" icon="FullScreen" @click="fitView">适应屏幕</el-button>
          <el-divider direction="vertical" />
          <el-button size="small" icon="DocumentAdd" @click="onSaveDraft">保存草稿</el-button>
          <el-button size="small" type="warning" icon="Upload" @click="onPublish">发布</el-button>
          <el-dropdown size="small" @command="onVersionCmd" style="margin: 0 8px">
            <el-button size="small" icon="Clock">版本<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item v-if="!versions.length" disabled>暂无发布版本</el-dropdown-item>
                <el-dropdown-item v-for="v in versions" :key="v.id" :command="v">
                  {{ v.version }} {{ v.current ? '(当前)' : '' }} {{ v.remark ? '· ' + v.remark : '' }}
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button size="small" icon="Histogram" @click="openHistory">运行历史</el-button>
          <el-button size="small" icon="Setting" @click="openSettings">设置</el-button>
          <el-divider direction="vertical" />
          <el-button size="small" type="primary" icon="VideoPlay" :loading="running" @click="onRun">运行</el-button>
          <el-button size="small" icon="Aim" :loading="running" @click="onDebug">试运行(草稿)</el-button>
        </div>

        <!-- 监控横幅(醒目,替代隐蔽的退出按钮)-->
        <div v-if="viewRunId" class="monitor-bar" :class="{ fail: runStatus === 'FAILURE', ok: runStatus === 'SUCCESS' }">
          <el-icon><VideoCamera /></el-icon>
          <span class="m-label">监控中</span>
          <el-tag size="small" :type="runTagType">{{ runStatus || '运行中' }}</el-tag>
          <el-progress :percentage="runProgress" :stroke-width="12"
            :status="runStatus === 'FAILURE' ? 'exception' : (runProgress >= 100 ? 'success' : '')" style="width: 200px" />
          <span class="muted">点节点查看日志</span>
          <el-button size="small" type="warning" icon="Close" round @click="exitMonitor" style="margin-left: auto">退出监控 / 返回编辑</el-button>
        </div>

        <div ref="canvasRef" class="canvas"></div>
        <div ref="minimapRef" class="minimap"></div>
      </div>
    </div>

    <!-- 右键菜单 -->
    <ul v-if="ctx.visible" class="ctx-menu" :style="{ left: ctx.x + 'px', top: ctx.y + 'px' }">
      <li @click="ctxRunNode">▶ 运行该节点</li>
      <li @click="ctxConfig">配置参数</li>
      <li @click="ctxNodeHistory">执行历史</li>
      <li class="danger" @click="ctxDelete">删除节点</li>
    </ul>

    <!-- 节点配置抽屉 -->
    <el-drawer v-model="nodeDrawer" :title="`节点配置 - ${curNode?.name || ''}`" size="640px" append-to-body>
      <el-form label-width="80px">
        <el-form-item label="节点名称"><el-input v-model="curNodeName" /></el-form-item>
        <el-form-item label="失败策略">
          <el-radio-group v-model="curErrorPolicy">
            <el-radio value="fail_fast">终止整个工作流</el-radio>
            <el-radio value="continue">跳过(仅跳过其下游,其余继续)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="失败重试">
          <el-input-number v-model="curNodeRetry" :min="0" :max="10" size="small" />
          <span style="margin: 0 6px; color: #909399">次,间隔</span>
          <el-input-number v-model="curNodeCountdown" :min="0" size="small" /><span style="margin-left:6px;color:#909399">秒</span>
        </el-form-item>
      </el-form>
      <el-divider content-position="left">任务参数</el-divider>
      <component v-if="curComp" :is="curComp" ref="nodeFormRef" :task-params="curParams" />
      <el-alert v-else type="info" :closable="false" show-icon title="该模板无对应前端组件" />
      <template #footer>
        <el-button type="primary" @click="applyNode">确定</el-button>
        <el-button @click="nodeDrawer = false">取消</el-button>
      </template>
    </el-drawer>

    <!-- 运行历史抽屉 -->
    <el-drawer v-model="historyDrawer" title="运行历史" size="560px" append-to-body class="run-history-drawer">
      <el-table :data="runs" size="small" @row-click="selectRun" highlight-current-row v-loading="historyLoading">
        <el-table-column label="状态" width="90">
          <template #default="s"><el-tag size="small" :type="tagType(s.row.status)">{{ s.row.status }}</el-tag></template>
        </el-table-column>
        <el-table-column label="进度" width="80"><template #default="s">{{ Math.round(s.row.progress || 0) }}%</template></el-table-column>
        <el-table-column label="开始时间" prop="startTime" show-overflow-tooltip />
        <el-table-column label="结束时间" prop="endTime" show-overflow-tooltip />
      </el-table>
      <div class="muted" style="margin-top:8px">点击某次运行 → 画布按该次状态着色,点节点看日志</div>
    </el-drawer>

    <!-- 节点日志(支持自动刷新)-->
    <el-dialog v-model="logDialog" :title="`节点日志 - ${logTitle}`" width="800px" append-to-body @close="stopLogPoll">
      <div class="log-bar">
        <el-switch v-model="logAuto" active-text="自动刷新(2s)" @change="toggleLogAuto" />
        <el-button size="small" icon="Refresh" @click="refreshLog">刷新</el-button>
        <span class="muted">共 {{ logs.length }} 条</span>
      </div>
      <div ref="logConsoleRef" class="log-console">
        <div v-for="(l, i) in logs" :key="i" :class="['log-line', 'lvl-' + (l.level || 'INFO')]">
          <span class="lt">{{ l.createTime }}</span><span class="ll">{{ l.level }}</span><span>{{ l.content }}</span>
        </div>
        <el-empty v-if="!logs.length" description="暂无日志" :image-size="50" />
      </div>
    </el-dialog>

    <!-- 节点执行历史 -->
    <el-dialog v-model="nodeHistDialog" :title="`节点执行历史 - ${nodeHistTitle}`" width="720px" append-to-body>
      <el-table :data="nodeHist" size="small">
        <el-table-column label="状态" width="90"><template #default="s"><el-tag size="small" :type="tagType(s.row.status)">{{ s.row.status }}</el-tag></template></el-table-column>
        <el-table-column label="开始" prop="startTime" show-overflow-tooltip />
        <el-table-column label="结束" prop="endTime" show-overflow-tooltip />
        <el-table-column label="结果" prop="result" show-overflow-tooltip />
        <el-table-column label="日志" width="70">
          <template #default="s"><el-button link type="primary" @click="viewHistLog(s.row)">查看</el-button></template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- DAG 本体设置 -->
    <el-dialog v-model="settingsDialog" title="工作流设置" width="560px" append-to-body>
      <el-form :model="settings" label-width="100px">
        <el-form-item label="名称" required><el-input v-model="settings.name" /></el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="settings.status" :active-value="1" :inactive-value="0" active-text="启用" inactive-text="停用" />
        </el-form-item>
        <el-form-item label="运行模式">
          <el-radio-group v-model="settings.runType">
            <el-radio :value="1">分布式(各节点分发到 worker 并行)</el-radio>
            <el-radio :value="2">单机(一个进程内顺序跑)</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="触发方式">
          <el-radio-group v-model="settings.triggerType">
            <el-radio :value="1">手动</el-radio>
            <el-radio :value="2">定时</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="Cron" v-if="settings.triggerType === 2">
          <el-input v-model="settings.crontab" placeholder="如 0 0 * * * ?(秒 分 时 日 月 周)">
            <template #append><el-button @click="openCron">生成表达式</el-button></template>
          </el-input>
        </el-form-item>
        <el-form-item label="运行队列"><el-input v-model="settings.runQueue" placeholder="default" /></el-form-item>
        <el-form-item label="失败重试">
          <el-input-number v-model="settings.retry" :min="0" :max="10" size="small" />
          <span style="margin:0 6px;color:#909399">次,间隔</span>
          <el-input-number v-model="settings.countdown" :min="0" size="small" /><span style="margin-left:6px;color:#909399">秒</span>
        </el-form-item>
        <el-form-item label="备注"><el-input v-model="settings.remark" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="saveSettings">保存</el-button>
        <el-button @click="settingsDialog = false">取消</el-button>
      </template>
    </el-dialog>

    <!-- Cron 表达式生成器(复用任务调度同款)-->
    <el-dialog title="Cron表达式生成器" v-model="cronDialog" append-to-body destroy-on-close>
      <crontab ref="crontabRef" :expression="settings.crontab" @hide="cronDialog = false" @fill="cronFill" />
    </el-dialog>
  </el-dialog>
</template>

<script setup name="DagEditor">
import { ref, reactive, computed, nextTick, shallowRef } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { Graph } from '@antv/x6'
import { register } from '@antv/x6-vue-shape'
import { History } from '@antv/x6-plugin-history'
import { Selection } from '@antv/x6-plugin-selection'
import { Keyboard } from '@antv/x6-plugin-keyboard'
import { Snapline } from '@antv/x6-plugin-snapline'
import { MiniMap } from '@antv/x6-plugin-minimap'
import FlowNode from './FlowNode.vue'
import Crontab from '@/components/Crontab'
import { listTemplateAll } from '@/api/task/template'
import { listTaskLog } from '@/api/task/log'
import { getTaskComponent } from '@/views/task/components/templates'
import {
  getDraft, saveDraft, publishDag, listVersions, getVersionGraph, rollbackDag,
  runDag, debugDag, dagRunStatus, listRuns, nodeHistory, runNode, getDagDetail, saveDagSettings
} from '@/api/task/dag'

const props = defineProps({ modelValue: Boolean, dagId: String, dagName: String })
const emit = defineEmits(['update:modelValue'])
const show = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })

if (!window.__dagNodeRegistered) {
  register({
    shape: 'dag-node', width: 180, height: 48, component: FlowNode,
    ports: {
      groups: {
        in: { position: 'top', attrs: { circle: { r: 5, magnet: true, stroke: '#409eff', strokeWidth: 1, fill: '#fff' } } },
        out: { position: 'bottom', attrs: { circle: { r: 5, magnet: true, stroke: '#409eff', strokeWidth: 1, fill: '#fff' } } }
      },
      items: [{ group: 'in' }, { group: 'out' }]
    }
  })
  window.__dagNodeRegistered = true
}

const canvasRef = ref()
const minimapRef = ref()
let graph = null
const templates = ref([])
const canUndo = ref(false)
const canRedo = ref(false)
const versions = ref([])

// 节点配置
const nodeDrawer = ref(false)
const curNode = ref(null)
const curNodeName = ref('')
const curNodeRetry = ref(0)
const curNodeCountdown = ref(0)
const curErrorPolicy = ref('fail_fast')
const curParams = ref({})
const curComp = shallowRef(null)
const nodeFormRef = ref()

// 运行 / 监控
const running = ref(false)
const runStatus = ref('')
const runProgress = ref(0)
const viewRunId = ref('')           // 非空 = 监控态(点节点看日志)
const runNodeMap = ref({})          // node_key -> {id,status,result,name}
let pollTimer = null
const runTagType = computed(() => tagType(runStatus.value))
function tagType(s) { return { SUCCESS: 'success', FAILURE: 'danger', STARTED: 'warning', SKIPPED: 'info', PENDING: 'info' }[s] || 'info' }

// 运行历史 / 日志 / 节点历史 / 右键
const historyDrawer = ref(false)
const historyLoading = ref(false)
const runs = ref([])
const logDialog = ref(false)
const logTitle = ref('')
const logs = ref([])
const logInstId = ref('')
const logNodeKey = ref('')   // 监控态正在看日志的节点(完成则停刷)
const logAuto = ref(true)
const logConsoleRef = ref()
let logTimer = null
const nodeHistDialog = ref(false)
const nodeHistTitle = ref('')
const nodeHist = ref([])
const ctx = reactive({ visible: false, x: 0, y: 0, node: null })

// DAG 本体设置
const settingsDialog = ref(false)
const settings = reactive({ name: '', status: 1, runType: 1, triggerType: 1, crontab: '', runQueue: 'default', retry: 0, countdown: 0, remark: '' })
const cronDialog = ref(false)
function openCron() { cronDialog.value = true }
function cronFill(val) { settings.crontab = val }

function genKey() { return 'n_' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6) }
function portId(node, group) { const p = node.getPorts().find((x) => x.group === group); return p && p.id }

async function onOpened() {
  templates.value = ((await listTemplateAll()).data || []).filter((t) => t.code !== 'DagTask')
  await nextTick()
  initGraph()
  await loadDraft()
  loadVersions()
  document.addEventListener('click', closeCtx)
}

function initGraph() {
  if (graph) { graph.dispose(); graph = null }
  graph = new Graph({
    container: canvasRef.value, autoResize: true,
    background: { color: '#f7f8fa' }, grid: { size: 10, visible: true },
    panning: true, mousewheel: { enabled: true, modifiers: ['ctrl', 'meta'] },
    connecting: {
      router: 'manhattan', connector: { name: 'rounded' },
      allowBlank: false, allowLoop: false, allowMulti: false, snap: { radius: 20 },
      validateConnection({ sourceCell, targetCell }) { return sourceCell && targetCell && sourceCell !== targetCell },
      createEdge() {
        return this.createEdge({ attrs: { line: { stroke: '#a0a4ad', strokeWidth: 1.5, targetMarker: { name: 'block', size: 7 } } } })
      }
    }
  })
  graph.use(new History())
  graph.use(new Selection({ rubberband: true, showNodeSelectionBox: true }))
  graph.use(new Keyboard())
  graph.use(new Snapline({ sharp: true }))
  graph.use(new MiniMap({ container: minimapRef.value, width: 180, height: 120, padding: 8 }))
  graph.on('history:change', () => { canUndo.value = graph.canUndo(); canRedo.value = graph.canRedo() })
  // 单击:编辑态→配置;监控态→日志
  graph.on('node:click', ({ node }) => { viewRunId.value ? openNodeLog(node) : openNodeConfig(node) })
  graph.on('node:contextmenu', ({ e, node }) => {
    e.preventDefault(); ctx.node = node; ctx.x = e.clientX; ctx.y = e.clientY; ctx.visible = true
  })
  graph.bindKey(['delete', 'backspace'], () => { removeSelected(); return false })
}

function onDragStart(e, tpl) { e.dataTransfer.setData('tpl', JSON.stringify({ code: tpl.code, name: tpl.name })) }
function bindDrop() {
  canvasRef.value.addEventListener('dragover', (e) => e.preventDefault())
  canvasRef.value.addEventListener('drop', (e) => {
    e.preventDefault()
    const raw = e.dataTransfer.getData('tpl'); if (!raw) return
    const tpl = JSON.parse(raw); const p = graph.clientToLocal({ x: e.clientX, y: e.clientY })
    addNode(tpl, p.x - 90, p.y - 24)
  })
}
function addNode(tpl, x, y) {
  graph.addNode({
    shape: 'dag-node', x, y, width: 180, height: 48,
    data: { node_key: genKey(), label: tpl.name, name: tpl.name, template_code: tpl.code, params: {}, retry: 0, countdown: 0, error_policy: 'fail_fast' }
  })
}

// ---- 节点配置 ----
function openNodeConfig(node) {
  curNode.value = node
  const d = node.getData()
  curNodeName.value = d.name || ''
  curNodeRetry.value = d.retry || 0
  curNodeCountdown.value = d.countdown || 0
  curErrorPolicy.value = d.error_policy || 'fail_fast'
  curParams.value = JSON.parse(JSON.stringify(d.params || {}))
  curComp.value = getTaskComponent(d.template_code) || null
  nodeDrawer.value = true
}
function applyNode() {
  let params = curParams.value
  if (nodeFormRef.value && nodeFormRef.value.genTaskParams) {
    const r = nodeFormRef.value.genTaskParams()
    if (r.error) { ElMessage.error(r.error); return }
    params = r.params || {}
  }
  curNode.value.setData({
    name: curNodeName.value, label: curNodeName.value, retry: curNodeRetry.value,
    countdown: curNodeCountdown.value, error_policy: curErrorPolicy.value, params
  })
  nodeDrawer.value = false
}

// ---- 右键菜单 ----
function closeCtx() { ctx.visible = false }
function ctxConfig() { closeCtx(); openNodeConfig(ctx.node) }
function ctxDelete() { closeCtx(); graph.removeNode(ctx.node) }
async function ctxNodeHistory() {
  const d = ctx.node.getData(); closeCtx()
  nodeHistTitle.value = d.name || d.node_key
  nodeHist.value = (await nodeHistory(props.dagId, d.node_key)).data || []
  nodeHistDialog.value = true
}
async function ctxRunNode() {
  const d = ctx.node.getData(); closeCtx()
  if (!d.params || !Object.keys(d.params).length) { ElMessage.warning('该节点未配置参数,先配置'); return }
  const g = buildSaveGraph(); if (!g) return
  await saveDraft(props.dagId, g)
  const res = await runNode(props.dagId, d.node_key)
  ElMessage.success('已运行该节点,日志自动刷新中')
  logNodeKey.value = ''
  openLogById(res.data.instanceId, d.name || d.node_key, true)
}
function viewHistLog(row) { logNodeKey.value = ''; openLogById(row.id, nodeHistTitle.value, false) }

function removeSelected() { const cells = graph.getSelectedCells(); if (cells?.length) graph.removeCells(cells) }
function fitView() { graph.zoomToFit({ padding: 40, maxScale: 1 }) }

// ---- 序列化 ----
function toGraphJSON() {
  const nodes = graph.getNodes().map((n) => {
    const d = n.getData(); const p = n.getPosition()
    return { node_key: d.node_key, name: d.name, template_code: d.template_code, params: d.params || {}, pos: p, retry: d.retry || 0, countdown: d.countdown || 0, error_policy: d.error_policy || 'fail_fast' }
  })
  const edges = []
  graph.getEdges().forEach((e) => {
    const s = e.getSourceCell(); const t = e.getTargetCell()
    if (s && t) edges.push({ source: s.getData().node_key, target: t.getData().node_key })
  })
  return { nodes, edges, viewport: {} }
}
function renderGraph(g) {
  graph.clearCells()
  const byKey = {}
  ;(g.nodes || []).forEach((nd) => {
    const node = graph.addNode({
      shape: 'dag-node', x: nd.pos?.x ?? 80, y: nd.pos?.y ?? 80, width: 180, height: 48,
      data: { node_key: nd.node_key, label: nd.name, name: nd.name, template_code: nd.template_code, params: nd.params || {}, retry: nd.retry || 0, countdown: nd.countdown || 0, error_policy: nd.error_policy || 'fail_fast' }
    })
    byKey[nd.node_key] = node
  })
  ;(g.edges || []).forEach((e) => {
    const s = byKey[e.source]; const t = byKey[e.target]
    if (s && t) graph.addEdge({
      source: { cell: s.id, port: portId(s, 'out') }, target: { cell: t.id, port: portId(t, 'in') },
      attrs: { line: { stroke: '#a0a4ad', strokeWidth: 1.5, targetMarker: { name: 'block', size: 7 } } }
    })
  })
}
async function loadDraft() {
  bindDrop()
  const res = await getDraft(props.dagId)
  renderGraph(res.data.graph || { nodes: [], edges: [] })
  nextTick(() => fitView())
}

function buildSaveGraph() {
  const g = toGraphJSON()
  if (!g.nodes.length) { ElMessage.warning('画布为空'); return null }
  const keys = g.nodes.map((n) => n.node_key)
  if (g.nodes.some((n) => !n.template_code)) { ElMessage.warning('存在未配置模板的节点'); return null }
  if (hasCycle(keys, g.edges)) { ElMessage.error('图中存在环路'); return null }
  const unconfig = g.nodes.filter((n) => !n.params || !Object.keys(n.params).length)
  if (unconfig.length) ElMessage.warning(`节点未配置参数(单击配置),运行会失败:${unconfig.map((n) => n.name).join('、')}`)
  return g
}
function hasCycle(keys, edges) {
  const adj = {}; keys.forEach((k) => (adj[k] = []))
  edges.forEach((e) => adj[e.source]?.push(e.target))
  const state = {}; let cyc = false
  const dfs = (n) => { state[n] = 0; for (const m of adj[n]) { if (state[m] === 0) { cyc = true; return } if (state[m] === undefined) dfs(m) } state[n] = 1 }
  keys.forEach((k) => { if (state[k] === undefined) dfs(k) })
  return cyc
}

async function onSaveDraft() { const g = buildSaveGraph(); if (!g) return; await saveDraft(props.dagId, g); ElMessage.success('草稿已保存') }
async function onPublish() {
  const g = buildSaveGraph(); if (!g) return
  await saveDraft(props.dagId, g)
  const { value: remark } = await ElMessageBox.prompt('发布说明(可选)', '发布工作流', { inputValue: '' }).catch(() => ({}))
  if (remark === undefined) return
  const res = await publishDag(props.dagId, remark || '')
  ElMessage.success(`已发布版本 ${res.data.version}`); loadVersions()
}
async function loadVersions() { versions.value = (await listVersions(props.dagId)).data || [] }
async function onVersionCmd(v) {
  const action = await ElMessageBox.confirm(`版本 ${v.version}`, '操作', {
    distinguishCancelAndClose: true, confirmButtonText: '回滚为当前', cancelButtonText: '查看'
  }).then(() => 'rollback').catch((a) => (a === 'cancel' ? 'view' : null))
  if (action === 'view') {
    const res = await getVersionGraph(v.id); renderGraph(res.data.graph); nextTick(() => fitView())
    ElMessage.info(`已载入版本 ${v.version}(查看,保存会覆盖草稿)`)
  } else if (action === 'rollback') {
    await rollbackDag(props.dagId, v.id); ElMessage.success('已回滚'); loadVersions()
  }
}

// ---- 运行 / 监控 ----
async function onRun() { await trigger(() => runDag(props.dagId, 'published')) }
async function onDebug() { const g = buildSaveGraph(); if (!g) return; await saveDraft(props.dagId, g); await trigger(() => debugDag(props.dagId)) }
async function trigger(fn) {
  running.value = true; runStatus.value = ''; runProgress.value = 0
  graph.getNodes().forEach((node) => node.setData({ status: '' }))
  try {
    const res = await fn()
    viewRunId.value = res.data.instanceId
    ElMessage.success('已触发,监控运行中…(点节点看日志)')
    startPoll(res.data.instanceId)
  } catch (e) {
    running.value = false
    ElMessage.error('触发失败:' + (e?.msg || e?.message || '未知错误'))
  }
}
const TERMINAL = ['SUCCESS', 'FAILURE', 'SKIPPED']
function fmtDur(start, end) {
  if (!start || !end) return ''
  const ms = new Date(end.replace(' ', 'T')) - new Date(start.replace(' ', 'T'))
  if (!(ms >= 0)) return ''
  const s = ms / 1000
  return s < 60 ? s.toFixed(1) + 's' : Math.floor(s / 60) + 'm' + Math.round(s % 60) + 's'
}
function applyRunStatus(d) {
  runStatus.value = d.run?.status || ''
  runProgress.value = Math.round(d.run?.progress || 0)
  const map = {}
  ;(d.nodes || []).forEach((n) => (map[n.nodeId] = n))
  runNodeMap.value = map
  graph.getNodes().forEach((node) => {
    const n = map[node.getData().node_key]
    const dur = n && TERMINAL.includes(n.status) ? fmtDur(n.startTime, n.endTime) : ''
    node.setData({ status: n ? n.status : '', dur })
  })
  // 正在看日志的节点若已完成 → 收尾刷新并停止自动刷新
  if (logNodeKey.value && logTimer) {
    const st = map[logNodeKey.value]?.status
    if (st && TERMINAL.includes(st)) { refreshLog(); stopLogPoll(); logAuto.value = false }
  }
}
function startPoll(runId) {
  stopPoll()
  pollTimer = setInterval(async () => {
    let d
    try { d = (await dagRunStatus(runId)).data || {} } catch (e) { return }
    applyRunStatus(d)
    if (['SUCCESS', 'FAILURE'].includes(runStatus.value)) {
      stopPoll(); running.value = false
      if (runStatus.value === 'SUCCESS') ElMessage.success('工作流运行成功')
      else {
        const bad = (d.nodes || []).filter((n) => n.status === 'FAILURE')
        ElNotification({
          title: '工作流运行失败', type: 'error', duration: 0,
          message: bad.map((n) => `· ${n.name || n.nodeId}:${(n.result || '').slice(0, 160)}`).join('\n') || (d.run?.result || '未知错误')
        })
      }
    }
  }, 2000)
}
function stopPoll() { if (pollTimer) { clearInterval(pollTimer); pollTimer = null } }
function exitMonitor() {
  stopPoll(); running.value = false; viewRunId.value = ''; runStatus.value = ''; runProgress.value = 0
  graph.getNodes().forEach((node) => node.setData({ status: '' }))
}

// ---- 运行历史 ----
async function openHistory() {
  historyDrawer.value = true; historyLoading.value = true
  try { runs.value = (await listRuns(props.dagId)).data || [] } finally { historyLoading.value = false }
}
async function selectRun(row) {
  stopPoll(); running.value = false
  viewRunId.value = row.id
  historyDrawer.value = false
  const d = (await dagRunStatus(row.id)).data || {}
  applyRunStatus(d)
  // 未结束的历史运行继续轮询
  if (!['SUCCESS', 'FAILURE'].includes(d.run?.status)) startPoll(row.id)
  ElMessage.info('已载入该次运行,点节点看日志')
}

// ---- 节点日志 ----
async function openNodeLog(node) {
  const d = node.getData()
  const inst = runNodeMap.value[d.node_key]
  if (!inst || !inst.id) { ElMessage.info('该节点本次未执行'); return }
  logNodeKey.value = d.node_key
  // 已完成节点不自动刷新
  await openLogById(inst.id, d.name || d.node_key, !TERMINAL.includes(inst.status))
}
async function openLogById(instId, title, autoRefresh = false) {
  logTitle.value = title; logInstId.value = instId; logs.value = []
  logDialog.value = true; logAuto.value = autoRefresh
  await refreshLog()
  if (autoRefresh) startLogPoll(); else stopLogPoll()
}
async function refreshLog() {
  if (!logInstId.value) return
  try { logs.value = (await listTaskLog({ taskUuid: logInstId.value, pageSize: 300 })).rows || [] } catch (e) { return }
  nextTick(() => { const el = logConsoleRef.value; if (el) el.scrollTop = el.scrollHeight })
}
function startLogPoll() { stopLogPoll(); logTimer = setInterval(refreshLog, 2000) }
function stopLogPoll() { if (logTimer) { clearInterval(logTimer); logTimer = null } }
function toggleLogAuto(v) { v ? startLogPoll() : stopLogPoll() }

// ---- DAG 本体设置 ----
async function openSettings() {
  const d = (await getDagDetail(props.dagId)).data || {}
  Object.assign(settings, {
    name: d.name || '', status: d.status ?? 1, runType: d.runType || 1, triggerType: d.triggerType || 1,
    crontab: d.crontab || '', runQueue: d.runQueue || 'default', retry: d.retry || 0, countdown: d.countdown || 0, remark: d.remark || ''
  })
  settingsDialog.value = true
}
async function saveSettings() {
  if (!settings.name.trim()) { ElMessage.warning('请填写名称'); return }
  if (settings.triggerType === 2 && !(settings.crontab || '').trim()) { ElMessage.warning('定时需填 Cron'); return }
  await saveDagSettings(props.dagId, { ...settings })
  ElMessage.success('已保存')
  settingsDialog.value = false
}

function onClose() {
  stopPoll(); stopLogPoll(); document.removeEventListener('click', closeCtx)
  if (graph) { graph.dispose(); graph = null }
  viewRunId.value = ''; runStatus.value = ''; runProgress.value = 0
}
</script>

<style scoped>
.dag-editor { display: flex; height: calc(100vh - 110px); }
.palette { width: 200px; border-right: 1px solid #ebeef5; padding: 8px; overflow-y: auto; }
.palette-title { font-size: 12px; color: #909399; margin-bottom: 8px; }
.palette-item { display: flex; align-items: center; gap: 6px; padding: 8px 10px; margin-bottom: 6px; cursor: grab; border: 1px solid #dcdfe6; border-radius: 6px; background: #fff; font-size: 13px; }
.palette-item:hover { border-color: #409eff; color: #409eff; }
.canvas-wrap { flex: 1; display: flex; flex-direction: column; position: relative; }
.toolbar { display: flex; align-items: center; gap: 6px; padding: 6px 8px; border-bottom: 1px solid #ebeef5; flex-wrap: wrap; }
.muted { font-size: 12px; color: #909399; }
.canvas { flex: 1; }
.monitor-bar {
  display: flex; align-items: center; gap: 10px; padding: 8px 14px;
  background: #ecf5ff; border-bottom: 2px solid #409eff; color: #303133; font-size: 13px;
}
.monitor-bar.ok { background: #f0f9eb; border-bottom-color: #67c23a; }
.monitor-bar.fail { background: #fef0f0; border-bottom-color: #f56c6c; }
.monitor-bar .m-label { font-weight: 600; }
.minimap { position: absolute; right: 8px; bottom: 8px; border: 1px solid #dcdfe6; background: #fff; }
.ctx-menu { position: fixed; z-index: 3000; background: #fff; border: 1px solid #e4e7ed; border-radius: 4px; box-shadow: 0 2px 12px rgba(0,0,0,.12); padding: 4px 0; margin: 0; list-style: none; min-width: 120px; }
.ctx-menu li { padding: 6px 16px; font-size: 13px; cursor: pointer; }
.ctx-menu li:hover { background: #f5f7fa; }
.ctx-menu li.danger { color: #f56c6c; }
.log-console { height: 420px; overflow-y: auto; background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 4px; font-family: Consolas, Monaco, monospace; font-size: 12px; }
.log-line { white-space: pre-wrap; word-break: break-all; line-height: 1.6; }
.log-line .lt { color: #6a9955; margin-right: 8px; }
.log-line .ll { display: inline-block; width: 56px; color: #569cd6; margin-right: 8px; }
.lvl-ERROR .ll, .lvl-ERROR { color: #f48771; }
</style>

<!-- 运行历史行可点击:小手(抽屉 append-to-body,需非 scoped)-->
<style>
.run-history-drawer .el-table__row { cursor: pointer; }
</style>
