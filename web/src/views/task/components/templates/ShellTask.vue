<template>
  <div class="builtin-task-form">
    <el-form label-width="90px">
      <el-form-item label="运行模式" required>
        <el-radio-group v-model="model.run_type">
          <el-radio value="code">代码模式</el-radio>
          <el-radio value="file">文件模式</el-radio>
        </el-radio-group>
      </el-form-item>

      <template v-if="model.run_type === 'code'">
        <el-form-item label="Shell脚本" required>
          <code-editor v-model="model.code" language="shell" height="280px" placeholder="输入 Shell 命令/脚本" />
        </el-form-item>
      </template>

      <template v-else>
        <el-form-item label="文件地址" required>
          <el-input v-model="model.file" placeholder="worker 可访问的脚本文件绝对路径" clearable />
        </el-form-item>
        <el-form-item label="额外参数">
          <el-input v-model="model.run_params" placeholder="命令行参数(可选)" clearable />
        </el-form-item>
      </template>
    </el-form>
  </div>
</template>

<script setup name="ShellTask">
import CodeEditor from '@/components/CodeEditor'

const props = defineProps({
  taskParams: { type: Object, default: () => ({}) },
  templateInfo: { type: Object, default: () => ({}) }
})

const DEFAULT_CODE = 'echo "hello from shell task"'

const model = reactive({ run_type: 'code', code: DEFAULT_CODE, file: '', run_params: '' })

function initParams() {
  const p = props.taskParams || {}
  model.run_type = p.run_type || 'code'
  // 兼容旧字段 command
  const code = p.code !== undefined && p.code !== '' ? p.code : p.command
  model.code = code !== undefined && code !== '' ? code : DEFAULT_CODE
  model.file = p.file || ''
  model.run_params = p.run_params || ''
}
onMounted(initParams)
watch(() => props.taskParams, initParams, { deep: true })

function genTaskParams() {
  if (model.run_type === 'code') {
    if (!model.code || !model.code.trim()) return { error: 'Shell脚本不能为空' }
    return { params: { run_type: 'code', code: model.code } }
  }
  if (!model.file || !model.file.trim()) return { error: '文件地址不能为空' }
  return { params: { run_type: 'file', file: model.file, run_params: model.run_params || '' } }
}

defineExpose({ genTaskParams })
</script>
