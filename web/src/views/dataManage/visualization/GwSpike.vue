<template>
  <div class="gw-spike">
    <div class="spike-tip">
      <el-tag type="warning" size="small">试验:原生 graphic-walker(Vue 组件,非 iframe)</el-tag>
      <span class="muted">验证点:能否拖拽出图 / 中文 / 比 iframe 快</span>
    </div>
    <VueGraphicWalker v-if="rows.length" :key="rows.length" :dataSource="rows" :rawFields="fields"
      i18nLang="zh-CN" :toolbar="toolbar" style="height: 520px" />
    <el-empty v-else description="先查询出数据" />
  </div>
</template>

<script setup name="GwSpike">
import { computed } from 'vue'
import { VueGraphicWalker } from '@kanaries/vue-graphic-walker'

const props = defineProps({ rows: { type: Array, default: () => [] } })
const toolbar = { exclude: [] }

// 由行数据首行推断字段类型:数字→度量(quantitative),其余→维度(nominal)
const fields = computed(() => {
  const r = props.rows[0] || {}
  return Object.keys(r).map((k) => {
    const num = typeof r[k] === 'number'
    return { fid: k, name: k, semanticType: num ? 'quantitative' : 'nominal', analyticType: num ? 'measure' : 'dimension' }
  })
})
</script>

<style scoped>
.spike-tip { margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
.spike-tip .muted { font-size: 12px; color: #909399; }
</style>
