<template>
  <div class="schema-designer">
    <div class="designer-toolbar">
      <el-button type="primary" size="small" icon="Plus" @click="addField">添加字段</el-button>
      <el-button size="small" icon="View" @click="previewVisible = !previewVisible">
        {{ previewVisible ? '隐藏预览' : '实时预览' }}
      </el-button>
      <span class="tip">可视化配置任务参数表单，任务创建时按此自动渲染</span>
    </div>

    <el-table :data="fields" size="small" border class="designer-table">
      <el-table-column label="排序" width="70" align="center">
        <template #default="scope">
          <el-button link icon="Top" :disabled="scope.$index === 0" @click="move(scope.$index, -1)" />
          <el-button link icon="Bottom" :disabled="scope.$index === fields.length - 1" @click="move(scope.$index, 1)" />
        </template>
      </el-table-column>
      <el-table-column label="字段标识" width="150">
        <template #default="scope">
          <el-input v-model="scope.row.field" placeholder="如 code" size="small" @input="emitChange" />
        </template>
      </el-table-column>
      <el-table-column label="标签" width="150">
        <template #default="scope">
          <el-input v-model="scope.row.label" placeholder="如 Python代码" size="small" @input="emitChange" />
        </template>
      </el-table-column>
      <el-table-column label="组件类型" width="140">
        <template #default="scope">
          <el-select v-model="scope.row.component" size="small" @change="emitChange">
            <el-option v-for="c in componentTypes" :key="c.value" :label="c.label" :value="c.value" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="必填" width="70" align="center">
        <template #default="scope">
          <el-switch v-model="scope.row.required" @change="emitChange" />
        </template>
      </el-table-column>
      <el-table-column label="占位/提示" min-width="160">
        <template #default="scope">
          <el-input v-model="scope.row.placeholder" placeholder="placeholder" size="small" @input="emitChange" />
        </template>
      </el-table-column>
      <el-table-column label="选项" width="90" align="center">
        <template #default="scope">
          <el-button
            v-if="['select', 'radio'].includes(scope.row.component)"
            link
            type="primary"
            size="small"
            @click="editOptions(scope.$index)"
          >
            选项({{ (scope.row.options || []).length }})
          </el-button>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="70" align="center">
        <template #default="scope">
          <el-button link type="danger" icon="Delete" @click="removeField(scope.$index)" />
        </template>
      </el-table-column>
    </el-table>

    <!-- 实时预览 -->
    <div v-if="previewVisible" class="preview-box">
      <div class="preview-title">表单预览</div>
      <el-form label-width="110px">
        <schema-renderer :schema="fields" v-model="previewModel" />
      </el-form>
    </div>

    <!-- 选项编辑 -->
    <el-dialog v-model="optionsDialog" title="选项配置" width="520px" append-to-body>
      <el-table :data="editingOptions" size="small" border>
        <el-table-column label="选项标签">
          <template #default="scope"><el-input v-model="scope.row.label" size="small" /></template>
        </el-table-column>
        <el-table-column label="选项值">
          <template #default="scope"><el-input v-model="scope.row.value" size="small" /></template>
        </el-table-column>
        <el-table-column label="操作" width="70" align="center">
          <template #default="scope">
            <el-button link type="danger" icon="Delete" @click="editingOptions.splice(scope.$index, 1)" />
          </template>
        </el-table-column>
      </el-table>
      <el-button size="small" icon="Plus" style="margin-top: 8px" @click="editingOptions.push({ label: '', value: '' })">添加选项</el-button>
      <template #footer>
        <el-button type="primary" @click="saveOptions">确 定</el-button>
        <el-button @click="optionsDialog = false">取 消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="SchemaDesigner">
import SchemaRenderer from './SchemaRenderer.vue'

const props = defineProps({
  // 参数schema(JSON字符串)
  modelValue: { type: String, default: '' }
})
const emit = defineEmits(['update:modelValue'])

const componentTypes = [
  { label: '单行文本', value: 'text' },
  { label: '多行文本', value: 'textarea' },
  { label: '代码编辑', value: 'code' },
  { label: 'JSON编辑', value: 'json' },
  { label: '数字', value: 'number' },
  { label: '下拉选择', value: 'select' },
  { label: '单选', value: 'radio' },
  { label: '开关', value: 'switch' },
  { label: '日期时间', value: 'date' }
]

const fields = ref([])
const previewVisible = ref(false)
const previewModel = ref({})

const optionsDialog = ref(false)
const editingOptions = ref([])
const editingIndex = ref(-1)

watch(
  () => props.modelValue,
  val => {
    fields.value = parse(val)
  },
  { immediate: true }
)

function parse(raw) {
  if (!raw) return []
  try {
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr : []
  } catch (e) {
    return []
  }
}

function emitChange() {
  emit('update:modelValue', JSON.stringify(fields.value))
}

function addField() {
  fields.value.push({ field: '', label: '', component: 'text', required: false, placeholder: '', options: [] })
  emitChange()
}

function removeField(idx) {
  fields.value.splice(idx, 1)
  emitChange()
}

function move(idx, dir) {
  const target = idx + dir
  if (target < 0 || target >= fields.value.length) return
  const arr = fields.value
  ;[arr[idx], arr[target]] = [arr[target], arr[idx]]
  emitChange()
}

function editOptions(idx) {
  editingIndex.value = idx
  editingOptions.value = JSON.parse(JSON.stringify(fields.value[idx].options || []))
  optionsDialog.value = true
}

function saveOptions() {
  if (editingIndex.value > -1) {
    fields.value[editingIndex.value].options = editingOptions.value.filter(o => o.label !== '' || o.value !== '')
    emitChange()
  }
  optionsDialog.value = false
}
</script>

<style scoped>
.designer-toolbar {
  margin-bottom: 10px;
}
.designer-toolbar .tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}
.preview-box {
  margin-top: 14px;
  padding: 14px;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  background: #fafafa;
}
.preview-title {
  font-size: 13px;
  color: #606266;
  margin-bottom: 10px;
  font-weight: 600;
}
</style>
