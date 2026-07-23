<template>
  <!-- 看板顶部筛选栏:按变量定义(filters)渲一排表单控件,值写进 modelValue(filterValues)。
       无变量则不渲染,保证无筛选的看板视觉不变。控件样式对齐 ChartEditor 的筛选栏。 -->
  <div v-if="filters && filters.length" class="dash-filter-bar" :class="{ dark }">
    <template v-for="f in filters" :key="f.name">
      <span class="fb-label">{{ f.label || f.name }}</span>
      <el-date-picker v-if="f.type === 'date'" :model-value="modelValue[f.name]" type="date" value-format="YYYY-MM-DD"
        size="small" style="width: 150px" @update:model-value="(v) => set(f.name, v)" />
      <el-date-picker v-else-if="f.type === 'daterange'" :model-value="modelValue[f.name]" type="daterange" value-format="YYYY-MM-DD"
        size="small" style="width: 230px" :start-placeholder="$t('开始')" :end-placeholder="$t('结束')" @update:model-value="(v) => set(f.name, v)" />
      <el-select v-else-if="f.type === 'select'" :model-value="modelValue[f.name]" size="small" clearable style="width: 150px"
        @update:model-value="(v) => set(f.name, v)">
        <el-option v-for="o in optionList(f)" :key="o" :label="o" :value="o" />
      </el-select>
      <el-input-number v-else-if="f.type === 'number'" :model-value="numOf(modelValue[f.name])" size="small" controls-position="right"
        style="width: 130px" @update:model-value="(v) => set(f.name, v)" />
      <el-input v-else :model-value="modelValue[f.name]" size="small" clearable style="width: 150px"
        @update:model-value="(v) => set(f.name, v)" />
    </template>
    <el-button size="small" text icon="RefreshLeft" class="fb-reset" @click="reset">{{ $t('重置') }}</el-button>
  </div>
</template>

<script setup name="DashFilterBar">
// 变量定义 → 控件;值以「就地改 modelValue[name]」写回(与 ChartEditor 一致,父级 reactive 会联动)。
const props = defineProps({
  filters: { type: Array, default: () => [] }, // [{name,label,type,default,options,optionsText}]
  modelValue: { type: Object, default: () => ({}) }, // filterValues {name: value}
  dark: { type: Boolean, default: false }, // 大屏深色底
})
const emit = defineEmits(['update:modelValue', 'change'])

// select 选项:优先 options 数组(存储态),兜底 optionsText 逗号串(编辑态)
function optionList(f) {
  if (Array.isArray(f.options) && f.options.length) return f.options
  return (f.optionsText || '').split(',').map((s) => s.trim()).filter(Boolean)
}
function numOf(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : undefined
}
function set(name, v) {
  props.modelValue[name] = v // 就地改(reactive,父级 chartParams computed 会重算)
  emit('update:modelValue', props.modelValue)
  emit('change', { name, value: v })
}
function reset() {
  for (const f of props.filters || []) {
    if (!f || !f.name) continue
    props.modelValue[f.name] = f.default ?? (f.type === 'daterange' ? null : '')
  }
  emit('update:modelValue', props.modelValue)
  emit('change', { name: '', value: null })
}
</script>

<style scoped>
.dash-filter-bar { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 10px; padding: 8px 10px; margin-bottom: 8px;
  background: #f5f7fa; border: 1px solid #ebeef5; border-radius: 6px; }
.dash-filter-bar.dark { background: rgba(255, 255, 255, 0.06); border-color: rgba(255, 255, 255, 0.12); }
.fb-label { font-size: 13px; color: #606266; margin-left: 4px; }
.dash-filter-bar.dark .fb-label { color: #cfe3ff; }
.fb-reset { margin-left: auto; }
</style>
