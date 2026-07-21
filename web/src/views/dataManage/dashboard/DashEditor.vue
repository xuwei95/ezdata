<template>
  <el-dialog
    v-model="visible"
    :title="dash.id ? '编辑看板' : '新建看板'"
    fullscreen
    append-to-body
    :close-on-click-modal="false"
    class="dash-editor-dialog"
  >
  <div class="dash-editor">
    <div class="de-head">
      <el-input v-model="dash.name" :placeholder="$t('看板名称')" style="width: 220px" />
      <el-tag size="small" type="info">{{ dash.dashType === 'screen' ? '大屏' : '多图看板' }}</el-tag>
      <el-select v-model="dash.refreshInterval" size="small" style="width: 116px" :placeholder="$t('自动刷新')">
        <el-option :value="0" :label="$t('不自动刷新')" />
        <el-option :value="10" :label="$t('每 10 秒')" />
        <el-option :value="30" :label="$t('每 30 秒')" />
        <el-option :value="60" :label="$t('每 1 分钟')" />
      </el-select>
      <el-button type="primary" icon="Check" :disabled="!dash.name" :loading="saving" @click="save">{{ $t('保存') }}</el-button>
      <span class="tip">{{ $t('拖/点左侧加入画布 → 双击组件(或点⚙)配数据 → 拖动/缩放排版 → 保存') }}</span>
    </div>

    <div class="de-body">
      <!-- 左:组件区 -->
      <div class="de-left">
        <el-tabs v-model="leftTab" class="de-tabs">
          <el-tab-pane :label="$t('新建图表')" name="new">
            <div class="de-types">
              <div v-for="t in CHART_TYPES" :key="t.v" class="de-type" draggable="true"
                @click="addChart(t)" @dragstart="onDragStart({ kind: 'chart', t })" @dragend="dragItem = null">
                <el-icon><Histogram /></el-icon><span>{{ t.l }}</span>
              </div>
            </div>
            <el-divider content-position="left">{{ $t('其它') }}</el-divider>
            <el-button size="small" icon="Document" @click="addText">{{ $t('添加文本') }}</el-button>
          </el-tab-pane>
          <el-tab-pane :label="$t('引用看板')" name="ref">
            <el-input v-model="boardKw" size="small" clearable :placeholder="$t('搜索单图看板')" prefix-icon="Search" style="margin-bottom: 6px" />
            <div class="de-board-list">
              <div v-for="b in filteredBoards" :key="b.id" class="de-board" draggable="true"
                @click="addRef(b)" @dragstart="onDragStart({ kind: 'ref', b })" @dragend="dragItem = null">
                <el-icon><PieChart /></el-icon><span class="nm">{{ b.name }}</span><el-icon class="add"><Plus /></el-icon>
              </div>
              <el-empty v-if="!filteredBoards.length" :description="$t('暂无单图看板')" :image-size="48" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 中:画布(支持从左侧拖入) -->
      <div class="de-canvas" :class="{ 'drop-hover': dropHover }"
        @dragover.prevent="dropHover = true" @dragleave="dropHover = false" @drop.prevent="onDrop">
        <DashCanvas
          v-if="dash.components.length"
          :components="dash.components"
          :canvas="dash.canvas"
          editable
          :selected-id="selectedId"
          @update:components="(c) => (dash.components = c)"
          @select-comp="onSelect"
          @edit-comp="onEdit"
          @remove-comp="removeComp"
        />
        <el-empty v-else :description="$t('从左侧拖入 / 点击图表类型加入画布')" />
      </div>
    </div>

    <!-- 图表配置抽屉(DataEase 式:选中组件 → 布局 + 当场配数据/图形) -->
    <el-drawer v-model="cfgDrawer" :title="drawerTitle" size="760px" :with-header="true" append-to-body>
      <!-- 布局/大小(所有组件通用) -->
      <div v-if="selectedComp && selectedComp.pos" class="de-layout">
        <span class="de-layout-lb">{{ $t('布局') }}</span>
        <template v-if="isFree">
          <span class="de-lb">X</span><el-input-number v-model="selectedComp.pos.x" :min="0" :step="10" size="small" controls-position="right" style="width: 96px" @change="pokeComponents" />
          <span class="de-lb">Y</span><el-input-number v-model="selectedComp.pos.y" :min="0" :step="10" size="small" controls-position="right" style="width: 96px" @change="pokeComponents" />
          <span class="de-lb">{{ $t('宽') }}</span><el-input-number v-model="selectedComp.pos.w" :min="80" :step="10" size="small" controls-position="right" style="width: 96px" @change="pokeComponents" />
          <span class="de-lb">{{ $t('高') }}</span><el-input-number v-model="selectedComp.pos.h" :min="60" :step="10" size="small" controls-position="right" style="width: 96px" @change="pokeComponents" />
        </template>
        <template v-else>
          <span class="de-lb">{{ $t('宽(列)') }}</span><el-input-number v-model="selectedComp.pos.w" :min="1" :max="dash.canvas.cols || 24" size="small" controls-position="right" style="width: 96px" @change="pokeComponents" />
          <span class="de-lb">{{ $t('高(行)') }}</span><el-input-number v-model="selectedComp.pos.h" :min="1" size="small" controls-position="right" style="width: 96px" @change="pokeComponents" />
        </template>
      </div>

      <ChartConfigPanel
        v-if="selectedComp && selectedComp.type === 'chart' && selectedInline"
        :comp-id="selectedComp.id"
        :inline="selectedComp.inline || {}"
        :models="models"
        :chart-h="360"
        @update:inline="applyInline"
      />
      <div v-else-if="selectedComp && selectedComp.type === 'chart'" class="de-refhint">
        该组件引用了单图看板「{{ (selectedComp.props && selectedComp.props.title) || '' }}」,请到「单图看板」里修改;或删除后改用「新建图表」内嵌配置。
      </div>
      <div v-else-if="selectedComp && selectedComp.type === 'text'">
        <el-input v-model="selectedComp.props.text" type="textarea" :rows="4" :placeholder="$t('文本内容')" @input="pokeComponents" />
      </div>

      <template #footer>
        <el-button type="danger" plain icon="Delete" @click="removeComp(selectedId)">{{ $t('删除组件') }}</el-button>
        <el-button type="primary" @click="cfgDrawer = false">{{ $t('完成') }}</el-button>
      </template>
    </el-drawer>
  </div>
  </el-dialog>
</template>

<script setup name="DashEditor">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { listModel, listAnalysisTemplate, getDashboard, saveDashboard } from '@/api/dataManage/data'
import DashCanvas from './DashCanvas.vue'
import ChartConfigPanel from './ChartConfigPanel.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false }, // 弹窗显隐
  id: { type: String, default: '' }, // 为空=新建
  dashType: { type: String, default: 'board' } // board / screen
})
const emit = defineEmits(['update:modelValue', 'saved'])
const visible = computed({ get: () => props.modelValue, set: (v) => emit('update:modelValue', v) })
const saving = ref(false)
const leftTab = ref('new')
const models = ref([])
const boards = ref([])
const boardKw = ref('')
const cfgDrawer = ref(false)
const selectedId = ref('')
const dragItem = ref(null) // 从左侧拖入画布的载荷 {kind:'chart'|'ref', t|b}
const dropHover = ref(false)
const dash = reactive({ id: '', name: '', dashType: 'board', canvas: { mode: 'matrix', cols: 24 }, components: [], filters: [], refreshInterval: 0 })

const CHART_TYPES = [
  { v: 'bar', l: '柱状图' }, { v: 'hbar', l: '横向条' }, { v: 'line', l: '折线图' }, { v: 'area', l: '面积图' },
  { v: 'pie', l: '饼图' }, { v: 'donut', l: '环形图' }, { v: 'scatter', l: '散点图' }, { v: 'radar', l: '雷达图' },
  { v: 'funnel', l: '漏斗图' }, { v: 'gauge', l: '仪表盘' }, { v: 'kline', l: 'K 线' }, { v: 'kpi', l: '指标卡' }, { v: 'table', l: '明细表' },
]
const filteredBoards = computed(() =>
  boards.value.filter((b) => !boardKw.value || (b.name || '').toLowerCase().includes(boardKw.value.toLowerCase()))
)
const selectedComp = computed(() => dash.components.find((c) => c.id === selectedId.value) || null)
const selectedInline = computed(() => selectedComp.value && selectedComp.value.inline != null)
const isFree = computed(() => (dash.canvas.mode || 'matrix') === 'free')
// 改布局数字后:替换数组引用触发 DashCanvas(矩阵)重新 sync;free 模板直接绑 pos 亦无害
function pokeComponents() { dash.components = dash.components.slice() }
const drawerTitle = computed(() => (selectedComp.value ? '配置:' + ((selectedComp.value.props && selectedComp.value.props.title) || selectedComp.value.type) : '配置'))
const uid = () => (crypto.randomUUID ? crypto.randomUUID().replace(/-/g, '') : 'c' + Date.now() + Math.floor(Math.random() * 1e6))

// 新组件默认位置/大小:matrix 用栅格单位;free/大屏 用像素(否则 8×6 会变成 8×6px 极小不可见)。多次添加做层叠偏移。
function defaultPos(kind) {
  const n = dash.components.length
  if (isFree.value) {
    const off = (n % 8) * 24
    return kind === 'text' ? { x: 60 + off, y: 60 + off, w: 400, h: 60 } : { x: 60 + off, y: 60 + off, w: 640, h: 360 }
  }
  return kind === 'text' ? { x: 0, y: 0, w: 6, h: 2 } : { x: 0, y: 0, w: 8, h: 6 }
}
// 注意:用"数组再代入"而非 push —— DashCanvas 的 watch(() => components) 是按引用触发,
// push 是原地修改、引用不变,矩阵模式的 layout 不会重新 sync,导致第 2 个起的组件不显示/延迟显示。
function addChart(t) {
  const id = uid()
  dash.components = [...dash.components, { id, type: 'chart', inline: { modelId: '', native: '', chartSpec: { type: t.v } }, pos: defaultPos('chart'), props: { title: t.l }, subscribe: true }]
  selectedId.value = id; cfgDrawer.value = true
}
function addRef(b) {
  const id = uid()
  dash.components = [...dash.components, { id, type: 'chart', ref: { boardId: b.id }, pos: defaultPos('chart'), props: { title: b.name }, subscribe: true }]
  selectedId.value = id
}
// 拖拽加入画布(与点击同效果;grid 自动排布位置)
function onDragStart(payload) { dragItem.value = payload }
function onDrop() {
  dropHover.value = false
  const it = dragItem.value
  dragItem.value = null
  if (!it) return
  if (it.kind === 'chart') addChart(it.t)
  else if (it.kind === 'ref') addRef(it.b)
}
function addText() {
  const id = uid()
  dash.components = [...dash.components, { id, type: 'text', pos: defaultPos('text'), props: { title: '文本', text: '文本内容' } }]
  selectedId.value = id; cfgDrawer.value = true
}
// 单击只选中(高亮),不弹配置;双击 / 组件上「配置」按钮才打开抽屉(对齐 DataEase,避免一碰就弹)
function onSelect(id) { selectedId.value = id }
function onEdit(id) { selectedId.value = id; cfgDrawer.value = true }
function removeComp(id) {
  dash.components = dash.components.filter((c) => c.id !== id)
  if (selectedId.value === id) cfgDrawer.value = false
}
// 配置面板改动 → 写回选中组件的 inline(画布 DashComponent 深监听会重渲)
function applyInline(inl) {
  const c = selectedComp.value
  if (c) c.inline = { ...inl }
}

async function load() {
  // 每次打开重置选中态,避免复用组件实例残留
  selectedId.value = ''
  cfgDrawer.value = false
  const id = props.id
  const dashType = props.dashType === 'screen' ? 'screen' : 'board'
  // 关键:先同步建好画布态(新建立即重置),再异步取模型/看板列表。
  // 否则 await 期间用户拖入组件,会被随后到达的重置覆盖 →「拖进去不落画布」。
  if (id) {
    const d = (await getDashboard(id)).data || {}
    Object.assign(dash, {
      id: d.id, name: d.name || '', dashType: d.dashType || 'board',
      canvas: d.canvas && Object.keys(d.canvas).length ? d.canvas : { mode: dashType === 'screen' ? 'free' : 'matrix', cols: 24 },
      components: d.components || [], filters: d.filters || [], refreshInterval: d.refreshInterval || 0,
    })
  } else {
    Object.assign(dash, {
      id: '', name: '', dashType,
      canvas: { mode: dashType === 'screen' ? 'free' : 'matrix', cols: 24, width: 1920, height: 1080 },
      components: [], filters: [], refreshInterval: 0,
    })
  }
  // 模型/看板列表(放最后:期间用户即便加了组件也不会被覆盖)
  models.value = (await listModel({ pageNum: 1, pageSize: 1000 })).rows || []
  boards.value = (await listAnalysisTemplate()).data || []
}
async function save() {
  if (!dash.name.trim()) { ElMessage.warning('请填写看板名称'); return }
  saving.value = true
  try {
    const { data } = await saveDashboard({
      id: dash.id || undefined, name: dash.name.trim(), dashType: dash.dashType,
      canvas: dash.canvas, components: dash.components, filters: dash.filters, refreshInterval: dash.refreshInterval,
    })
    dash.id = data.id
    ElMessage.success('已保存')
    emit('saved', dash.id)
    visible.value = false
  } catch (e) { ElMessage.error('保存失败: ' + (e?.msg || e?.message || e)) } finally { saving.value = false }
}

watch(() => props.modelValue, (v) => { if (v) load() })
</script>

<style scoped>
.dash-editor { display: flex; flex-direction: column; height: calc(100vh - 130px); }
.de-head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.de-head .tip { font-size: 12px; color: #909399; }
.de-body { flex: 1; min-height: 0; display: flex; gap: 10px; }
.de-left { width: 240px; flex: none; border: 1px solid #ebeef5; border-radius: 6px; padding: 8px; overflow: auto; }
.de-types { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.de-type { display: flex; align-items: center; gap: 6px; padding: 8px; border: 1px solid #ebeef5; border-radius: 6px; cursor: grab; font-size: 13px; }
.de-type:active { cursor: grabbing; }
.de-type:hover { background: #f5f7fa; border-color: var(--el-color-primary); }
.de-board-list { max-height: 52vh; overflow: auto; }
.de-board { display: flex; align-items: center; gap: 6px; padding: 6px 8px; border-radius: 6px; cursor: pointer; font-size: 13px; }
.de-board:hover { background: #f5f7fa; }
.de-board .nm { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.de-board .add { color: var(--el-color-primary); }
.de-canvas { flex: 1; min-width: 0; overflow: auto; border: 1px solid #ebeef5; border-radius: 6px; background: #f5f7fa; padding: 6px; transition: border-color .15s, background .15s; }
.de-canvas.drop-hover { border: 1px dashed var(--el-color-primary); background: #eef5ff; }
.de-refhint { color: #909399; font-size: 13px; line-height: 1.7; }
.de-layout { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; padding: 8px 10px; background: #f5f7fa; border-radius: 6px; }
.de-layout-lb { font-weight: 600; font-size: 13px; color: #303133; margin-right: 4px; }
.de-lb { font-size: 12px; color: #606266; }
</style>
