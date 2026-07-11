<template>
  <div class="echarts-builder">
    <div v-if="showControls" class="eb-bar">
      <el-select v-model="cfg.type" size="small" style="width: 108px" @change="emitAndRender">
        <el-option v-for="t in TYPES" :key="t.v" :label="t.l" :value="t.v" />
      </el-select>
      <el-select v-model="cfg.x" size="small" filterable clearable placeholder="维度(X/分类)" style="width: 150px" @change="emitAndRender">
        <el-option v-for="f in fields" :key="f" :label="f" :value="f" />
      </el-select>
      <el-select v-model="cfg.y" size="small" filterable clearable placeholder="度量(Y/值)" style="width: 150px" @change="emitAndRender">
        <el-option v-for="f in fields" :key="f" :label="f" :value="f" />
      </el-select>
      <el-select v-model="cfg.agg" size="small" style="width: 96px" @change="emitAndRender">
        <el-option v-for="a in AGGS" :key="a.v" :label="a.l" :value="a.v" />
      </el-select>
      <el-select v-model="cfg.series" size="small" filterable clearable placeholder="分组(可选)" style="width: 128px" @change="emitAndRender">
        <el-option v-for="f in fields" :key="f" :label="f" :value="f" />
      </el-select>
    </div>
    <div ref="chartEl" class="eb-chart" :style="{ height: height + 'px' }"></div>
  </div>
</template>

<script setup name="EchartsBuilder">
import { ref, reactive, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  config: { type: Object, default: null },   // {type,x,y,agg,series}
  showControls: { type: Boolean, default: true },
  height: { type: Number, default: 460 }
})
const emit = defineEmits(['update:config'])

const TYPES = [
  { v: 'bar', l: '柱状图' }, { v: 'line', l: '折线图' }, { v: 'area', l: '面积图' },
  { v: 'pie', l: '饼图' }, { v: 'scatter', l: '散点图' }
]
const AGGS = [
  { v: 'sum', l: '求和' }, { v: 'avg', l: '平均' }, { v: 'count', l: '计数' },
  { v: 'max', l: '最大' }, { v: 'min', l: '最小' }
]
const cfg = reactive({ type: 'bar', x: '', y: '', agg: 'sum', series: '' })
const fields = ref([])
const chartEl = ref()
let chart = null

function inferFields() {
  const r = props.rows[0] || {}
  fields.value = Object.keys(r)
  if (!cfg.x || !fields.value.includes(cfg.x)) {
    cfg.x = fields.value.find((k) => typeof r[k] !== 'number') || fields.value[0] || ''
  }
  if (!cfg.y || !fields.value.includes(cfg.y)) {
    cfg.y = fields.value.find((k) => typeof r[k] === 'number') || fields.value[1] || fields.value[0] || ''
  }
}

function agg(vals, mode) {
  if (mode === 'count') return vals.length
  const nums = vals.map(Number).filter((v) => !Number.isNaN(v))
  if (!nums.length) return 0
  if (mode === 'avg') return +(nums.reduce((a, b) => a + b, 0) / nums.length).toFixed(2)
  if (mode === 'max') return Math.max(...nums)
  if (mode === 'min') return Math.min(...nums)
  return nums.reduce((a, b) => a + b, 0) // sum
}

function buildOption() {
  const rows = props.rows || []
  const { type, x, y, series } = cfg
  if (!rows.length || !x) {
    return { title: { text: '选择字段后出图', left: 'center', top: 'center', textStyle: { color: '#909399', fontSize: 14 } } }
  }
  if (type === 'scatter') {
    return { tooltip: {}, xAxis: { name: x }, yAxis: { name: y }, series: [{ type: 'scatter', data: rows.map((r) => [r[x], Number(r[y])]) }] }
  }
  const xs = [...new Set(rows.map((r) => r[x]))]
  if (series) {
    const svs = [...new Set(rows.map((r) => r[series]))]
    const ss = svs.map((sv) => ({
      name: String(sv),
      type: type === 'area' ? 'line' : type,
      areaStyle: type === 'area' ? {} : undefined,
      data: xs.map((xv) => agg(rows.filter((r) => r[x] === xv && r[series] === sv).map((r) => r[y]), cfg.agg))
    }))
    return { tooltip: { trigger: 'axis' }, legend: { type: 'scroll', data: svs.map(String) }, xAxis: { type: 'category', data: xs.map(String) }, yAxis: { type: 'value' }, series: ss }
  }
  const data = xs.map((xv) => agg(rows.filter((r) => r[x] === xv).map((r) => r[y]), cfg.agg))
  if (type === 'pie') {
    return { tooltip: { trigger: 'item' }, legend: { type: 'scroll', bottom: 0 }, series: [{ type: 'pie', radius: '62%', data: xs.map((xv, i) => ({ name: String(xv), value: data[i] })) }] }
  }
  return { tooltip: { trigger: 'axis' }, grid: { left: 48, right: 24, bottom: 40, top: 24 }, xAxis: { type: 'category', data: xs.map(String) }, yAxis: { type: 'value' }, series: [{ name: y, type: type === 'area' ? 'line' : type, areaStyle: type === 'area' ? {} : undefined, data }] }
}

function render() {
  if (!chart) return
  chart.setOption(buildOption(), true)
  chart.resize()
}
function emitAndRender() {
  emit('update:config', { ...cfg })
  render()
}
function onResize() { chart && chart.resize() }

watch(() => props.rows, () => { inferFields(); render() })
watch(() => props.config, (c) => { if (c && typeof c === 'object') { Object.assign(cfg, c); render() } })

onMounted(async () => {
  if (props.config && typeof props.config === 'object') Object.assign(cfg, props.config)
  inferFields()
  await nextTick()
  chart = echarts.init(chartEl.value)
  render()
  window.addEventListener('resize', onResize)
  if (props.showControls) emit('update:config', { ...cfg }) // 回传默认配置,便于直接保存
})
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); chart && chart.dispose() })

defineExpose({ getConfig: () => ({ ...cfg }) })
</script>

<style scoped>
.echarts-builder { display: flex; flex-direction: column; }
.eb-bar { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
.eb-chart { width: 100%; border: 1px solid #ebeef5; border-radius: 6px; }
</style>
