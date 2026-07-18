<template>
  <div class="echarts-builder" :class="{ 'no-ctrl': !showControls, dark: dark }">
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
            <div v-if="!isSankey" class="fld">
              <label>{{ xLabel }}</label>
              <el-select v-model="cfg.x" size="small" filterable clearable placeholder="选择字段" style="width: 100%">
                <el-option v-for="f in fields" :key="f" :label="f" :value="f" />
              </el-select>
            </div>

            <!-- K 线:开/高/低/收 四列映射(数据需为每类别一行的 OHLC) -->
            <template v-if="isKline">
              <div v-for="o in OHLC_FIELDS" :key="o.k" class="fld">
                <label>{{ o.l }}</label>
                <el-select v-model="cfg.ohlc[o.k]" size="small" filterable clearable placeholder="选择字段" style="width: 100%">
                  <el-option v-for="f in fields" :key="f" :label="f" :value="f" />
                </el-select>
              </div>
            </template>

            <!-- 桑基图:源 / 目标 / 流量值 三列映射 -->
            <template v-if="isSankey">
              <div v-for="l in LINK_FIELDS" :key="l.k" class="fld">
                <label>{{ l.l }}</label>
                <el-select v-model="cfg.link[l.k]" size="small" filterable clearable placeholder="选择字段" style="width: 100%">
                  <el-option v-for="f in fields" :key="f" :label="f" :value="f" />
                </el-select>
              </div>
            </template>

            <div v-if="!isKline && !isSankey" class="fld">
              <label>{{ isHeatmap ? '值(颜色深浅)' : '度量 / 指标' }}</label>
              <div v-for="(m, i) in cfg.ys" :key="i" class="ys-row">
                <el-select v-model="m.field" size="small" filterable placeholder="字段" style="flex: 1">
                  <el-option v-for="f in fields" :key="f" :label="f" :value="f" />
                </el-select>
                <el-select v-model="m.agg" size="small" style="width: 76px">
                  <el-option v-for="a in AGGS" :key="a.v" :label="a.l" :value="a.v" />
                </el-select>
                <template v-if="isCombo">
                  <el-select v-model="m.mark" size="small" style="width: 62px">
                    <el-option v-for="o in MARKS" :key="o.v" :label="o.l" :value="o.v" />
                  </el-select>
                  <el-select v-model="m.axis" size="small" style="width: 68px">
                    <el-option v-for="o in AXES" :key="o.v" :label="o.l" :value="o.v" />
                  </el-select>
                </template>
                <el-color-picker v-model="m.color" size="small" title="该度量颜色(留空走配色方案)" />
                <el-button size="small" icon="Delete" text :disabled="cfg.ys.length <= 1" @click="removeY(i)" />
              </div>
              <el-button v-if="allowMultiY" size="small" text type="primary" icon="Plus" @click="addY">添加度量</el-button>
            </div>

            <div v-if="allowSeries || isHeatmap" class="fld">
              <label>{{ isHeatmap ? 'Y 轴类别' : '分组 / 拆分(可选)' }}</label>
              <el-select v-model="cfg.series" size="small" filterable clearable :placeholder="isHeatmap ? '选择 Y 轴字段' : '按此字段拆多系列'" style="width: 100%">
                <el-option v-for="f in fields" :key="f" :label="f" :value="f" />
              </el-select>
            </div>

            <div v-if="showSortTopN" class="fld">
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

            <div v-if="showSortTopN" class="fld">
              <label>Top-N(0 = 不限)</label>
              <el-input-number v-model="cfg.topN" :min="0" :max="1000" size="small" controls-position="right" style="width: 100%" />
            </div>

            <div v-if="showSortTopN && cfg.topN > 0" class="fld inline">
              <label>余下归并「其他」</label>
              <el-switch v-model="cfg.style.othersGroup" size="small" />
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

          <div class="fld inline">
            <label>图上导出按钮</label>
            <el-switch v-model="cfg.style.showExport" size="small" />
            <span class="tip" style="margin-left: 8px">导出 PNG / Excel(默认关)</span>
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

            <div v-if="isCartesian || isCombo || cfg.type === 'scatter'" class="fld inline">
              <label>缩放条</label>
              <el-switch v-model="cfg.style.dataZoom" size="small" />
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

            <div v-if="hasAxis" class="fld inline">
              <label>轴名</label>
              <el-input v-model="cfg.style.xName" size="small" placeholder="X" style="width: 44%" />
              <el-input v-model="cfg.style.yName" size="small" placeholder="Y" style="width: 44%; margin-left: auto" />
            </div>

            <div v-if="hasAxis" class="fld inline">
              <label>X 标签旋转</label>
              <el-input-number v-model="cfg.style.rotate" :min="0" :max="90" :step="15" size="small" controls-position="right" style="width: 110px; margin-left: auto" />
            </div>

            <div v-if="hasAxis" class="fld inline">
              <label>Y 轴范围</label>
              <el-input v-model="cfg.style.yMin" size="small" placeholder="min" style="width: 44%" />
              <el-input v-model="cfg.style.yMax" size="small" placeholder="max" style="width: 44%; margin-left: auto" />
            </div>

            <div v-if="isPieFamily" class="fld inline">
              <label>环形内径 %</label>
              <el-slider v-model="cfg.style.donutInner" :min="0" :max="80" size="small" style="width: 130px; margin-left: auto" />
            </div>

            <!-- 参考/目标线(仅直角坐标 / 组合图) -->
            <div v-if="isCartesian || isCombo" class="fld">
              <label>参考线 / 目标线</label>
              <div v-for="(ml, i) in cfg.style.markLines" :key="i" class="ml-row">
                <el-input v-model="ml.value" size="small" placeholder="值" style="width: 92px" />
                <el-input v-model="ml.label" size="small" placeholder="标签(可选)" style="flex: 1" />
                <el-button size="small" icon="Delete" text @click="cfg.style.markLines.splice(i, 1)" />
              </div>
              <el-button size="small" text type="primary" icon="Plus" @click="cfg.style.markLines.push({ value: '', label: '' })">添加参考线</el-button>
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
            <label>数值缩放</label>
            <el-select v-model="cfg.style.scale" size="small" style="width: 110px; margin-left: auto" :disabled="cfg.style.percent">
              <el-option label="原值" value="" />
              <el-option label="万" value="wan" />
              <el-option label="亿" value="yi" />
            </el-select>
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
      <!-- 导出工具条(悬浮右上,默认关;PNG 仅画布类,数据任意有行时可导) -->
      <div v-if="cfg.style.showExport && (rows || []).length" class="eb-tools">
        <el-button v-if="isCanvasType" size="small" text bg icon="Picture" @click="exportPng">PNG</el-button>
        <el-button size="small" text bg icon="Download" @click="exportData">数据</el-button>
      </div>
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
import * as XLSX from 'xlsx'
import { CFG_VERSION } from './board.js'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  config: { type: Object, default: null }, // 丰富后的 chart_spec
  showControls: { type: Boolean, default: true },
  height: { type: Number, default: 460 },
  aiEnabled: { type: Boolean, default: false }, // 显示「AI 生成图表」输入
  aiLoading: { type: Boolean, default: false }, // 由宿主控制生成中状态
  dark: { type: Boolean, default: false }       // 大屏暗底:透明背景 + 明色轴/文字/网格
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
  { label: 'K 线', items: [
    { v: 'kline', l: 'K 线图(OHLC)' }
  ] },
  { label: '组合 / 进阶', items: [
    { v: 'combo', l: '双轴组合' }, { v: 'waterfall', l: '瀑布图' }, { v: 'heatmap', l: '热力图' },
    { v: 'boxplot', l: '箱线图' }, { v: 'treemap', l: '矩形树图' }, { v: 'sankey', l: '桑基图' }
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
// K 线的四个度量列(顺序=面板展示顺序);guess=按列名关键词自动匹配
const OHLC_FIELDS = [
  { k: 'o', l: '开盘价', guess: ['open', '开盘', '开'] },
  { k: 'h', l: '最高价', guess: ['high', '最高', '高'] },
  { k: 'l', l: '最低价', guess: ['low', '最低', '低'] },
  { k: 'c', l: '收盘价', guess: ['close', '收盘', '收'] }
]
const PALETTES = {
  default: { label: '默认', colors: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc'] },
  tech: { label: '科技蓝', colors: ['#1f6feb', '#2ea6ff', '#00c2ff', '#0ad4c8', '#5b8ff9', '#5ad8a6', '#3b5bdb', '#748ffc'] },
  warm: { label: '暖色', colors: ['#ff6b6b', '#ff922b', '#fab005', '#f76707', '#e8590c', '#ffa94d', '#f03e3e', '#d9480f'] },
  business: { label: '商务灰', colors: ['#4c6ef5', '#495057', '#868e96', '#adb5bd', '#7048e8', '#1098ad', '#5c7cfa', '#343a40'] },
  vivid: { label: '多彩', colors: ['#7048e8', '#f03e3e', '#12b886', '#fab005', '#1c7ed6', '#e64980', '#40c057', '#fd7e14'] }
}

const DEFAULT_STYLE = {
  title: '', legend: true, legendPos: 'top', label: false, smooth: false, palette: 'default',
  decimals: 2, thousands: true, unit: '', percent: false, scale: '', // scale: ''|'wan'(万)|'yi'(亿) 数值缩放
  xName: '', yName: '', rotate: 0, yMin: null, yMax: null, donutInner: 50,
  othersGroup: false, dataZoom: false, showExport: false // othersGroup:Top-N 归并"其他";dataZoom:缩放条;showExport:图上导出按钮(默认关)
}
// 双轴组合每个度量可选:mark(bar/line)、axis(left/right)
const MARKS = [{ v: '', l: '默认' }, { v: 'bar', l: '柱' }, { v: 'line', l: '线' }]
const AXES = [{ v: '', l: '左轴' }, { v: 'right', l: '右轴' }]
// 桑基图三列映射(源→目标,值=流量)
const LINK_FIELDS = [
  { k: 'source', l: '源节点', guess: ['source', 'from', '源', '起'] },
  { k: 'target', l: '目标节点', guess: ['target', 'to', '目标', '止', '终'] },
  { k: 'value', l: '流量值', guess: ['value', 'amount', 'weight', 'count', '值', '量'] }
]
function newCfg() {
  return { version: CFG_VERSION, type: 'bar', x: '', ys: [{ field: '', agg: 'sum', mark: '', axis: '', color: '' }], series: '', sort: { by: '', dir: 'desc' }, topN: 0,
    ohlc: { o: '', h: '', l: '', c: '' }, link: { source: '', target: '', value: '' }, style: { ...DEFAULT_STYLE, markLines: [] } }
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
const isKline = computed(() => cfg.type === 'kline')
const isCombo = computed(() => cfg.type === 'combo')
const isHeatmap = computed(() => cfg.type === 'heatmap')
const isSankey = computed(() => cfg.type === 'sankey')
// 有直角轴(共用轴名/旋转/范围样式):直角坐标 + K线/组合/瀑布/箱线/热力
const hasAxis = computed(() => isCartesian.value || ['kline', 'combo', 'waterfall', 'boxplot', 'heatmap'].includes(cfg.type))
const allowSeries = computed(() => isCartesian.value || isCombo.value) // 分组:直角坐标 + 组合图(热力单独用 series 当 Y 轴)
const showSortTopN = computed(() => !['kpi', 'gauge', 'kline', 'sankey', 'heatmap', 'boxplot'].includes(cfg.type))
const allowMultiY = computed(() => isCartesian.value || isCombo.value || cfg.type === 'radar') // 支持多度量的类型
const xLabel = computed(() => cfg.type === 'kpi' ? '标签维度(可选)'
  : isKline.value ? '时间 / 类别(X 轴)' : isHeatmap.value ? 'X 轴类别' : '类别 / 维度')
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
    out.ys = c.ys.map((m) => ({ field: m.field || '', agg: m.agg || 'sum', mark: m.mark || '', axis: m.axis || '', color: m.color || '' }))
  } else if (c.y) { // 旧结构 {y, agg}
    out.ys = [{ field: c.y, agg: c.agg || 'sum', mark: '', axis: '', color: '' }]
  }
  if (c.sort && typeof c.sort === 'object') out.sort = { by: c.sort.by || '', dir: c.sort.dir || 'desc' }
  out.topN = c.topN || 0
  if (c.ohlc && typeof c.ohlc === 'object') out.ohlc = { o: c.ohlc.o || '', h: c.ohlc.h || '', l: c.ohlc.l || '', c: c.ohlc.c || '' }
  if (c.link && typeof c.link === 'object') out.link = { source: c.link.source || '', target: c.link.target || '', value: c.link.value || '' }
  out.style = { ...DEFAULT_STYLE, ...(c.style || {}) }
  // markLines 用全新数组(避免 DEFAULT_STYLE 引用被共享/污染)
  out.style.markLines = Array.isArray(c.style && c.style.markLines)
    ? c.style.markLines.map((m) => ({ value: m.value, label: m.label || '' }))
    : []
  return out
}
function applyCfg(c) {
  const m = migrate(c)
  cfg.type = m.type; cfg.x = m.x; cfg.ys = m.ys; cfg.series = m.series
  cfg.sort = m.sort; cfg.topN = m.topN; cfg.ohlc = m.ohlc; cfg.link = m.link; cfg.style = m.style
}
// K 线:为空的 OHLC 列按列名关键词猜,猜不到则顺次取未用的数值列;x 未设时另取一列(通常日期)
function ensureOhlc() {
  const r = props.rows[0] || {}
  const nums = fields.value.filter((k) => typeof r[k] === 'number')
  const used = new Set([cfg.x])
  for (const o of OHLC_FIELDS) {
    let f = cfg.ohlc[o.k]
    if (f && fields.value.includes(f)) { used.add(f); continue }
    f = fields.value.find((k) => !used.has(k) && o.guess.some((g) => k.toLowerCase().includes(g)))
    if (!f) f = nums.find((k) => !used.has(k)) || ''
    cfg.ohlc[o.k] = f
    if (f) used.add(f)
  }
}
// 桑基:源/目标猜文本列、值猜数值列;猜不到顺次取列
function ensureLink() {
  const cols = fields.value
  const r = props.rows[0] || {}
  const nonNum = cols.filter((k) => typeof r[k] !== 'number')
  const nums = cols.filter((k) => typeof r[k] === 'number')
  const L = cfg.link
  const pick = (cur, guess, pool, used) => {
    if (cur && cols.includes(cur)) return cur
    return pool.find((k) => !used.has(k) && guess.some((g) => k.toLowerCase().includes(g))) || pool.find((k) => !used.has(k)) || ''
  }
  const used = new Set()
  L.source = pick(L.source, LINK_FIELDS[0].guess, nonNum.length ? nonNum : cols, used); used.add(L.source)
  L.target = pick(L.target, LINK_FIELDS[1].guess, nonNum.length ? nonNum : cols, used); used.add(L.target)
  L.value = pick(L.value, LINK_FIELDS[2].guess, nums.length ? nums : cols, used)
}
function inferFields() {
  const r = props.rows[0] || {}
  fields.value = Object.keys(r)
  const nums = fields.value.filter((k) => typeof r[k] === 'number')
  if (!cfg.x || !fields.value.includes(cfg.x)) {
    cfg.x = fields.value.find((k) => typeof r[k] !== 'number') || fields.value[0] || ''
  }
  if (!cfg.ys.length) cfg.ys = [{ field: '', agg: 'sum', mark: '', axis: '' }]
  cfg.ys.forEach((m) => { if (!m.field || !fields.value.includes(m.field)) m.field = nums[0] || fields.value[1] || fields.value[0] || '' })
  if (cfg.type === 'kline') ensureOhlc()
  if (cfg.type === 'sankey') ensureLink()
  // 热力:series 当 Y 轴类别,必须有;缺则另取一列(非 x、优先文本)
  if (cfg.type === 'heatmap' && (!cfg.series || !fields.value.includes(cfg.series))) {
    cfg.series = fields.value.find((k) => k !== cfg.x && typeof r[k] !== 'number') || fields.value.find((k) => k !== cfg.x) || ''
  }
}

function addY() {
  const r = props.rows[0] || {}
  const nums = fields.value.filter((k) => typeof r[k] === 'number')
  cfg.ys.push({ field: nums[0] || fields.value[0] || '', agg: 'sum', mark: '', axis: '', color: '' })
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
  else if (s.scale === 'wan') n /= 1e4
  else if (s.scale === 'yi') n /= 1e8
  let str = n.toFixed(s.decimals ?? 2)
  if (s.thousands) {
    const [ip, dp] = str.split('.')
    str = ip.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (dp ? '.' + dp : '')
  }
  if (s.percent) str += '%'
  else if (s.scale === 'wan') str += '万'
  else if (s.scale === 'yi') str += '亿'
  if (s.unit) str += s.unit
  return str
}
function numOrNull(v) {
  if (v === null || v === undefined || v === '') return null
  const n = Number(v)
  return Number.isNaN(n) ? null : n
}
// 分位数(线性插值)+ 箱线五数概括 [min,Q1,中位,Q3,max]
function quantile(sorted, p) {
  if (!sorted.length) return 0
  const idx = (sorted.length - 1) * p
  const lo = Math.floor(idx); const hi = Math.ceil(idx)
  return lo === hi ? sorted[lo] : sorted[lo] + (sorted[hi] - sorted[lo]) * (idx - lo)
}
function boxOf(sorted) {
  return [sorted[0] || 0, quantile(sorted, 0.25), quantile(sorted, 0.5), quantile(sorted, 0.75), sorted[sorted.length - 1] || 0]
}
// 按 x 分组取某度量(none=取该组首值,其余按 agg 汇总)——组合/瀑布/热力/箱线/树图共用
function catAgg(rows, cat, field, mode) {
  return agg(rows.filter((r) => String(r[cfg.x]) === String(cat)).map((r) => r[field]), mode)
}
// 对 name/value 列表应用 Top-N(topN>0);othersGroup 时把余下项汇总成「其他」
function topNData(data) {
  if (!(cfg.topN > 0) || data.length <= cfg.topN) return data
  const head = data.slice(0, cfg.topN)
  if (!cfg.style.othersGroup) return head
  const rest = data.slice(cfg.topN).reduce((a, d) => a + (Number(d.value) || 0), 0)
  return [...head, { name: '其他', value: rest }]
}
// 参考/目标线 → 某系列的 markLine;axisKey='yAxis'(纵值轴)或 'xAxis'(横值轴,如 hbar)
function markLineOpt(axisKey) {
  const ml = (cfg.style.markLines || []).filter((m) => numOrNull(m.value) !== null)
  if (!ml.length) return undefined
  return {
    silent: true, symbol: 'none',
    data: ml.map((m) => ({ [axisKey]: Number(m.value), label: { formatter: m.label || fmtNumber(m.value) } }))
  }
}
// 缩放条(dataZoom):开启后给直角坐标/组合/散点加 inside+slider
function zoomOpt() {
  return cfg.style.dataZoom ? [{ type: 'inside' }, { type: 'slider', height: 16, bottom: 4 }] : undefined
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

  // ---- K 线(candlestick):x=时间/类别,每行一组 OHLC ----
  if (T === 'kline') {
    const o = cfg.ohlc || {}
    const cats = rows.map((r) => String(r[cfg.x]))
    // ECharts candlestick 每项顺序为 [开, 收, 低, 高]
    const data = rows.map((r) => [numOrNull(r[o.o]), numOrNull(r[o.c]), numOrNull(r[o.l]), numOrNull(r[o.h])])
    return {
      title: titleCfg(),
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      grid: { left: 56, right: 24, bottom: 54, top: s.title ? 40 : 24, containLabel: true },
      xAxis: { type: 'category', data: cats, name: s.xName, boundaryGap: true, axisLabel: { rotate: s.rotate } },
      yAxis: { type: 'value', name: s.yName, scale: true, min: numOrNull(s.yMin), max: numOrNull(s.yMax),
        axisLabel: { formatter: (v) => fmtNumber(v) } },
      dataZoom: [{ type: 'inside' }, { type: 'slider', bottom: 6, height: 16 }],
      series: [{ type: 'candlestick', data,
        // 红涨绿跌(A 股习惯);color=阳线 color0=阴线
        itemStyle: { color: '#ef232a', color0: '#14b143', borderColor: '#ef232a', borderColor0: '#14b143' } }]
    }
  }

  // ---- 饼 / 环形 / 玫瑰 ----
  if (isPieFamily.value) {
    const y = cfg.ys[0]
    let cats = [...new Set(rows.map((r) => r[cfg.x]))]
    let data = cats.map((c) => ({ name: String(c), value: agg(rows.filter((r) => r[cfg.x] === c).map((r) => r[y.field]), y.agg) }))
    if (cfg.sort.by) data.sort((a, b) => (cfg.sort.dir === 'asc' ? a.value - b.value : b.value - a.value))
    data = topNData(data)
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
      dataZoom: zoomOpt(),
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
    data = topNData(data)
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

  // ---- 双轴组合:每个度量可选 柱/线 与 左/右轴 ----
  if (T === 'combo') {
    const cats0 = [...new Set(rows.map((r) => r[cfg.x]))]
    let seriesList = cfg.ys.filter((y) => y.field).map((y) => ({
      name: y.field, data: cats0.map((c) => catAgg(rows, c, y.field, y.agg))
    }))
    const sorted = applySortTopN(cats0, seriesList)
    const cats = sorted.cats; seriesList = sorted.seriesList
    const measures = cfg.ys.filter((y) => y.field)
    const hasRight = measures.some((y) => y.axis === 'right')
    const series = seriesList.map((s2, i) => {
      const y = measures[i] || {}
      const mark = y.mark === 'line' ? 'line' : (y.mark === 'bar' ? 'bar' : (i === 0 ? 'bar' : 'line'))
      return {
        name: s2.name, type: mark, yAxisIndex: y.axis === 'right' ? 1 : 0,
        smooth: mark === 'line' ? s.smooth : undefined,
        itemStyle: y.color ? { color: y.color } : undefined,
        lineStyle: (mark === 'line' && y.color) ? { color: y.color } : undefined,
        label: { show: s.label, position: 'top', formatter: (p) => fmtNumber(p.value) },
        markLine: i === 0 ? markLineOpt('yAxis') : undefined,
        data: s2.data
      }
    })
    const yL = { type: 'value', name: s.yName, min: numOrNull(s.yMin), max: numOrNull(s.yMax), axisLabel: { formatter: (v) => fmtNumber(v) } }
    const yR = { type: 'value', axisLabel: { formatter: (v) => fmtNumber(v) } }
    return {
      color, title: titleCfg(), legend: legendCfg(), tooltip: { trigger: 'axis', valueFormatter: (v) => fmtNumber(v) },
      grid: { left: 56, right: hasRight ? 56 : 24, bottom: s.rotate ? 60 : 40, top: (s.title || cfg.style.legend) ? 48 : 28, containLabel: true },
      dataZoom: zoomOpt(),
      xAxis: { type: 'category', data: cats.map(String), name: s.xName, axisLabel: { rotate: s.rotate } },
      yAxis: hasRight ? [yL, yR] : [yL], series
    }
  }

  // ---- 瀑布图:x 一个度量,累计升降(透明底座 + 增/减两段)----
  if (T === 'waterfall') {
    const y = cfg.ys[0]
    let items = [...new Set(rows.map((r) => r[cfg.x]))].map((c) => ({ c: String(c), v: Number(catAgg(rows, c, y.field, y.agg)) || 0 }))
    if (cfg.sort.by) items.sort((a, b) => (cfg.sort.dir === 'asc' ? a.v - b.v : b.v - a.v))
    if (cfg.topN > 0) items = items.slice(0, cfg.topN)
    const base = []; const rise = []; const fall = []; let run = 0
    for (const it of items) {
      const start = run; run += it.v
      base.push(Math.min(start, run))
      const h = Math.abs(it.v)
      rise.push(it.v >= 0 ? h : '-'); fall.push(it.v < 0 ? h : '-')
    }
    return {
      title: titleCfg(), legend: legendCfg(), tooltip: { trigger: 'axis', valueFormatter: (v) => fmtNumber(v) },
      grid: { left: 56, right: 24, bottom: s.rotate ? 60 : 40, top: (s.title || cfg.style.legend) ? 48 : 28, containLabel: true },
      xAxis: { type: 'category', data: items.map((it) => it.c), name: s.xName, axisLabel: { rotate: s.rotate } },
      yAxis: { type: 'value', name: s.yName, axisLabel: { formatter: (v) => fmtNumber(v) } },
      series: [
        { type: 'bar', stack: 'wf', itemStyle: { color: 'transparent' }, emphasis: { itemStyle: { color: 'transparent' } }, data: base, silent: true },
        { name: '增加', type: 'bar', stack: 'wf', itemStyle: { color: '#ef232a' }, data: rise, label: { show: s.label, position: 'top', formatter: (p) => fmtNumber(p.value) } },
        { name: '减少', type: 'bar', stack: 'wf', itemStyle: { color: '#14b143' }, data: fall, label: { show: s.label, position: 'bottom', formatter: (p) => fmtNumber(p.value) } }
      ]
    }
  }

  // ---- 热力图:x=X轴类别,series=Y轴类别,ys[0]=值(颜色深浅)----
  if (T === 'heatmap') {
    const y = cfg.ys[0]
    const xcats = [...new Set(rows.map((r) => String(r[cfg.x])))]
    const ycats = [...new Set(rows.map((r) => String(r[cfg.series])))]
    const data = []; let minV = Infinity; let maxV = -Infinity
    for (let xi = 0; xi < xcats.length; xi++) {
      for (let yi = 0; yi < ycats.length; yi++) {
        const sub = rows.filter((r) => String(r[cfg.x]) === xcats[xi] && String(r[cfg.series]) === ycats[yi])
        if (!sub.length) continue
        const v = agg(sub.map((r) => r[y.field]), y.agg)
        data.push([xi, yi, v]); if (v < minV) minV = v; if (v > maxV) maxV = v
      }
    }
    return {
      title: titleCfg(), tooltip: { position: 'top', formatter: (p) => `${xcats[p.value[0]]} / ${ycats[p.value[1]]}: ${fmtNumber(p.value[2])}` },
      grid: { left: 80, right: 24, bottom: 60, top: s.title ? 40 : 24, containLabel: true },
      xAxis: { type: 'category', data: xcats, name: s.xName, axisLabel: { rotate: s.rotate } },
      yAxis: { type: 'category', data: ycats, name: s.yName },
      visualMap: { min: isFinite(minV) ? minV : 0, max: isFinite(maxV) ? maxV : 1, calculable: true, orient: 'horizontal', left: 'center', bottom: 4, inRange: { color: ['#e0f3f8', '#4575b4'] } },
      series: [{ type: 'heatmap', data, label: { show: s.label, formatter: (p) => fmtNumber(p.value[2]) } }]
    }
  }

  // ---- 箱线图:x=类别,ys[0]=原始值列,按类别算五数概括 ----
  if (T === 'boxplot') {
    const y = cfg.ys[0]
    const cats = [...new Set(rows.map((r) => String(r[cfg.x])))]
    const boxData = cats.map((c) => boxOf(
      rows.filter((r) => String(r[cfg.x]) === c).map((r) => Number(r[y.field])).filter((v) => !Number.isNaN(v)).sort((a, b) => a - b)
    ))
    return {
      color, title: titleCfg(), tooltip: { trigger: 'item' },
      grid: { left: 56, right: 24, bottom: s.rotate ? 60 : 40, top: s.title ? 40 : 24, containLabel: true },
      xAxis: { type: 'category', data: cats, name: s.xName, axisLabel: { rotate: s.rotate } },
      yAxis: { type: 'value', name: s.yName, scale: true, axisLabel: { formatter: (v) => fmtNumber(v) } },
      series: [{ type: 'boxplot', data: boxData }]
    }
  }

  // ---- 矩形树图:name=x,value=ys[0](单层)----
  if (T === 'treemap') {
    const y = cfg.ys[0]
    let data = [...new Set(rows.map((r) => r[cfg.x]))].map((c) => ({ name: String(c), value: catAgg(rows, c, y.field, y.agg) }))
    if (cfg.sort.by) data.sort((a, b) => (cfg.sort.dir === 'asc' ? a.value - b.value : b.value - a.value))
    data = topNData(data)
    return {
      color, title: titleCfg(), tooltip: { formatter: (p) => `${p.name}: ${fmtNumber(p.value)}` },
      series: [{ type: 'treemap', data, breadcrumb: { show: false }, roam: false,
        label: { show: true, formatter: (p) => `${p.name}\n${fmtNumber(p.value)}` } }]
    }
  }

  // ---- 桑基图:link{source,target,value} 三列 → 节点 + 边 ----
  if (T === 'sankey') {
    const lk = cfg.link || {}
    const nodes = new Set(); const links = []
    for (const r of rows) {
      const src = String(r[lk.source] ?? ''); const tgt = String(r[lk.target] ?? ''); const val = Number(r[lk.value])
      if (!src || !tgt || Number.isNaN(val)) continue
      nodes.add(src); nodes.add(tgt); links.push({ source: src, target: tgt, value: val })
    }
    return {
      color, title: titleCfg(), tooltip: { trigger: 'item', valueFormatter: (v) => fmtNumber(v) },
      series: [{ type: 'sankey', data: [...nodes].map((n) => ({ name: n })), links, emphasis: { focus: 'adjacency' },
        label: { show: s.label !== false }, lineStyle: { color: 'gradient', curveness: 0.5 } }]
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

  const series = seriesList.map((s2, i2) => {
    // 每度量单独配色仅在"未分组"(seriesList 按 ys 展开)时生效;分组时走调色板
    const clr = (!cfg.series && cfg.ys[i2] && cfg.ys[i2].color) ? cfg.ys[i2].color : ''
    return {
      name: s2.name, type: isBar ? 'bar' : 'line',
      stack: stacked ? 'total' : undefined,
      smooth: !isBar ? s.smooth : undefined,
      areaStyle: area ? {} : undefined,
      itemStyle: clr ? { color: clr } : undefined,
      lineStyle: (!isBar && clr) ? { color: clr } : undefined,
      label: { show: s.label, position: horizontal ? 'right' : 'top', formatter: (p) => (percent ? `${p.value}%` : fmtNumber(p.value)) },
      markLine: i2 === 0 ? markLineOpt(horizontal ? 'xAxis' : 'yAxis') : undefined,
      data: s2.data
    }
  })

  const catAxis = { type: 'category', data: cats.map(String), name: horizontal ? '' : s.xName,
    axisLabel: { rotate: horizontal ? 0 : s.rotate } }
  const valAxis = { type: 'value', name: horizontal ? s.xName : s.yName,
    min: numOrNull(s.yMin), max: percent ? 100 : numOrNull(s.yMax),
    axisLabel: { formatter: (v) => (percent ? `${v}%` : fmtNumber(v)) } }

  return {
    color, title: titleCfg(), legend: legendCfg(),
    tooltip: { trigger: 'axis', valueFormatter: (v) => (percent ? `${v}%` : fmtNumber(v)) },
    grid: { left: 56, right: 24, bottom: s.rotate ? 60 : 40, top: (s.title || cfg.style.legend) ? 48 : 28, containLabel: true },
    dataZoom: zoomOpt(),
    xAxis: horizontal ? valAxis : catAxis,
    yAxis: horizontal ? catAxis : valAxis,
    series
  }
}

// ---- 渲染 & 同步 ----
// 大屏暗底:把默认深色文字/轴线改成明色,并让画布透明(透出大屏背景)
function applyDark(opt) {
  if (!opt) return opt
  const text = '#c9d4e3', line = 'rgba(201,212,227,0.35)', split = 'rgba(201,212,227,0.12)'
  opt.backgroundColor = 'transparent'
  opt.textStyle = { color: text, ...(opt.textStyle || {}) }
  if (opt.legend) {
    const ls = Array.isArray(opt.legend) ? opt.legend : [opt.legend]
    ls.forEach((l) => { l.textStyle = { color: text, ...(l.textStyle || {}) } })
  }
  if (opt.title) {
    const ts = Array.isArray(opt.title) ? opt.title : [opt.title]
    ts.forEach((t) => { t.textStyle = { color: text, ...(t.textStyle || {}) } })
  }
  const decorate = (ax) => {
    if (!ax) return ax
    ;(Array.isArray(ax) ? ax : [ax]).forEach((a) => {
      a.axisLine = { ...(a.axisLine || {}), lineStyle: { ...((a.axisLine && a.axisLine.lineStyle) || {}), color: line } }
      a.axisLabel = { ...(a.axisLabel || {}), color: text }
      a.splitLine = { ...(a.splitLine || {}), lineStyle: { ...((a.splitLine && a.splitLine.lineStyle) || {}), color: split } }
      a.nameTextStyle = { ...(a.nameTextStyle || {}), color: text }
    })
    return ax
  }
  opt.xAxis = decorate(opt.xAxis)
  opt.yAxis = decorate(opt.yAxis)
  return opt
}
async function render() {
  if (!isCanvasType.value) return
  await nextTick()
  if (!chart) return
  const opt = buildOption()
  chart.setOption(props.dark ? applyDark(opt) : opt, true)
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

watch(() => cfg.type, () => inferFields()) // 切类型时按新类型补齐所需字段映射(OHLC/桑基 link/热力 Y 等)
watch(() => props.rows, () => { inferFields(); render() })
watch(() => props.dark, () => render()) // 暗底模式切换时重渲
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

// 导出:PNG(仅画布类)/ 数据(当前 rows → xlsx)
function exportPng() {
  if (!chart || !isCanvasType.value) return
  const url = chart.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#fff' })
  const a = document.createElement('a')
  a.href = url
  a.download = `${cfg.style.title || 'chart'}_${Date.now()}.png`
  a.click()
}
function exportData() {
  const rows = props.rows || []
  if (!rows.length) return
  const ws = XLSX.utils.json_to_sheet(rows)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'data')
  XLSX.writeFile(wb, `${cfg.style.title || 'data'}_${Date.now()}.xlsx`)
}

defineExpose({ getConfig: () => JSON.parse(JSON.stringify(cfg)), exportPng, exportData })
</script>

<style scoped>
.echarts-builder { display: flex; gap: 12px; align-items: flex-start; }
.echarts-builder.no-ctrl { display: block; }
.eb-panel { width: 300px; flex: none; overflow-y: auto; overflow-x: hidden; border-right: 1px solid #ebeef5; padding-right: 10px; }
.eb-tabs :deep(.el-tabs__content) { padding-top: 4px; }
.eb-main { flex: 1; min-width: 0; position: relative; }
.eb-tools { position: absolute; top: 4px; right: 8px; z-index: 5; display: flex; gap: 4px; }
.eb-chart { width: 100%; border: 1px solid #ebeef5; border-radius: 6px; }
/* 大屏暗底:去掉浅色边框(否则深色底上会显出突兀的白框),背景透明 */
.echarts-builder.dark .eb-chart { border-color: transparent; background: transparent; }
.echarts-builder.dark .eb-kpi { border-color: transparent; }

.fld { margin-bottom: 12px; }
.fld > label { display: block; font-size: 12px; color: #606266; margin-bottom: 4px; }
.fld.inline { display: flex; align-items: center; gap: 8px; }
.fld.inline > label { display: inline; margin-bottom: 0; }
.row2 { display: flex; gap: 8px; }
.ys-row { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.ml-row { display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }
.eb-panel .tip { font-size: 12px; color: #909399; }
.ai-fld { padding: 8px 10px; margin-bottom: 14px; border: 1px dashed #c0c4cc; border-radius: 6px; background: #fafcff; }

.eb-kpi { display: flex; flex-wrap: wrap; gap: 16px; align-content: flex-start; align-items: stretch;
  border: 1px solid #ebeef5; border-radius: 6px; padding: 20px; overflow: auto; }
.kpi-card { flex: 1 1 180px; min-width: 160px; padding: 22px 18px; border-radius: 10px;
  background: linear-gradient(135deg, #f5f7ff 0%, #eef2ff 100%); border: 1px solid #e4e9ff; text-align: center; }
.kpi-val { font-size: 34px; font-weight: 700; color: #3b5bdb; line-height: 1.2; word-break: break-all; }
.kpi-label { margin-top: 8px; font-size: 13px; color: #606266; }
.eb-empty { margin: auto; color: #909399; font-size: 14px; }
</style>
