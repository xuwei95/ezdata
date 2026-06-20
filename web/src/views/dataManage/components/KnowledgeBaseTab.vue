<template>
  <div class="kb-tab">
    <el-alert type="info" :closable="false" show-icon
      title="选择目标知识库,批量导入 QA 问答对或文本分段(CSV/Excel)。完整管理请前往「知识库」菜单。" style="margin-bottom: 14px" />

    <el-form :inline="true" style="margin-bottom: 8px">
      <el-form-item label="目标知识库">
        <el-select v-model="datasetId" filterable placeholder="选择知识库" style="width: 280px">
          <el-option v-for="d in datasets" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button icon="Refresh" @click="loadDatasets">刷新</el-button>
        <el-button type="primary" link icon="TopRight" @click="goManage">知识库管理</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card shadow="never" class="imp-card">
          <template #header><el-icon><ChatLineSquare /></el-icon> 导入 QA 问答对</template>
          <p class="hint">CSV / Excel,两列:<b>question</b>(问题)、<b>answer</b>(答案),首行表头。</p>
          <el-upload drag :action="uploadUrl" :headers="uploadHeaders" :show-file-list="false" :limit="1"
            :disabled="!datasetId || qaLoading" :before-upload="beforeUpload"
            :on-success="(r) => onImport(r, 'qa')" :on-error="onErr">
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽或<em>点击上传</em> QA 文件</div>
          </el-upload>
          <div v-if="qaLoading" class="imp-status"><el-icon class="is-loading"><Loading /></el-icon> 导入中...</div>
          <div v-else-if="qaResult" class="imp-status ok"><el-icon><CircleCheck /></el-icon> {{ qaResult }}</div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="never" class="imp-card">
          <template #header><el-icon><Tickets /></el-icon> 导入文本分段</template>
          <p class="hint">CSV / Excel,一列:<b>content</b>(内容);无表头时取第一列。每行一条分段。</p>
          <el-upload drag :action="uploadUrl" :headers="uploadHeaders" :show-file-list="false" :limit="1"
            :disabled="!datasetId || chLoading" :before-upload="beforeUpload"
            :on-success="(r) => onImport(r, 'chunk')" :on-error="onErr">
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽或<em>点击上传</em> 分段文件</div>
          </el-upload>
          <div v-if="chLoading" class="imp-status"><el-icon class="is-loading"><Loading /></el-icon> 导入中...</div>
          <div v-else-if="chResult" class="imp-status ok"><el-icon><CircleCheck /></el-icon> {{ chResult }}</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="KnowledgeBaseTab">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { listDataset, bulkImportChunk } from '@/api/rag'
import { getToken } from '@/utils/auth'

const router = useRouter()
const uploadUrl = import.meta.env.VITE_APP_BASE_API + '/common/upload'
const uploadHeaders = { Authorization: 'Bearer ' + getToken() }

const datasets = ref([])
const datasetId = ref()
const qaLoading = ref(false)
const chLoading = ref(false)
const qaResult = ref('')
const chResult = ref('')

function loadDatasets() {
  listDataset({ pageNum: 1, pageSize: 100 }).then((res) => { datasets.value = res.rows || [] })
}
function goManage() { router.push('/rag/dataset') }
function beforeUpload(file) {
  if (!datasetId.value) { ElMessage.error('请先选择目标知识库'); return false }
  const ok = /\.(csv|xlsx|xls|tsv)$/i.test(file.name)
  if (!ok) { ElMessage.error('仅支持 CSV / Excel'); return false }
  return true
}
function onImport(res, type) {
  const loading = type === 'qa' ? qaLoading : chLoading
  const result = type === 'qa' ? qaResult : chResult
  if (!(res && res.code === 200)) { ElMessage.error((res && res.msg) || '上传失败'); return }
  loading.value = true; result.value = ''
  bulkImportChunk({ datasetId: datasetId.value, chunkType: type, fileKey: res.fileName })
    .then((r) => {
      const d = r.data || {}
      if (d.error) { ElMessage.error(d.error); result.value = '失败:' + d.error }
      else { result.value = `成功导入 ${d.imported || 0} 条` + (d.note ? `(${d.note})` : ''); ElMessage.success(result.value) }
    })
    .catch(() => ElMessage.error('导入失败'))
    .finally(() => (loading.value = false))
}
function onErr() { ElMessage.error('上传失败,请检查文件类型或大小') }

onMounted(loadDatasets)
</script>

<style scoped>
.hint { color: #909399; font-size: 12px; margin: 0 0 10px; }
.imp-card { min-height: 230px; }
.imp-status { margin-top: 10px; font-size: 13px; color: #606266; display: flex; align-items: center; gap: 6px; }
.imp-status.ok { color: #67c23a; }
</style>
