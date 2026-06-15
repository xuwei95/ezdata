<template>
  <div class="dynamic-params-form">
    <el-empty v-if="!schema.length" description="该模板无可配置参数" :image-size="60" />
    <el-form-item
      v-for="item in schema"
      :key="item.field"
      :label="item.label || item.field"
      :prop="item.field"
      :rules="buildRules(item)"
    >
      <!-- 数字 -->
      <el-input-number
        v-if="item.component === 'number'"
        v-model="model[item.field]"
        :min="item.min"
        :max="item.max"
        controls-position="right"
        style="width: 100%"
      />
      <!-- 开关 -->
      <el-switch v-else-if="item.component === 'switch'" v-model="model[item.field]" />
      <!-- 下拉 -->
      <el-select
        v-else-if="item.component === 'select'"
        v-model="model[item.field]"
        :placeholder="item.placeholder || '请选择'"
        clearable
        style="width: 100%"
      >
        <el-option v-for="opt in item.options || []" :key="optVal(opt)" :label="optLabel(opt)" :value="optVal(opt)" />
      </el-select>
      <!-- 代码 -->
      <code-editor
        v-else-if="item.component === 'code'"
        v-model="model[item.field]"
        :language="item.language || 'python'"
        :placeholder="item.placeholder || ''"
      />
      <!-- JSON -->
      <code-editor
        v-else-if="item.component === 'json'"
        v-model="model[item.field]"
        language="json"
        :placeholder="item.placeholder || ''"
      />
      <!-- 多行文本 -->
      <el-input
        v-else-if="item.component === 'textarea'"
        v-model="model[item.field]"
        type="textarea"
        :rows="4"
        :placeholder="item.placeholder || ''"
      />
      <!-- 默认单行文本 -->
      <el-input v-else v-model="model[item.field]" :placeholder="item.placeholder || ''" clearable />
      <div v-if="item.tip" class="form-tip">{{ item.tip }}</div>
    </el-form-item>
  </div>
</template>

<script setup name="DynamicParamsForm">
import CodeEditor from '@/components/CodeEditor'

const props = defineProps({
  // 参数schema(JSON数组)
  schema: {
    type: Array,
    default: () => []
  },
  // 参数值对象(v-model)
  modelValue: {
    type: Object,
    default: () => ({})
  }
})
const emit = defineEmits(['update:modelValue'])

// 直接复用传入对象作为响应式模型
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

function buildRules(item) {
  const rules = []
  if (item.required) {
    rules.push({ required: true, message: (item.label || item.field) + '不能为空', trigger: 'blur' })
  }
  if (item.component === 'json') {
    rules.push({
      trigger: 'blur',
      validator: (rule, value, cb) => {
        if (value === undefined || value === null || value === '') return cb()
        try {
          JSON.parse(value)
          cb()
        } catch (e) {
          cb(new Error((item.label || item.field) + '不是合法的JSON'))
        }
      }
    })
  }
  return rules
}
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
