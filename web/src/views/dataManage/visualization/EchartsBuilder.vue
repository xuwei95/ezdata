<template>
  <div class="echarts-builder" :class="{ 'no-ctrl': !showControls }">
    <!-- 左侧配置面板:数据 / 样式 -->
    <div v-if="showControls" class="eb-panel" :style="{ maxHeight: height + 'px' }">
      <el-tabs v-model="panelTab" class="eb-tabs">
        <!-- ============ 数据 ============ -->
        <el-tab-pane label="数据" name="data">
          <div v-if="aiEnabled" class="fld ai-fld">
            <label>AI 生成图表</label>
            <el-input v-model="aiQuestion" type="textarea" :rows="2" placeholder="一句话描述想要的图,如:各城市销售额 Top10 柱状图"
              @keyup.enter.stop="genAi" />
            <el-button size="small" type="primary" icon="MagicStick" :loading="aiLoading" style="margin-top: 6px" @click="genAi">
              {{ aiLoading ? '生成中…' : '生成图表' }}</el-button>
          </div>
          <div class="fld">
            <label>图表类型</label>
            <el-select v-model="cfg.type" size="small" style="width: 100%">
              <el-option-group v-for="g in TYPE_GROUPS" :key="g.label" :label="g.label">
                <el-option v-for="t in g.items" :key="t.v" :label="t.l" :value="t.v" />
              </el-option-group>
            </el-select>
          </div>

          <template v-if="cfg.type !== 'table'">
            <div class="fld">
              <label>{{ cfg.type === 'kpi' ? '标签维度(可选)' : '类别 / 维度' }}</label>
              <el-select v-model="cfg.x" size="small" filterable clearable placeholder="选择字段" style="width: 100%">
                <el-option v-for="f in fields" :key="f" :label="f" :value="f" />
              </el-select>
            </div>

            <div class="fld">
              <label>度量 / 指标</label>
              <div v-for="(m, i) in cfg.ys" :key="i" class="ys-row">
                <el-select v-model="m.field" size="small" filterable placeholder="字段" style="flex: 1">
                  <el-option v-for="f in fields" :key="f" :label="f" :value="f" />
                </el-select>
                <el-select v-model="m.agg" size="small" style="width: 82px">
                  <el-option v-for="a in AGGS" :key="a.v" :label="a.l" :value="a.v" />
                </el-select>
                <el-button size="small" icon="Delete" text :disabled="cfg.ys.length <= 1" @click="removeY(i)" />
              </div>
              <el-button size="small" text type="primary" icon="Plus" @click="addY">添加度量</el-button>
            </div>

            <div v-if="allowSeries" class="fld">
              <label>分组 / 拆分(可选)</label>
              <el-select v-model="cfg.series" size="small" filterable clearable placeholder="按此字段拆多系列" style="width: 100%">
                <el-option v-for="f in fields" :key="f" :label="f" :value="f" />
              </el-select>
            </div>

            <div v-if="cfg.type !== 'kpi' && cfg.type !== 'gauge'" class="fld">
              <label>排序</label>
              <div class="row2">
                <el-select v-model="cfg.sort.by" size="small" style="flex: 1">
                  <el-option label="默认" value="" />
                  <el-option label="按类别" value="__x__" />
                  <el-option v-for="m in cfg.ys" :key="m.field" :label="'按 ' + m.field" :value="m.field" />
                </el-select>
                <el-select v-model="cfg.sort.dir" size="small" style="width: 82px" :disabled="!cfg.sort.by">
                  <el-option label="降序" value="desc" />
                  <el-option label="升序" value="asc" />
                </el-select>
              </div>
            </div>

            <div v-if="cfg.type !== 'kpi' && cfg.type !== 'gauge'" class="fld">
              <label>Top-N(0 = 不限)</label>
              <el-input-number v-model="cfg.topN" :min="0" :max="1000" size="small" controls-position="right" style="width: 100%" />
            </div>
          </template>
          <el-alert v-else type="info" :closable="false" show-icon title="明细表直接展示查询结果的所有字段,无需配置维度/度量" />
        </el-tab-pane>

        <!-- ============ 样式 ============ -->
        <el-tab-pane label="样式" name="style">
          <div class="fld">
            <label>标题</label>
            <el-input v-model="cfg.style.title" size="small" clearable placeholder="留空不显示" />
          </div>

          <template v-if="cfg.type !== 'table'">
            <div v-if="cfg.type !== 'kpi'" class="fld inline">
              <label>图例</label>
              <el-switch v-model="cfg.style.legend" size="small" />
              <el-select v-model="cfg.style.legendPos" size="small" style="width: 96px; margin-left: auto" :disabled="!cfg.style.legend">
                <el-option label="上" value="top" />
                <el-option label="下" value="bottom" />
                <el-option label="左" value="left" />
                <el-option label="右" value="right" />
              </el-select>
            </div>

            <div v-if="cfg.type !== 'kpi'" class="fld inline">
              <label>数据标签</label>
              <el-switch v-model="cfg.style.label" size="small" />
            </div>

            <div v-if="isLineFamily" class="fld inline">
              <label>平滑曲线</label>
              <el-switch v-model="cfg.style.smooth" size="small" />
            </div>

            <div v-if="cfg.type !== 'kpi'" class="fld">
              <label>配色方案</label>
              <el-select v-model="cfg.style.palette" size="small" style="width: 100%">
                <el-option v-for="(v, k) in PALETTES" :key="k" :label="v.label" :value="k" />
              </el-select>
            </div>

            <div v-if="isCartesian" class="fld inline">
              <label>轴名</label>
              <el-input v-model="cfg.style.xName" size="small" placeholder="X" style="width: 44%" />
              <el-input v-model="cfg.style.yName" size="small" placeholder="Y" style="width: 44%; margin-left: auto" />
            </div>

            <div v-if="isCartesian" class="fld inline">
              <label>X 标签旋转</label>
              <el-input-number v-model="cfg.style.rotate" :min="0" :max="90" :step="15" size="small" controls-position="right" style="width: 110px; margin-left: auto" />
            </div>

            <div v-if="isCartesian" class="fld inline">
              <label>Y 轴范围</label>
              <el-input v-model="cfg.style.yMin" size="small" placeholder="min" style="width: 44%" />
              <el-input v-model="cfg.style.yMax" size="small" placeholder="max" style="width: 44%; margin-left: auto" />
            </div>

            <div v-if="isPieFamily" class="fld inline">
              <label>环形内径 %</label>
              <el-slider v-model="cfg.style.donutInner" :min="0" :max="80" size="small" style="width: 130px; margin-left: auto" />
            </div>
          </template>

          <el-divider content-position="left">数值格式</el-divider>
          <div class="fld inline">
            <label>小数位</label>
            <el-input-number v-model="cfg.style.decimals" :min="0" :max="6" size="small" controls-position="right" style="width: 110px; margin-left: auto" />
          </div>
          <div class="fld inline">
            <label>千分位</label>
            <el-switch v-model="cfg.style.thousands" size="small" />
          </div>
          <div class="fld inline">
            <label>百分比(×100)</label>
            <el-switch v-model="cfg.style.percent" size="small" />
          </div>
          <div class="fld inline">
            <label>单位后缀</label>
            <el-input v-model="cfg.style.unit" size="small" placeholder="如 元 / 万" style="width: 110px; margin-left: auto" />
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 右侧渲染区:图表 / 指标卡 / 明细表 -->
    <div class="eb-main">
      <!-- ECharts 画布(始终在 DOM,用 v-show 控制,便于实例复用) -->
      <div v-show="isCanvasType" ref="chartEl" class="eb-chart" :style="{ height: height + 'px' }"></div>

      <!-- 指标卡 -->
      <div v-if="cfg.type === 'kpi'" class="eb-kpi" :style="{ height: height + 'px' }">
        <div v-if="!kpiItems.length" class="eb-empty">选择度量后显示指标</div>
        <div v-for="(k, i) in kpiItems" :key="i" class="kpi-card">
          <div class="kpi-val">{{ k.value }}</div>
          <div class="kpi-label">{{ k.label }}</div>
        </div>
      </div>

      <!-- 明细表 -->
      <el-table v-else-if="cfg.type === 'table'" :data="tableRows" :height="height" border stripe size="small"
        :style="{ width: '100%' }">
        <el-table-column type="index" label="#" width="50" />
        <el-table-column v-for="c in fields" :key="c" :prop="c" :label="c" min-width="120" show-overflow-tooltip />
        <template #empty>暂无数据</template>
      </el-table>
    </div>
  </div>
</template>

<script setup name="EchartsBuilder">
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  config: { type: Object, default: null }, // 丰富后的 chart_spec
  showControls: { type: Boolean, default: true },
  height: { type: Number, default: 460 },
  aiEnabled: { type: Boolean, default: false }, // 显示「AI 生成图表」输入
  aiLoading: { type: Boolean, default: false }  // 由宿主控制生成中状态
})
const emit = defineEmits(['update:config', 'ai-generate'])

const aiQuestion = ref('')
function genAi() {
  const q = aiQuestion.value.trim()
  if (!q) return
  emit('ai-generate', q) // 宿主调用后端后,把返回的 cfg 通过 :config 回填,watch 会应用
}

// ---- 常量:类型分组 / 聚合 / 配色 ----
const TYPE_GROUPS = [
  { label: '柱 / 条', items: [
    { v: 'bar', l: '柱状图' }, { v: 'bar_stack', l: '堆叠柱状' },
    { v: 'bar_percent', l: '百分比堆叠' }, { v: 'hbar', l: '横向条形' }
  ] },
  { label: '线 / 面', items: [
    { v: 'line', l: '折线图' }, { v: 'area', l: '面积图' }, { v: 'line_stack', l: '堆叠面积' }
  ] },
  { label: '饼图', items: [
    { v: 'pie', l: '饼图' }, { v: 'donut', l: '环形图' }, { v: 'rose', l: '玫瑰图' }
  ] },
  { label: '其他', items: [
    { v: 'scatter', l: '散点图' }, { v: 'radar', l: '雷达图' },
    { v: 'funnel', l: '漏斗图' }, { v: 'gauge', l: '仪表盘' }
  ] },
  { label: '纯展示', items: [
    { v: 'kpi', l: '指标卡' }, { v: 'table', l: '明细表' }
  ] }
]
const AGGS = [
  { v: 'sum', l: '求和' }, { v: 'avg', l: '平均' }, { v: 'count', l: '计数' },
  { v: 'max', l: '最大' }, { v: 'min', l: '最小' }, { v: 'none', l: '不聚合(已聚合直接画)' }
]
const AGG_LABEL = { sum: '总', avg: '均', count: '数', max: '最大', min: '最小' }
const PALETTES = {
  default: { label: '默认', colors: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'] },
  tech: { label: '科技蓝', colors: ['#1f6feb', '#2ea6ff', '#00c2ff', '#0ad4c8', '#5b8ff9', '#5ad8a6', '#3b5bdb', '#748ffc'] },
  warm: { label: '暖色', colors: ['#ff6b6b', '#ff922b', '#fab005', '#f76707', '#e8590c', '#ffa94d', '#f03e3e', '#d9480f'] },
  business: { label: '商务灰', colors: ['#4c6ef5', '#495057', '#868e96', '#adb5bd', '#7048e8', '#1098ad', '#5c7cfa', '#343a40'] },
  vivid: { label: '多彩', colors: ['#7048e8', '#f03e3e', '#12b886', '#fab005', '#1c7ed6', '#e64980', '#40c057', '#fd7e14'] }
}

const DEFAULT_STYLE = {
  title: '', legend: true, legendPos: 'top', label: false, smooth: false, palette: 'default',
  decimals: 2, thousands: true, unit: '', percent: false,
  xName: '', yName: '', rotate: 0, yMin: null, yMax: null, donutInner: 50
}
function newCfg() {
  return { type: 'bar', x: '', ys: [{ field: '', agg: 'sum' }], series: '', sort: { by: '', dir: 'desc' }, topN: 0, style: { ...DEFAULT_STYLE } }
}

const panelTab = ref('data')
const cfg = reactive(newCfg())
const fields = ref([])
const chartEl = ref()
let chart = null
let ro = null
let lastCfgJson = ''

// ---- 计算属性 ----
const isCanvasType = computed(() => !['kpi', 'table'].includes(cfg.type))
const isCartesian = computed(() => ['bar', 'bar_stack', 'bar_percent', 'hbar', 'line', 'area', 'line_stack'].includes(cfg.type))
const isLineFamily = computed(() => ['line', 'area', 'line_stack'].includes(cfg.type))
const isPieFamily = computed(() => ['pie', 'donut', 'rose'].includes(cfg.type))
const allowSeries = computed(() => isCartesian.value) // 分组仅对直角坐标类有意义
const tableRows = computed(() => (props.rows || []).slice(0, 1000))
const kpiItems = computed(() => cfg.ys.filter((m) => m.field).map((m) => ({
  label: `${AGG_LABEL[m.agg] || ''} ${m.field}`,
  value: fmtNumber(agg((props.rows || []).map((r) => r[m.field]), m.agg))
})))

// ---- 迁移 & 字段推断 ----
function migrate(c) {
  const out = newCfg()
  if (!c || typeof c !== 'object' || Array.isArray(c)) return out
  out.type = c.type || 'bar'
  out.x = c.x || ''
  out.series = c.series || ''
  if (Array.isArray(c.ys) && c.ys.length) {
    out.ys = c.ys.map((m) => ({ field: m.field || '', agg: m.agg || 'sum' }))
  } else if (c.y) { // 旧结构 {y, agg}
    out.ys = [{ field: c.y, agg: c.agg || 'sum' }]
  }
  if (c.sort && typeof c.sort === 'object') out.sort = { by: c.sort.by || '', dir: c.sort.dir || 'desc' }
  out.topN = c.topN || 0
  out.style = { ...DEFAULT_STYLE, ...(c.style || {}) }
  return out
}
function applyCfg(c) {
  const m = migrate(c)
  cfg.type = m.type; cfg.x = m.x; cfg.ys = m.ys; cfg.series = m.series
  cfg.sort = m.sort; cfg.topN = m.topN; cfg.style = m.style
}
function inferFields() {
  const r = props.rows[0] || {}
  fields.value = Object.keys(r)
  const nums = fields.value.filter((k) => typeof r[k] === 'number')
  if (!cfg.x || !fields.value.includes(cfg.x)) {
    cfg.x = fields.value.find((k) => typeof r[k] !== 'number') || fields.value[0] || ''
  }
  if (!cfg.ys.length) cfg.ys = [{ field: '', agg: 'sum' }]
  cfg.ys.forEach((m) => { if (!m.field || !fields.value.includes(m.field)) m.field = nums[0] || fields.value[1] || fields.value[0] || '' })
}

function addY() {
  const r = props.rows[0] || {}
  const nums = fields.value.filter((k) => typeof r[k] === 'number')
  cfg.ys.push({ field: nums[0] || fields.value[0] || '', agg: 'sum' })
}
function removeY(i) { if (cfg.ys.length > 1) cfg.ys.splice(i, 1) }

// ---- 聚合 & 格式化 ----
function agg(vals, mode) {
  if (mode === 'none') return vals.length ? vals[0] : 0 // 数据已聚合:每类别一行,直接取该值不再二次聚合
  if (mode === 'count') return vals.length
  const nums = vals.map(Number).filter((v) => !Number.isNaN(v))
  if (!nums.length) return 0
  if (mode === 'avg') return nums.reduce((a, b) => a + b, 0) / nums.length
  if (mode === 'max') return Math.max(...nums)
  if (mode === 'min') return Math.min(...nums)
  return nums.reduce((a, b) => a + b, 0)
}
function fmtNumber(v) {
  if (v === null || v === undefined || v === '') return v
  let n = Number(v)
  if (Number.isNaN(n)) return v
  const s = cfg.style
  if (s.percent) n *= 100
  let str = n.toFixed(s.decimals ?? 2)
  if (s.thousands) {
    const [ip, dp] = str.split('.')
    str = ip.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (dp ? '.' + dp : '')
  }
  if (s.percent) str += '%'
  if (s.unit) str += s.unit
  return str
}
function numOrNull(v) {
  if (v === null || v === undefined || v === '') return null
  const n = Number(v)
  return Number.isNaN(n) ? null : n
}

// 按 sort + topN 对类别裁剪排序,同步重排各系列 data
function applySortTopN(cats, seriesList) {
  const { by, dir } = cfg.sort
  let idx = cats.map((_, i) => i)
  if (by) {
    const keyOf = (i) => {
      if (by === '__x__') return cats[i]
      const s = seriesList.find((x) => x.name === by)
      if (s) return Number(s.data[i]) || 0
      return seriesList.reduce((a, x) => a + (Number(x.data[i]) || 0), 0)
    }
    idx.sort((a, b) => {
      const ka = keyOf(a); const kb = keyOf(b)
      const c = typeof ka === 'number' && typeof kb === 'number' ? ka - kb : String(ka).localeCompare(String(kb))
      return dir === 'asc' ? c : -c
    })
  }
  if (cfg.topN > 0) idx = idx.slice(0, cfg.topN)
  return {
    cats: idx.map((i) => cats[i]),
    seriesList: seriesList.map((s) => ({ ...s, data: idx.map((i) => s.data[i]) }))
  }
}

// 直角坐标类:算出 { cats, seriesList }
function cartesianData() {
  const rows = props.rows
  const cats = [...new Set(rows.map((r) => r[cfg.x]))]
  let seriesList
  if (cfg.series) {
    const y = cfg.ys[0]
    const groups = [...new Set(rows.map((r) => r[cfg.series]))]
    seriesList = groups.map((g) => ({
      name: String(g),
      data: cats.map((c) => agg(rows.filter((r) => r[cfg.x] === c && r[cfg.series] === g).map((r) => r[y.field]), y.agg))
    }))
  } else {
    seriesList = cfg.ys.map((y) => ({
      name: y.field,
      data: cats.map((c) => agg(rows.filter((r) => r[cfg.x] === c).map((r) => r[y.field]), y.agg))
    }))
  }
  return applySortTopN(cats, seriesList)
}

function legendCfg() {
  if (!cfg.style.legend) return { show: false }
  const p = cfg.style.legendPos
  const base = { show: true, type: 'scroll' }
  if (p === 'bottom') return { ...base, bottom: 0 }
  if (p === 'left') return { ...base, left: 0, top: 'middle', orient: 'vertical' }
  if (p === 'right') return { ...base, right: 0, top: 'middle', orient: 'vertical' }
  return { ...base, top: cfg.style.title ? 26 : 4 }
}
function titleCfg() {
  return cfg.style.title ? { text: cfg.style.title, left: 'center', top: 4, textStyle: { fontSize: 14 } } : undefined
}
function paletteColors() { return (PALETTES[cfg.style.palette] || PALETTES.default).colors }

function buildOption() {
  const rows = props.rows || []
  if (!rows.length) {
    return { title: { text: '选择字段后出图', left: 'center', top: 'center', textStyle: { color: '#909399', fontSize: 14 } } }
  }
  const T = cfg.type
  const color = paletteColors()
  const s = cfg.style

  // ---- 饼 / 环形 / 玫瑰 ----
  if (isPieFamily.value) {
    const y = cfg.ys[0]
    let cats = [...new Set(rows.map((r) => r[cfg.x]))]
    let data = cats.map((c) => ({ name: String(c), value: agg(rows.filter((r) => r[cfg.x] === c).map((r) => r[y.field]), y.agg) }))
    if (cfg.sort.by) data.sort((a, b) => (cfg.sort.dir === 'asc' ? a.value - b.value : b.value - a.value))
    if (cfg.topN > 0) data = data.slice(0, cfg.topN)
    const radius = T === 'donut' ? [`${s.donutInner}%`, '70%'] : (T === 'rose' ? ['12%', '72%'] : '65%')
    return {
      color, title: titleCfg(), tooltip: { trigger: 'item', valueFormatter: (v) => fmtNumber(v) }, legend: legendCfg(),
      series: [{ type: 'pie', radius, roseType: T === 'rose' ? 'radius' : undefined, data,
        label: { show: s.label, formatter: (p) => `${p.name}: ${fmtNumber(p.value)}` } }]
    }
  }

  // ---- 散点 ----
  if (T === 'scatter') {
    const y = cfg.ys[0]
    return {
      color, title: titleCfg(), tooltip: { trigger: 'item' },
      grid: { left: 56, right: 24, bottom: 40, top: s.title ? 40 : 24 },
      xAxis: { name: s.xName || cfg.x, type: 'value' }, yAxis: { name: s.yName || y.field, type: 'value', axisLabel: { formatter: (v) => fmtNumber(v) } },
      series: [{ type: 'scatter', data: rows.map((r) => [Number(r[cfg.x]), Number(r[y.field])]) }]
    }
  }

  // ---- 雷达 ----
  if (T === 'radar') {
    let cats = [...new Set(rows.map((r) => r[cfg.x]))]
    if (cfg.topN > 0) cats = cats.slice(0, cfg.topN)
    const seriesVals = cfg.ys.map((y) => ({ name: y.field, value: cats.map((c) => agg(rows.filter((r) => r[cfg.x] === c).map((r) => r[y.field]), y.agg)) }))
    const maxV = Math.max(1, ...seriesVals.flatMap((sv) => sv.value))
    return {
      color, title: titleCfg(), tooltip: {}, legend: legendCfg(),
      radar: { indicator: cats.map((c) => ({ name: String(c), max: maxV })) },
      series: [{ type: 'radar', data: seriesVals, label: { show: s.label, formatter: (p) => fmtNumber(p.value) } }]
    }
  }

  // ---- 漏斗 ----
  if (T === 'funnel') {
    const y = cfg.ys[0]
    let cats = [...new Set(rows.map((r) => r[cfg.x]))]
    let data = cats.map((c) => ({ name: String(c), value: agg(rows.filter((r) => r[cfg.x] === c).map((r) => r[y.field]), y.agg) }))
    data.sort((a, b) => b.value - a.value)
    if (cfg.topN > 0) data = data.slice(0, cfg.topN)
    return {
      color, title: titleCfg(), tooltip: { trigger: 'item', valueFormatter: (v) => fmtNumber(v) }, legend: legendCfg(),
      series: [{ type: 'funnel', data, label: { show: s.label !== false, formatter: (p) => `${p.name}: ${fmtNumber(p.value)}` } }]
    }
  }

  // ---- 仪表盘 ----
  if (T === 'gauge') {
    const y = cfg.ys[0]
    const val = agg(rows.map((r) => r[y.field]), y.agg)
    const max = numOrNull(s.yMax) ?? (Math.ceil(val * 1.2) || 100)
    return {
      color, title: titleCfg(),
      series: [{ type: 'gauge', max, data: [{ value: Number(val.toFixed(s.decimals ?? 2)), name: y.field }],
        detail: { formatter: (v) => fmtNumber(v), fontSize: 18 } }]
    }
  }

  // ---- 直角坐标:柱 / 条 / 线 / 面 ----
  const isBar = ['bar', 'bar_stack', 'bar_percent', 'hbar'].includes(T)
  const stacked = ['bar_stack', 'bar_percent', 'line_stack'].includes(T)
  const percent = T === 'bar_percent'
  const horizontal = T === 'hbar'
  const area = T === 'area' || T === 'line_stack'

  let { cats, seriesList } = cartesianData()

  // 百分比堆叠:每个类别列归一化到 100
  if (percent) {
    const totals = cats.map((_, i) => seriesList.reduce((a, s2) => a + (Number(s2.data[i]) || 0), 0))
    seriesList = seriesList.map((s2) => ({ ...s2, data: s2.data.map((v, i) => (totals[i] ? +(v / totals[i] * 100).toFixed(2) : 0)) }))
  }

  const series = seriesList.map((s2) => ({
    name: s2.name, type: isBar ? 'bar' : 'line',
    stack: stacked ? 'total' : undefined,
    smooth: !isBar ? s.smooth : undefined,
    areaStyle: area ? {} : undefined,
    label: { show: s.label, position: horizontal ? 'right' : 'top', formatter: (p) => (percent ? `${p.value}%` : fmtNumber(p.value)) },
    data: s2.data
  }))

  const catAxis = { type: 'category', data: cats.map(String), name: horizontal ? '' : s.xName,
    axisLabel: { rotate: horizontal ? 0 : s.rotate } }
  const valAxis = { type: 'value', name: horizontal ? s.xName : s.yName,
    min: numOrNull(s.yMin), max: percent ? 100 : numOrNull(s.yMax),
    axisLabel: { formatter: (v) => (percent ? `${v}%` : fmtNumber(v)) } }

  return {
    color, title: titleCfg(), legend: legendCfg(),
    tooltip: { trigger: 'axis', valueFormatter: (v) => (percent ? `${v}%` : fmtNumber(v)) },
    grid: { left: 56, right: 24, bottom: s.rotate ? 60 : 40, top: (s.title || cfg.style.legend) ? 48 : 28, containLabel: true },
    xAxis: horizontal ? valAxis : catAxis,
    yAxis: horizontal ? catAxis : valAxis,
    series
  }
}

// ---- 渲染 & 同步 ----
async function render() {
  if (!isCanvasType.value) return
  await nextTick()
  if (!chart) return
  chart.setOption(buildOption(), true)
  chart.resize()
}
function onResize() { chart && chart.resize() }

// 用户改配置 → 回传 + 重渲;prop 驱动的变更用 lastCfgJson 挡掉,避免回环
watch(cfg, () => {
  const j = JSON.stringify(cfg)
  if (j === lastCfgJson) { render(); return }
  lastCfgJson = j
  emit('update:config', JSON.parse(j))
  render()
}, { deep: true })

watch(() => props.rows, () => { inferFields(); render() })
watch(() => props.config, (c) => { applyCfg(c); lastCfgJson = JSON.stringify(cfg); inferFields(); render() })

onMounted(async () => {
  if (props.config) applyCfg(props.config)
  inferFields()
  lastCfgJson = JSON.stringify(cfg)
  await nextTick()
  chart = echarts.init(chartEl.value)
  render()
  // 容器尺寸变化(如在隐藏 tab 中挂载后再切显、宽度 0→实宽)自动重绘,修「图很窄」
  ro = new ResizeObserver(() => { chart && chart.resize() })
  ro.observe(chartEl.value)
  window.addEventListener('resize', onResize)
  if (props.showControls) emit('update:config', JSON.parse(lastCfgJson)) // 回传默认配置,便于直接保存
})
onBeforeUnmount(() => {
  ro && ro.disconnect()
  window.removeEventListener('resize', onResize)
  chart && chart.dispose()
})

defineExpose({ getConfig: () => JSON.parse(JSON.stringify(cfg)) })
</script>

<style scoped>
.echarts-builder { display: flex; gap: 12px; align-items: flex-start; }
.echarts-builder.no-ctrl { display: block; }
.eb-panel { width: 300px; flex: none; overflow-y: auto; overflow-x: hidden; border-right: 1px solid #ebeef5; padding-right: 10px; }
.eb-tabs :deep(.el-tabs__content) { padding-top: 4px; }
.eb-main { flex: 1; min-width: 0; }
.eb-chart { width: 100%; border: 1px solid #ebeef5; border-radius: 6px; }

.fld { margin-bottom: 12px; }
.fld > label { display: block; font-size: 12px; color: #606266; margin-bottom: 4px; }
.fld.inline { display: flex; align-items: center; gap: 8px; }
.fld.inline > label { display: inline; margin-bottom: 0; }
.row2 { display: flex; gap: 8px; }
.ys-row { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.ai-fld { padding: 8px 10px; margin-bottom: 14px; border: 1px dashed #c0c4cc; border-radius: 6px; background: #fafcff; }

.eb-kpi { display: flex; flex-wrap: wrap; gap: 16px; align-content: flex-start; align-items: stretch;
  border: 1px solid #ebeef5; border-radius: 6px; padding: 20px; overflow: auto; }
.kpi-card { flex: 1 1 180px; min-width: 160px; padding: 22px 18px; border-radius: 10px;
  background: linear-gradient(135deg, #f5f7ff 0%, #eef2ff 100%); border: 1px solid #e4e9ff; text-align: center; }
.kpi-val { font-size: 34px; font-weight: 700; color: #3b5bdb; line-height: 1.2; word-break: break-all; }
.kpi-label { margin-top: 8px; font-size: 13px; color: #606266; }
.eb-empty { margin: auto; color: #909399; font-size: 14px; }
</style>
