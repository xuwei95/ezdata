<template>
  <div class="lineage-tab">
    <div class="lin-toolbar">
      <span class="hint">数据血缘:该模型「从哪来 → 到哪去」。源 → 任务 → 模型 → 指标(声明式,来自任务的抽取/写入参数与绑定关系,始终新鲜)。</span>
      <el-button size="small" icon="Refresh" :loading="loading" @click="load">刷新</el-button>
    </div>
    <div v-loading="loading" class="lin-canvas-wrap">
      <div ref="chartEl" class="lin-canvas"></div>
      <el-empty v-if="!loading && empty" description="暂无血缘(该模型无产出任务/绑定)" />
    </div>
    <div class="legend">
      <span><i class="sq" :style="{ background: COLORS.datasource }" /> 数据源</span>
      <span><i class="sq" :style="{ background: COLORS.task }" /> 任务</span>
      <span><i class="sq" :style="{ background: COLORS.model }" /> 数据模型</span>
      <span><i class="sq" :style="{ background: COLORS.metric }" /> 指标</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getLineage } from '@/api/dataManage/data'

const props = defineProps({ model: { type: Object, required: true } })

const chartEl = ref()
const loading = ref(false)
const empty = ref(false)
let chart = null
let ro = null
let canvasH = 360

// 四类节点配色 + 左→右列序(血缘流向:源→任务→模型→指标)
const COLORS = { datasource: '#409eff', task: '#e6a23c', model: '#67c23a', metric: '#9254de' }
const COL = { datasource: 0, task: 1, model: 2, metric: 3 }
const TYPE_LABEL = { datasource: '源', task: '任务', model: '模型', metric: '指标' }

async function load() {
  if (!props.model?.id) return
  loading.value = true
  try {
    const res = await getLineage({ nodeType: 'model', nodeId: props.model.id, depth: 3 })
    const g = res.data || { nodes: [], edges: [] }
    empty.value = !g.nodes || g.nodes.length <= 1
    await nextTick()
    render(g)
  } finally {
    loading.value = false
  }
}

function render(g) {
  if (!chartEl.value) return
  if (!chart) chart = echarts.init(chartEl.value)
  const nodes = g.nodes || []
  const edges = g.edges || []

  // 按类型分列布局:每列纵向均分;列间距/行距固定,居中
  const byCol = { 0: [], 1: [], 2: [], 3: [] }
  nodes.forEach((n) => byCol[COL[n.type] ?? 2].push(n))
  const colGap = 260
  const rowGap = 84
  const maxRows = Math.max(1, ...Object.values(byCol).map((a) => a.length))
  canvasH = Math.max(320, maxRows * rowGap + 40)

  const enodes = []
  Object.entries(byCol).forEach(([col, arr]) => {
    const c = Number(col)
    const offset = (maxRows - arr.length) / 2 // 每列居中
    arr.forEach((n, i) => {
      enodes.push({
        id: n.id,
        name: (n.name || n.id) + (n.id === `model:${props.model.id}` ? ' ★' : ''),
        value: n.type,
        x: 60 + c * colGap,
        y: 30 + (offset + i) * rowGap,
        symbol: n.type === 'metric' ? 'diamond' : n.type === 'datasource' ? 'roundRect' : 'rect',
        symbolSize: n.id === `model:${props.model.id}` ? [150, 46] : [128, 38],
        itemStyle: { color: COLORS[n.type] || '#909399', borderColor: '#fff', borderWidth: 1 },
        label: { show: true, position: 'inside', color: '#fff', fontSize: 12, overflow: 'truncate', width: 116 },
        tooltip: { formatter: `${TYPE_LABEL[n.type] || ''}:${n.name || n.id}` },
      })
    })
  })

  const eedges = edges.map((e) => ({
    source: e.source,
    target: e.target,
    label: { show: true, formatter: e.label || '', fontSize: 11, color: '#606266' },
    lineStyle: { color: '#c0c4cc', width: 1.5, curveness: 0.06, opacity: 0.9 },
  }))

  chart.setOption(
    {
      tooltip: {},
      animationDuration: 300,
      series: [
        {
          type: 'graph',
          layout: 'none',
          roam: true,
          edgeSymbol: ['none', 'arrow'],
          edgeSymbolSize: 8,
          data: enodes,
          links: eedges,
          emphasis: { focus: 'adjacency' },
        },
      ],
    },
    true,
  )
  chart.resize({ height: canvasH })
  if (chartEl.value) chartEl.value.style.height = canvasH + 'px'
  chart.resize()
}

// 仅在容器可见(有宽度)时重绘;隐藏(display:none,宽=0)时跳过,避免图在 0 宽下被重算而变形
const onResize = () => {
  if (!chart || !chartEl.value || chartEl.value.clientWidth <= 0) return
  chartEl.value.style.height = canvasH + 'px'
  chart.resize()
}
onMounted(() => {
  ro = new ResizeObserver(onResize)
  ro.observe(chartEl.value)
  load()
})
onBeforeUnmount(() => { ro && ro.disconnect(); chart && chart.dispose() })
watch(() => props.model?.id, load)
</script>

<style scoped lang="scss">
.lineage-tab { display: flex; flex-direction: column; }
.lin-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 8px; }
.lin-toolbar .hint { font-size: 12px; color: #909399; }
.lin-canvas-wrap { position: relative; border: 1px solid #ebeef5; border-radius: 4px; overflow: auto; background: #fafafa; }
.lin-canvas { width: 100%; height: 360px; }
.legend { display: flex; gap: 18px; margin-top: 8px; font-size: 12px; color: #606266; }
.legend .sq { display: inline-block; width: 12px; height: 12px; border-radius: 2px; margin-right: 4px; vertical-align: middle; }
</style>
