<template>
  <el-dialog
    :title="$t('新增文档')"
    v-model="dialogVisible"
    width="620px"
    append-to-body
    :close-on-click-modal="false"
  >
    <el-form ref="docRef" :model="docForm" :rules="docRules" label-position="top">
      <el-form-item :label="$t('来源类型')">
        <el-radio-group v-model="docForm.documentType" @change="onTypeChange">
          <el-radio-button value="upload_file"><el-icon><Upload /></el-icon> {{ $t('上传文件') }}</el-radio-button>
          <el-radio-button value="text"><el-icon><Document /></el-icon> {{ $t('粘贴文本') }}</el-radio-button>
          <el-radio-button value="website"><el-icon><Link /></el-icon> {{ $t('网页') }}</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <!-- 文件:拖拽上传 -->
      <el-form-item v-if="docForm.documentType === 'upload_file'" :label="$t('文件')">
        <el-upload drag :action="uploadUrl" :headers="uploadHeaders" :limit="1" :show-file-list="false"
          :before-upload="beforeUpload" :on-progress="onProgress" :on-success="onUploaded"
          :on-error="onUploadError" style="width: 100%">
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">{{ $t('拖拽文件到此处,或') }}<em>{{ $t('点击上传') }}</em></div>
          <template #tip><div class="up-tip">{{ $t('支持 txt / md / pdf / csv / xlsx / docx / html / json,单文件 ≤ 50MB') }}</div></template>
        </el-upload>
        <el-progress v-if="uploading" :percentage="uploadPercent" :stroke-width="6" status="success" style="margin-top: 8px" />
        <div v-else-if="docForm.uploadedName" class="uploaded">
          <el-icon color="#67c23a"><CircleCheck /></el-icon>
          <span>{{ docForm.uploadedName }}</span>
          <el-button link type="danger" icon="Close" @click="clearUpload">{{ $t('移除') }}</el-button>
        </div>
      </el-form-item>

      <!-- 文本 -->
      <el-form-item v-if="docForm.documentType === 'text'" :label="$t('文本内容')">
        <el-input v-model="docForm.text" type="textarea" :rows="8" :placeholder="$t('粘贴要入库的文本内容')" />
      </el-form-item>

      <!-- 网页 -->
      <el-form-item v-if="docForm.documentType === 'website'" :label="$t('网页 URL')">
        <el-input v-model="docForm.source" placeholder="https://example.com/article">
          <template #prepend><el-icon><Link /></el-icon></template>
        </el-input>
      </el-form-item>

      <el-form-item :label="$t('文档名')" prop="name">
        <el-input v-model="docForm.name" :placeholder="$t('文档名(上传文件会自动填充)')" />
      </el-form-item>

      <el-form-item :label="$t('切分策略')">
        <el-select v-model="docForm.strategy" style="width: 200px">
          <el-option :label="$t('递归(默认)')" value="recursive" />
          <el-option :label="$t('固定大小')" value="fixed" />
          <el-option :label="$t('按文档段落')" value="document" />
          <el-option :label="$t('按 Markdown 标题')" value="markdown" />
          <el-option :label="$t('语义切分(更准)')" value="semantic" />
        </el-select>
        <el-tooltip :content="$t('语义切分按内容语义边界分块,召回更准,但训练时会多调用 embedding')" placement="top">
          <el-icon style="margin-left:6px;color:#909399"><QuestionFilled /></el-icon>
        </el-tooltip>
      </el-form-item>
      <el-form-item :label="$t('切分设置')">
        <div class="chunk-cfg">
          <span>{{ $t('每段') }}</span>
          <el-input-number v-model="docForm.chunkSize" :min="128" :max="4000" :step="64" controls-position="right" />
          <span>{{ $t('字符,重叠') }}</span>
          <el-input-number v-model="docForm.chunkOverlap" :min="0" :max="1000" :step="20" controls-position="right" />
          <span>{{ $t('字符') }}</span>
        </div>
      </el-form-item>
      <el-form-item :label="$t('上下文增强')">
        <el-switch v-model="docForm.contextual" />
        <span class="up-tip" style="margin-left:8px">{{ $t('为每段附 LLM 生成的上下文背景(Contextual Retrieval),召回更准但训练更慢') }}</span>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">{{ $t('取 消') }}</el-button>
      <el-button type="primary" :loading="docSubmitting" @click="submitDoc">{{ $t('创建并训练') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup name="DocumentImportDialog">
import { ref, computed, watch, getCurrentInstance } from 'vue'
import { addDocument } from '@/api/rag'
import { getToken } from '@/utils/auth'

// 通用「新增文档」对话框:上传文件 / 粘贴文本 / 网页导入 → addDocument(自动训练)。
// datasetId 参数化,通用库与数据源专属库共用。
const props = defineProps({
  datasetId: { type: [String, Number], default: '' },
  visible: { type: Boolean, default: false },
})
const emit = defineEmits(['update:visible', 'success'])
const { proxy } = getCurrentInstance()

const dialogVisible = computed({
  get: () => props.visible,
  set: (v) => emit('update:visible', v),
})

const uploadUrl = import.meta.env.VITE_APP_BASE_API + '/common/upload'
const uploadHeaders = { Authorization: 'Bearer ' + getToken() }

const docRef = ref()
const docForm = ref({})
const docRules = { name: [{ required: true, message: '文档名不能为空', trigger: 'blur' }] }
const docSubmitting = ref(false)
const uploading = ref(false)
const uploadPercent = ref(0)

// 打开时重置表单
watch(
  () => props.visible,
  (v) => {
    if (v) {
      docForm.value = {
        documentType: 'upload_file', strategy: 'recursive', contextual: false,
        chunkSize: 512, chunkOverlap: 100, name: '', uploadedName: '',
      }
      uploading.value = false
    }
  },
)

function onTypeChange() { docForm.value.fileKey = ''; docForm.value.uploadedName = ''; uploading.value = false }
function beforeUpload(file) {
  if (file.size > 50 * 1024 * 1024) { proxy.$modal.msgError('文件不能超过 50MB'); return false }
  uploading.value = true; uploadPercent.value = 0
  return true
}
function onProgress(evt) { uploadPercent.value = Math.round(evt.percent || 0) }
function onUploaded(res, file) {
  uploading.value = false
  if (res && res.code === 200) {
    docForm.value.fileKey = res.fileName || res.url
    docForm.value.uploadedName = res.originalFilename || res.newFileName || file?.name || '已上传'
    if (!docForm.value.name) docForm.value.name = docForm.value.uploadedName
    proxy.$modal.msgSuccess('上传成功')
  } else {
    proxy.$modal.msgError((res && res.msg) || '上传失败')
  }
}
function onUploadError() { uploading.value = false; proxy.$modal.msgError('上传失败,请检查文件类型或大小') }
function clearUpload() { docForm.value.fileKey = ''; docForm.value.uploadedName = '' }

function submitDoc() {
  docRef.value.validate((valid) => {
    if (!valid) return
    const f = docForm.value
    if (!props.datasetId) return proxy.$modal.msgError('知识库未就绪')
    if (f.documentType === 'upload_file' && !f.fileKey) return proxy.$modal.msgError('请先上传文件')
    if (f.documentType === 'text' && !f.text) return proxy.$modal.msgError('请填写文本内容')
    if (f.documentType === 'website' && !f.source) return proxy.$modal.msgError('请填写网页 URL')
    docSubmitting.value = true
    addDocument({
      datasetId: props.datasetId, name: f.name, documentType: f.documentType,
      fileKey: f.fileKey, source: f.source, text: f.text, autoTrain: true,
      chunkStrategy: { strategy: f.strategy, contextual: f.contextual, chunk_size: f.chunkSize, chunk_overlap: f.chunkOverlap },
    }).then(() => {
      proxy.$modal.msgSuccess('已创建,开始训练')
      dialogVisible.value = false
      emit('success')
    }).finally(() => (docSubmitting.value = false))
  })
}
</script>

<style scoped>
.up-tip { color: #909399; font-size: 12px; margin-top: 4px; }
.uploaded { display: flex; align-items: center; gap: 8px; margin-top: 8px; padding: 6px 10px; background: #f0f9eb; border-radius: 4px; font-size: 13px; }
.chunk-cfg { display: flex; align-items: center; gap: 8px; color: #606266; }
.chunk-cfg :deep(.el-input-number) { width: 120px; }
</style>
