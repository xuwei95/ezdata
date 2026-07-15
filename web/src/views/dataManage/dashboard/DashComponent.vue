<template>
  <div class="dash-comp" :class="'dc-' + (comp.type || 'chart')">
    <!-- 图表:引用已有看板 或 内嵌配置;有外部 rows/cfg(公开页)则直接用,否则自取数 -->
    <template v-if="comp.type === 'chart'">
      <div v-if="displayRows.length && displayCfg" class="dc-chart">
        <EchartsBuilder :rows="displayRows" :config="displayCfg" :show-controls="false" :height="height" :dark="dark" />
      </div>
      <div v-else class="dc-empty">{{ err || (loading ? '加载中…' : '无数据') }}</div>
    </template>
    <!-- 文本 -->
    <div v-else-if="comp.type === 'text'" class="dc-text" :style="comp.props && comp.props.style">
      {{ (comp.props && comp.props.text) || '文本' }}
    </div>
    <!-- 图片 -->
    <img v-else-if="comp.type === 'image'" class="dc-img" :src="comp.props && comp.props.url" alt="" />
    <!-- 其它(filter/tab 等,P2)占位 -->
    <div v-else class="dc-empty">{{ comp.type }}</div>
  </div>
</template>

<script setup name="DashComponent">
import { ref, computed, watch, onMounted } from 'vue'
import EchartsBuilder from '@/views/dataManage/visualization/EchartsBuilder.vue'
import { fetchBoardRows } from '@/views/dataManage/visualization/board.js'
import { getDashboard } from '@/api/dataManage/data'

const props = defineProps({
  comp: { type: Object, required: true },
  rows: { type: Array, default: null }, // 外部已取好的行(公开页/联动)
  chartSpec: { type: Object, default: null }, // 外部已解析的图表配置
  params: { type: Object, default: null }, // 全局筛选值 {name: value}
  height: { type: Number, default: 300 },
  dark: { type: Boolean, default: false }, // 大屏(暗底)模式:图表透明底 + 明色轴/文字
  silent: { type: Boolean, default: false }, // 预览/展示模式:取数失败不弹 msg,只打 console + 卡片内提示
})

const localRows = ref([])
const localCfg = ref(null)
const loading = ref(false)
const err = ref('')

// 优先级:显式 props > 组件自带(公开页 /open/dashboard 已附 rows/chartSpec)> 自取
const displayRows = computed(() => (props.rows != null ? props.rows : (props.comp.rows != null ? props.comp.rows : localRows.value)))
// 内嵌图表配置直接取 comp.inline.chartSpec(样式改动无需再取数即可反映);引用组件用 localCfg 兜底
const displayCfg = computed(() => props.chartSpec || props.comp.chartSpec || (props.comp.inline && props.comp.inline.chartSpec) || localCfg.value)

// 解析组件的图表配置:内嵌直接用;引用则拉那条 chart 看板的组件配置
async function resolveChart() {
  const c = props.comp
  if (c.type !== 'chart' || props.rows != null || c.rows != null) return // 外部已给数据,无需自取
  let modelId, native, cfg
  if (c.inline && c.inline.native != null) {
    modelId = c.inline.modelId; native = c.inline.native; cfg = c.inline.chartSpec
  } else if (c.ref && c.ref.boardId) {
    try {
      const d = (await getDashboard(c.ref.boardId, props.silent)).data || {}
      const comp0 = (d.components || [])[0] || {}
      const inl = comp0.inline || {}
      modelId = inl.modelId; native = inl.native; cfg = inl.chartSpec
    } catch (e) { err.value = '引用的看板不存在'; return }
  }
  localCfg.value = cfg || null
  if (!modelId || native == null) { err.value = '组件无有效查询'; return }
  loading.value = true; err.value = ''
  try {
    localRows.value = await fetchBoardRows(modelId, native, props.params, 5000, props.silent)
    if (!localRows.value.length) err.value = '查询无数据'
  } catch (e) { err.value = '取数失败'; if (props.silent) console.warn('[DashComponent] 取数失败', modelId, e?.message || e) } finally { loading.value = false }
}

// 只在"取数相关"字段变化时重新取数(modelId/native/ref/params);
// pos(拖拽/缩放/布局)、chartSpec(样式)变化不触发,避免拖动时狂发查询、失败弹窗刷屏。
watch(
  () => [
    props.comp && props.comp.inline && props.comp.inline.modelId,
    props.comp && props.comp.inline && props.comp.inline.native,
    props.comp && props.comp.ref && props.comp.ref.boardId,
    props.params,
  ],
  resolveChart,
  { deep: true }
)
onMounted(resolveChart)
</script>

<style scoped>
/* 底色交给外层:矩阵卡片由 .dg-item 提供白底;自由模式(大屏)保持透明,透出暗背景 */
.dash-comp { width: 100%; height: 100%; overflow: hidden; background: transparent; }
.dc-chart { width: 100%; height: 100%; }
.dc-empty { display: flex; align-items: center; justify-content: center; height: 100%; color: #909399; font-size: 13px; }
.dc-text { padding: 8px 12px; white-space: pre-wrap; word-break: break-word; }
.dc-img { width: 100%; height: 100%; object-fit: contain; }
</style>
