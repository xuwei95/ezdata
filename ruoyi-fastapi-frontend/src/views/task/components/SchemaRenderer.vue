<template>
  <div class="schema-renderer">
    <el-empty v-if="!schema.length" description="该模板无可配置参数" :image-size="60" />
    <el-form-item
      v-for="item in schema"
      :key="item.field"
      :label="item.label || item.field"
      :required="!!item.required"
    >
      <el-input-number
        v-if="item.component === 'number'"
        v-model="model[item.field]"
        :min="item.min"
        :max="item.max"
        controls-position="right"
        style="width: 100%"
      />
      <el-switch v-else-if="item.component === 'switch'" v-model="model[item.field]" />
      <el-select
        v-else-if="item.component === 'select'"
        v-model="model[item.field]"
        :placeholder="item.placeholder || '请选择'"
        clearable
        style="width: 100%"
      >
        <el-option v-for="opt in item.options || []" :key="optVal(opt)" :label="optLabel(opt)" :value="optVal(opt)" />
      </el-select>
      <el-radio-group v-else-if="item.component === 'radio'" v-model="model[item.field]">
        <el-radio v-for="opt in item.options || []" :key="optVal(opt)" :value="optVal(opt)">{{ optLabel(opt) }}</el-radio>
      </el-radio-group>
      <el-date-picker
        v-else-if="item.component === 'date'"
        v-model="model[item.field]"
        type="datetime"
        value-format="YYYY-MM-DD HH:mm:ss"
        :placeholder="item.placeholder || '请选择时间'"
        style="width: 100%"
      />
      <code-editor
        v-else-if="item.component === 'code'"
        v-model="model[item.field]"
        :language="item.language || 'python'"
        :placeholder="item.placeholder || ''"
      />
      <code-editor
        v-else-if="item.component === 'json'"
        v-model="model[item.field]"
        language="json"
        :placeholder="item.placeholder || ''"
      />
      <el-input
        v-else-if="item.component === 'textarea'"
        v-model="model[item.field]"
        type="textarea"
        :rows="4"
        :placeholder="item.placeholder || ''"
      />
      <el-input v-else v-model="model[item.field]" :placeholder="item.placeholder || ''" clearable />
      <div v-if="item.tip" class="form-tip">{{ item.tip }}</div>
    </el-form-item>
  </div>
</template>

<script setup name="SchemaRenderer">
import CodeEditor from '@/components/CodeEditor'

const props = defineProps({
  schema: { type: Array, default: () => [] },
  modelValue: { type: Object, default: () => ({}) }
})
const emit = defineEmits(['update:modelValue'])

const model = computed({
  get: () => props.modelValue || {},
  set: val => emit('update:modelValue', val)
})

function optVal(opt) {
  return typeof opt === 'object' ? opt.value : opt
}
function optLabel(opt) {
  return typeof opt === 'object' ? opt.label : opt
}

// 校验参数(由父级在提交时调用)：返回第一个错误信息，全部通过返回 null
// - 必填项为空 → 报错
// - json 组件非空 → 校验是否为合法 JSON
function validate() {
  for (const item of props.schema || []) {
    const v = (props.modelValue || {})[item.field]
    const empty = v === undefined || v === null || v === '' || (Array.isArray(v) && v.length === 0)
    if (item.required && empty) return (item.label || item.field) + '不能为空'
    if (item.component === 'json' && !empty) {
      try {
        JSON.parse(v)
      } catch (e) {
        return (item.label || item.field) + '不是合法的JSON'
      }
    }
  }
  return null
}

defineExpose({ validate })
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
.code-area :deep(textarea) {
  font-family: Consolas, Monaco, 'Courier New', monospace;
}
</style>
