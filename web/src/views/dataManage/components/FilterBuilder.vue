<template>
  <div class="filter-builder">
    <div v-for="(f, i) in filters" :key="i" class="filter-row">
      <el-select v-model="f.field" :placeholder="$t('字段')" filterable style="width: 170px">
        <el-option v-for="c in fields" :key="c.name" :label="c.name" :value="c.name" />
      </el-select>
      <el-select v-model="f.op" :placeholder="$t('操作符')" style="width: 120px">
        <el-option v-for="o in operators" :key="o.op" :label="o.label" :value="o.op" />
      </el-select>
      <el-input v-if="!isSort(f.op)" v-model="f.value" :placeholder="$t('值')" style="width: 180px" />
      <el-button icon="Delete" link @click="filters.splice(i, 1)" />
    </div>
    <el-button size="small" icon="Plus" @click="filters.push({ field: '', op: 'eq', value: '' })">{{ $t('加条件') }}</el-button>
  </div>
</template>

<script setup name="FilterBuilder">
// 统一的条件筛选行编辑器(字段/操作符/值 + 增删),供「数据接口」「自助分析」等复用。
// v-model 绑定 [{field,op,value}] 数组;值一律原样透传,由后端 handler.search 解释。
const filters = defineModel({ type: Array, default: () => [] })
defineProps({
  fields: { type: Array, default: () => [] }, // [{name,...}]
  operators: { type: Array, default: () => [] }, // [{op,label}]
})
const isSort = op => op === 'sort_asc' || op === 'sort_desc'
</script>

<style scoped>
.filter-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
</style>
