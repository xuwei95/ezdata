<template>
  <div class="kb-tab">
    <div class="kb-head">
      <el-icon><Collection /></el-icon>
      <span class="kb-name">{{ datasetName || '该数据源专属知识库' }}</span>
      <el-text type="info" size="small">供数据分析使用的专属知识库</el-text>
      <div class="kb-head-r">
        <el-input v-model="query.keyword" placeholder="搜索内容/问题/答案" clearable size="small" style="width: 200px"
          @keyup.enter="reload" @clear="reload" />
        <el-select v-model="query.chunkType" placeholder="类型" clearable size="small" style="width: 100px" @change="reload">
          <el-option label="分段" value="chunk" />
          <el-option label="QA" value="qa" />
        </el-select>
        <el-button size="small" type="primary" icon="Search" @click="reload">查询</el-button>
      </div>
    </div>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5"><el-button type="primary" plain icon="Plus" :disabled="!datasetId" @click="add('chunk')" v-hasPermi="['rag:dataset:edit']">新增分段</el-button></el-col>
      <el-col :span="1.5"><el-button type="warning" plain icon="ChatLineSquare" :disabled="!datasetId" @click="add('qa')" v-hasPermi="['rag:dataset:edit']">新增 QA</el-button></el-col>
      <el-col :span="1.5"><el-button icon="Upload" :disabled="!datasetId" @click="importOpen = true" v-hasPermi="['rag:dataset:edit']">批量导入</el-button></el-col>
    </el-row>

    <el-table v-loading="loading" :data="rows" border>
      <el-table-column label="类型" width="80">
        <template #default="s"><el-tag size="small" :type="s.row.chunkType === 'qa' ? 'warning' : ''">{{ s.row.chunkType === 'qa' ? 'QA' : '分段' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="内容 / 问题" min-width="260">
        <template #default="s"><div class="cell-text">{{ s.row.chunkType === 'qa' ? s.row.question : s.row.content }}</div></template>
      </el-table-column>
      <el-table-column label="答案" min-width="200">
        <template #default="s"><div class="cell-text" v-if="s.row.chunkType === 'qa'">{{ s.row.answer }}</div></template>
      </el-table-column>
      <el-table-column label="标星" width="64" align="center">
        <template #default="s">
          <el-button link :icon="s.row.starFlag ? 'StarFilled' : 'Star'" :type="s.row.starFlag ? 'warning' : 'info'" @click="toggleStar(s.row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" width="130" fixed="right">
        <template #default="s">
          <el-button link type="primary" icon="Edit" @click="edit(s.row)" v-hasPermi="['rag:dataset:edit']">编辑</el-button>
          <el-button link type="danger" icon="Delete" @click="del(s.row)" v-hasPermi="['rag:dataset:edit']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <pagination v-show="total > 0" :total="total" v-model:page="query.pageNum" v-model:limit="query.pageSize" @pagination="getList" />

    <!-- 新增/编辑 -->
    <el-dialog :title="(form.id ? '编辑' : '新增') + (form.chunkType === 'qa' ? ' QA' : '分段')" v-model="open" width="560px" append-to-body>
      <el-form :model="form" label-width="60px">
        <template v-if="form.chunkType === 'qa'">
          <el-form-item label="问题"><el-input v-model="form.question" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="答案"><el-input v-model="form.answer" type="textarea" :rows="5" /></el-form-item>
        </template>
        <el-form-item v-else label="内容"><el-input v-model="form.content" type="textarea" :rows="6" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="open = false">取 消</el-button>
        <el-button type="primary" @click="submit">确 定</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入 -->
    <el-dialog title="批量导入" v-model="importOpen" width="560px" append-to-body>
      <p class="hint">CSV / Excel。QA:<b>question,answer</b> 两列;分段:<b>content</b> 列(无表头取第一列)。</p>
      <el-row :gutter="14">
        <el-col :span="12">
          <el-upload drag :action="uploadUrl" :headers="uploadHeaders" :show-file-list="false" :limit="1"
            :before-upload="beforeUpload" :on-success="(r) => onImport(r, 'qa')" :on-error="onErr">
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">QA 文件</div>
          </el-upload>
        </el-col>
        <el-col :span="12">
          <el-upload drag :action="uploadUrl" :headers="uploadHeaders" :show-file-list="false" :limit="1"
            :before-upload="beforeUpload" :on-success="(r) => onImport(r, 'chunk')" :on-error="onErr">
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">分段文件</div>
          </el-upload>
        </el-col>
      </el-row>
      <div v-if="importMsg" class="imp-status ok"><el-icon><CircleCheck /></el-icon> {{ importMsg }}</div>
    </el-dialog>
  </div>
</template>

<script setup name="KnowledgeBaseTab">
import { ref, reactive, watch, getCurrentInstance, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ensureSourceDataset, listChunk, saveChunk, delChunk, starChunk, bulkImportChunk } from '@/api/rag'
import { getToken } from '@/utils/auth'

const props = defineProps({ model: { type: Object, default: () => ({}) }, nodeType: { type: String, default: '' } })
const { proxy } = getCurrentInstance()
const uploadUrl = import.meta.env.VITE_APP_BASE_API + '/common/upload'
const uploadHeaders = { Authorization: 'Bearer ' + getToken() }

const datasetId = ref()
const datasetName = ref('')
const rows = ref([])
const total = ref(0)
const loading = ref(false)
const query = reactive({ pageNum: 1, pageSize: 10, chunkType: undefined, keyword: undefined })

// 当前数据源标识:源节点用 id,模型节点用其 datasourceCode
function sourceParams() {
  if (props.nodeType === 'source') return { sourceId: props.model?.id }
  return { sourceCode: props.model?.datasourceCode }
}
function sourceKey() {
  const p = sourceParams()
  return p.sourceId || p.sourceCode || ''
}

function resolveDataset() {
  const p = sourceParams()
  if (!p.sourceId && !p.sourceCode) { datasetId.value = null; rows.value = []; total.value = 0; return }
  ensureSourceDataset(p).then((res) => {
    datasetId.value = res.data?.id
    datasetName.value = res.data?.name || ''
    query.pageNum = 1
    getList()
  }).catch(() => { datasetId.value = null })
}
function reload() { query.pageNum = 1; getList() }
function getList() {
  if (!datasetId.value) return
  loading.value = true
  listChunk({ datasetId: datasetId.value, ...query }).then((res) => {
    rows.value = res.rows; total.value = res.total; loading.value = false
  }).catch(() => (loading.value = false))
}

// CRUD
const open = ref(false)
const form = ref({})
function add(type) { form.value = { chunkType: type, datasetId: datasetId.value }; open.value = true }
function edit(row) { form.value = { ...row, datasetId: datasetId.value }; open.value = true }
function submit() {
  const f = form.value
  if (f.chunkType === 'qa' && !(f.question && f.answer)) return ElMessage.error('请填写问题和答案')
  if (f.chunkType !== 'qa' && !f.content) return ElMessage.error('请填写内容')
  saveChunk(f).then(() => { ElMessage.success('保存成功'); open.value = false; getList() })
}
function del(row) {
  proxy.$modal.confirm('删除该知识段?').then(() => delChunk(row.id))
    .then(() => { getList(); ElMessage.success('删除成功') }).catch(() => {})
}
function toggleStar(row) { starChunk(row.id, row.starFlag ? 0 : 1).then(() => { row.starFlag = row.starFlag ? 0 : 1 }) }

// 批量导入
const importOpen = ref(false)
const importMsg = ref('')
function beforeUpload(file) {
  if (!/\.(csv|xlsx|xls|tsv)$/i.test(file.name)) { ElMessage.error('仅支持 CSV / Excel'); return false }
  return true
}
function onImport(res, type) {
  if (!(res && res.code === 200)) return ElMessage.error((res && res.msg) || '上传失败')
  bulkImportChunk({ datasetId: datasetId.value, chunkType: type, fileKey: res.fileName }).then((r) => {
    const d = r.data || {}
    if (d.error) { ElMessage.error(d.error); return }
    importMsg.value = `成功导入 ${d.imported || 0} 条` + (d.note ? `(${d.note})` : '')
    ElMessage.success(importMsg.value); getList()
  }).catch(() => ElMessage.error('导入失败'))
}
function onErr() { ElMessage.error('上传失败') }

watch(sourceKey, resolveDataset)
onMounted(resolveDataset)
</script>

<style scoped>
.kb-head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.kb-head .kb-name { font-size: 15px; font-weight: 600; color: #303133; }
.kb-head-r { margin-left: auto; display: flex; gap: 8px; }
.cell-text { white-space: pre-wrap; line-height: 1.5; max-height: 66px; overflow: hidden; }
.hint { color: #909399; font-size: 12px; margin: 0 0 10px; }
.imp-status { margin-top: 12px; font-size: 13px; display: flex; align-items: center; gap: 6px; }
.imp-status.ok { color: #67c23a; }
</style>
