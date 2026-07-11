<template>
  <div class="gw-spike">
    <div class="spike-tip">
      <el-tag type="warning" size="small">试验:原生 graphic-walker 0.4(veaury 引 React 组件)</el-tag>
      <span class="muted">验证点:能渲染 / 中文 / 样式正常 / 比 iframe 快</span>
    </div>
    <GW v-if="rows.length" :key="rows.length" :data="rows" :fields="fields"
      i18nLang="zh-CN" appearance="light" :style="{ height: '520px' }" />
    <el-empty v-else description="先查询出数据" />
  </div>
</template>

<script setup name="GwSpike">
import { computed } from 'vue'
import { applyPureReactInVue } from 'veaury'
import { GraphicWalker } from '@kanaries/graphic-walker'
import '@kanaries/graphic-walker/dist/style.css'

// 用 veaury 把 React 组件 GraphicWalker 包成 Vue 组件(预构建 npm 包,无需改 vite 插件)
const GW = applyPureReactInVue(GraphicWalker)

const props = defineProps({ rows: { type: Array, default: () => [] } })

// 由首行推断字段:数字→度量,其余→维度(graphic-walker 0.4 用 data + fields)
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
