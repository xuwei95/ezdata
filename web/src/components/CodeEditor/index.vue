<template>
  <div class="code-editor" :class="{ 'is-disabled': readOnly }">
    <div class="code-editor__toolbar">
      <span class="code-editor__lang">{{ langLabel }}</span>
      <el-button
        v-if="!readOnly"
        link
        type="primary"
        size="small"
        icon="MagicStick"
        :title="formatTip"
        @click="format"
      >{{ $t('格式化') }}</el-button>
    </div>
    <div ref="el" class="code-editor__body" :style="{ height }"></div>
  </div>
</template>

<script setup name="CodeEditor">
import * as monaco from 'monaco-editor'

const props = defineProps({
  modelValue: { type: String, default: '' },
  language: { type: String, default: 'python' },
  height: { type: String, default: '220px' },
  readOnly: { type: Boolean, default: false },
  placeholder: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const el = ref(null)
let editor = null
let suppressEmit = false

const langLabel = computed(() => {
  const map = { python: 'Python', json: 'JSON', shell: 'Shell', javascript: 'JavaScript', sql: 'SQL' }
  return map[props.language] || props.language
})
const formatTip = computed(() =>
  props.language === 'json' ? '格式化 JSON' : 'Python 简易格式化（缩进规范化，非完整 PEP8）'
)

onMounted(() => {
  nextTick(() => {
    editor = monaco.editor.create(el.value, {
      value: props.modelValue || '',
      language: props.language,
      readOnly: props.readOnly,
      automaticLayout: true,
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      fontSize: 13,
      tabSize: 4,
      lineNumbers: 'on',
      renderWhitespace: 'selection',
      scrollbar: { alwaysConsumeMouseWheel: false }
    })
    editor.onDidChangeModelContent(() => {
      if (suppressEmit) return
      emit('update:modelValue', editor.getValue())
    })
  })
})

onBeforeUnmount(() => {
  if (editor) {
    editor.dispose()
    editor = null
  }
})

// 外部值变化时同步到编辑器（仅在不一致时 setValue，避免打断输入光标）
watch(
  () => props.modelValue,
  val => {
    if (!editor) return
    const cur = editor.getValue()
    if ((val || '') !== cur) {
      suppressEmit = true
      editor.setValue(val || '')
      suppressEmit = false
    }
  }
)

watch(
  () => props.language,
  lang => {
    if (editor) monaco.editor.setModelLanguage(editor.getModel(), lang)
  }
)

// Python 简易格式化：去行尾空白、tab→4空格、压缩多余空行、保证末尾换行（保留原有缩进结构）
function formatPython(code) {
  const lines = (code || '').replace(/\t/g, '    ').split(/\r?\n/).map(l => l.replace(/\s+$/, ''))
  const out = []
  let blank = 0
  for (const line of lines) {
    if (line === '') {
      blank += 1
      if (blank <= 1) out.push('')
    } else {
      blank = 0
      out.push(line)
    }
  }
  while (out.length && out[out.length - 1] === '') out.pop()
  return out.join('\n') + '\n'
}

async function format() {
  if (!editor) return
  if (props.language === 'json') {
    // 借助 monaco json worker 的内置格式化
    await editor.getAction('editor.action.formatDocument')?.run()
    return
  }
  if (props.language === 'python') {
    const model = editor.getModel()
    const formatted = formatPython(editor.getValue())
    // 用 executeEdits 替换全文以保留撤销栈
    editor.executeEdits('format-python', [{ range: model.getFullModelRange(), text: formatted }])
    editor.pushUndoStop()
    return
  }
  await editor.getAction('editor.action.formatDocument')?.run()
}

defineExpose({ format })
</script>

<style scoped>
.code-editor {
  border: 1px solid var(--el-border-color, #dcdfe6);
  border-radius: 4px;
  overflow: hidden;
  width: 100%;
}
.code-editor.is-disabled {
  background: var(--el-disabled-bg-color, #f5f7fa);
}
.code-editor__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 30px;
  padding: 0 8px;
  background: var(--el-fill-color-light, #f5f7fa);
  border-bottom: 1px solid var(--el-border-color-lighter, #ebeef5);
}
.code-editor__lang {
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
}
.code-editor__body {
  width: 100%;
}
</style>
