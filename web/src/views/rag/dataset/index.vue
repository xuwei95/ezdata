<template>
  <div class="app-container">
    <!-- 查询 -->
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="名称" prop="name">
        <el-input v-model="queryParams.name" placeholder="知识库名称" clearable style="width: 220px"
          @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['rag:dataset:edit']">新建知识库</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <!-- 知识库列表 -->
    <el-table v-loading="loading" :data="list">
      <el-table-column label="名称" prop="name" min-width="160" show-overflow-tooltip />
      <el-table-column label="描述" prop="remark" min-width="180" show-overflow-tooltip />
      <el-table-column label="Embedding" min-width="170">
        <template #default="s">
          <span v-if="s.row.embeddingModel">{{ s.row.embeddingModel }}<el-text type="info" size="small" v-if="s.row.embeddingDims"> · {{ s.row.embeddingDims }}维</el-text></span>
          <el-text v-else type="info" size="small">未训练</el-text>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="s">
          <el-tag :type="s.row.status === 1 ? 'success' : 'info'">{{ s.row.status === 1 ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="createTime" width="160" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="s">
          <el-button link type="primary" icon="FolderOpened" @click="openDocs(s.row)" v-hasPermi="['rag:dataset:list']">文档管理</el-button>
          <el-button link type="primary" icon="Edit" @click="handleUpdate(s.row)" v-hasPermi="['rag:dataset:edit']">编辑</el-button>
          <el-button link type="danger" icon="Delete" @click="handleDelete(s.row)" v-hasPermi="['rag:dataset:edit']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize"
      @pagination="getList" />

    <!-- 新建/编辑知识库 -->
    <el-dialog :title="title" v-model="open" width="520px" append-to-body>
      <el-form ref="dsRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="知识库名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="描述(可选)" />
        </el-form-item>
        <el-form-item v-if="form.id" label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-alert v-else type="info" :closable="false" show-icon
          title="Embedding 模型与向量后端使用系统默认(环境变量),建库后向量维度固定。" style="margin-bottom: 4px" />
      </el-form>
      <template #footer>
        <el-button type="primary" @click="submitForm">确 定</el-button>
        <el-button @click="open = false">取 消</el-button>
      </template>
    </el-dialog>

    <!-- 文档管理:全屏 -->
    <el-dialog v-model="docDrawer" fullscreen append-to-body class="rag-fullscreen" :show-close="true">
      <template #header>
        <div class="fs-header">
          <el-icon><Collection /></el-icon>
          <span class="fs-title">{{ curDataset.name }}</span>
          <el-tag round size="small" type="info">{{ docs.length }} 个文档</el-tag>
          <el-text v-if="curDataset.embeddingModel" type="info" size="small">{{ curDataset.embeddingModel }}</el-text>
        </div>
      </template>

      <div class="fs-body">
        <el-row :gutter="10" class="mb8">
          <el-col :span="1.5"><el-button type="primary" icon="Plus" @click="handleAddDoc" v-hasPermi="['rag:dataset:edit']">新增文档</el-button></el-col>
          <el-col :span="1.5"><el-button icon="Refresh" @click="getDocs">刷新</el-button></el-col>
        </el-row>
        <el-table v-loading="docLoading" :data="docs" height="calc(100vh - 190px)">
          <el-table-column label="文档名" prop="name" min-width="220" show-overflow-tooltip />
          <el-table-column label="类型" width="110">
            <template #default="s"><el-tag size="small" effect="plain">{{ TYPE_TEXT[s.row.documentType] || s.row.documentType }}</el-tag></template>
          </el-table-column>
          <el-table-column label="状态" width="120">
            <template #default="s">
              <el-tag :type="STATUS_TAG[s.row.status]" effect="light">
                <el-icon v-if="s.row.status === 2" class="is-loading"><Loading /></el-icon>
                {{ STATUS_TEXT[s.row.status] }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="分段数" prop="chunkCount" width="90" align="center" />
          <el-table-column label="错误" prop="error" min-width="180" show-overflow-tooltip>
            <template #default="s"><el-text v-if="s.row.error" type="danger" size="small">{{ s.row.error }}</el-text></template>
          </el-table-column>
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="s">
              <el-button link type="primary" icon="VideoPlay" :disabled="s.row.status === 2" @click="doTrain(s.row)" v-hasPermi="['rag:dataset:edit']">{{ s.row.status === 3 ? '重训' : '训练' }}</el-button>
              <el-button link type="primary" icon="Files" @click="openChunks(s.row)">分段({{ s.row.chunkCount || 0 }})</el-button>
              <el-button link type="danger" icon="Delete" @click="delDoc(s.row)" v-hasPermi="['rag:dataset:edit']">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <!-- 新增文档:优化后的 UI -->
    <el-dialog title="新增文档" v-model="docOpen" width="620px" append-to-body :close-on-click-modal="false">
      <el-form ref="docRef" :model="docForm" :rules="docRules" label-position="top">
        <el-form-item label="来源类型">
          <el-radio-group v-model="docForm.documentType" @change="onTypeChange">
            <el-radio-button value="upload_file"><el-icon><Upload /></el-icon> 上传文件</el-radio-button>
            <el-radio-button value="text"><el-icon><Document /></el-icon> 粘贴文本</el-radio-button>
            <el-radio-button value="website"><el-icon><Link /></el-icon> 网页</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 文件:拖拽上传 -->
        <el-form-item v-if="docForm.documentType === 'upload_file'" label="文件">
          <el-upload drag :action="uploadUrl" :headers="uploadHeaders" :limit="1" :show-file-list="false"
            :before-upload="beforeUpload" :on-progress="onProgress" :on-success="onUploaded"
            :on-error="onUploadError" style="width: 100%">
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽文件到此处,或<em>点击上传</em></div>
            <template #tip><div class="up-tip">支持 txt / md / pdf / csv / xlsx / docx / html / json,单文件 ≤ 50MB</div></template>
          </el-upload>
          <el-progress v-if="uploading" :percentage="uploadPercent" :stroke-width="6" status="success" style="margin-top: 8px" />
          <div v-else-if="docForm.uploadedName" class="uploaded">
            <el-icon color="#67c23a"><CircleCheck /></el-icon>
            <span>{{ docForm.uploadedName }}</span>
            <el-button link type="danger" icon="Close" @click="clearUpload">移除</el-button>
          </div>
        </el-form-item>

        <!-- 文本 -->
        <el-form-item v-if="docForm.documentType === 'text'" label="文本内容">
          <el-input v-model="docForm.text" type="textarea" :rows="8" placeholder="粘贴要入库的文本内容" />
        </el-form-item>

        <!-- 网页 -->
        <el-form-item v-if="docForm.documentType === 'website'" label="网页 URL">
          <el-input v-model="docForm.source" placeholder="https://example.com/article">
            <template #prepend><el-icon><Link /></el-icon></template>
          </el-input>
        </el-form-item>

        <el-form-item label="文档名" prop="name">
          <el-input v-model="docForm.name" placeholder="文档名(上传文件会自动填充)" />
        </el-form-item>

        <el-form-item label="切分策略">
          <el-select v-model="docForm.strategy" style="width: 200px">
            <el-option label="递归(默认)" value="recursive" />
            <el-option label="固定大小" value="fixed" />
            <el-option label="按文档段落" value="document" />
            <el-option label="按 Markdown 标题" value="markdown" />
            <el-option label="语义切分(更准)" value="semantic" />
          </el-select>
          <el-tooltip content="语义切分按内容语义边界分块,召回更准,但训练时会多调用 embedding" placement="top">
            <el-icon style="margin-left:6px;color:#909399"><QuestionFilled /></el-icon>
          </el-tooltip>
        </el-form-item>
        <el-form-item label="切分设置">
          <div class="chunk-cfg">
            <span>每段</span>
            <el-input-number v-model="docForm.chunkSize" :min="128" :max="4000" :step="64" controls-position="right" />
            <span>字符,重叠</span>
            <el-input-number v-model="docForm.chunkOverlap" :min="0" :max="1000" :step="20" controls-position="right" />
            <span>字符</span>
          </div>
        </el-form-item>
        <el-form-item label="上下文增强">
          <el-switch v-model="docForm.contextual" />
          <span class="up-tip" style="margin-left:8px">为每段附 LLM 生成的上下文背景(Contextual Retrieval),召回更准但训练更慢</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="docOpen = false">取 消</el-button>
        <el-button type="primary" :loading="docSubmitting" @click="submitDoc">创建并训练</el-button>
      </template>
    </el-dialog>

    <!-- 分段抽屉 -->
    <el-drawer v-model="chunkDrawer" :title="`分段 - ${curDoc.name || ''}`" size="58%" append-to-body>
      <el-row :gutter="10" class="mb8">
        <el-col :span="1.5"><el-button type="primary" plain icon="Plus" @click="handleAddQa" v-hasPermi="['rag:dataset:edit']">新增 QA</el-button></el-col>
        <el-col :span="1.5"><el-button icon="Refresh" @click="getChunks">刷新</el-button></el-col>
      </el-row>
      <el-table v-loading="chunkLoading" :data="chunks">
        <el-table-column label="#" prop="position" width="56" />
        <el-table-column label="类型" width="76">
          <template #default="s"><el-tag size="small" :type="s.row.chunkType === 'qa' ? 'warning' : ''">{{ s.row.chunkType }}</el-tag></template>
        </el-table-column>
        <el-table-column label="内容/问题" min-width="300">
          <template #default="s"><div class="chunk-content">{{ s.row.chunkType === 'qa' ? s.row.question : s.row.content }}</div></template>
        </el-table-column>
        <el-table-column label="标星" width="64">
          <template #default="s">
            <el-button link :icon="s.row.starFlag ? 'StarFilled' : 'Star'" :type="s.row.starFlag ? 'warning' : 'info'" @click="toggleStar(s.row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="130" fixed="right">
          <template #default="s">
            <el-button link type="primary" icon="Edit" @click="editChunk(s.row)" v-hasPermi="['rag:dataset:edit']">编辑</el-button>
            <el-button link type="danger" icon="Delete" @click="delC(s.row)" v-hasPermi="['rag:dataset:edit']">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <pagination v-show="chunkTotal > 0" :total="chunkTotal" v-model:page="chunkQuery.pageNum"
        v-model:limit="chunkQuery.pageSize" @pagination="getChunks" />
    </el-drawer>

    <!-- 分段/QA 编辑 -->
    <el-dialog :title="chunkForm.chunkType === 'qa' ? 'QA 问答对' : '分段'" v-model="chunkOpen" width="560px" append-to-body>
      <el-form ref="cRef" :model="chunkForm" label-width="60px">
        <template v-if="chunkForm.chunkType === 'qa'">
          <el-form-item label="问题"><el-input v-model="chunkForm.question" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="答案"><el-input v-model="chunkForm.answer" type="textarea" :rows="4" /></el-form-item>
        </template>
        <el-form-item v-else label="内容"><el-input v-model="chunkForm.content" type="textarea" :rows="6" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="chunkOpen = false">取 消</el-button>
        <el-button type="primary" @click="submitChunk">确 定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="RagDataset">
import {
  listDataset, addDataset, updateDataset, delDataset,
  listDocument, addDocument, delDocument, trainDocument, documentStatus,
  listChunk, saveChunk, delChunk, starChunk,
} from '@/api/rag'
import { getToken } from '@/utils/auth'

const { proxy } = getCurrentInstance()
const STATUS_TEXT = { 1: '待训练', 2: '训练中', 3: '成功', 4: '失败' }
const STATUS_TAG = { 1: 'info', 2: 'warning', 3: 'success', 4: 'danger' }
const TYPE_TEXT = { upload_file: '文件', text: '文本', website: '网页', datamodel: '数据模型' }

const uploadUrl = import.meta.env.VITE_APP_BASE_API + '/common/upload'
const uploadHeaders = { Authorization: 'Bearer ' + getToken() }

const loading = ref(false)
const showSearch = ref(true)
const list = ref([])
const total = ref(0)
const queryParams = reactive({ pageNum: 1, pageSize: 10, name: undefined })

// 知识库表单
const open = ref(false)
const title = ref('')
const form = ref({})
const rules = { name: [{ required: true, message: '名称不能为空', trigger: 'blur' }] }

function getList() {
  loading.value = true
  listDataset(queryParams).then((res) => {
    list.value = res.rows; total.value = res.total; loading.value = false
  }).catch(() => (loading.value = false))
}
function handleQuery() { queryParams.pageNum = 1; getList() }
function resetQuery() { proxy.resetForm('queryRef'); handleQuery() }
function handleAdd() { form.value = { status: 1 }; title.value = '新建知识库'; open.value = true }
function handleUpdate(row) {
  form.value = { id: row.id, name: row.name, description: row.remark, status: row.status, remark: row.remark }
  title.value = '编辑知识库'; open.value = true
}
function submitForm() {
  proxy.$refs.dsRef.validate((valid) => {
    if (!valid) return
    const p = form.value.id ? updateDataset(form.value.id, form.value) : addDataset(form.value)
    p.then(() => { proxy.$modal.msgSuccess('保存成功'); open.value = false; getList() })
  })
}
function handleDelete(row) {
  proxy.$modal.confirm(`确认删除知识库「${row.name}」及其文档/分段?`).then(() => delDataset(row.id))
    .then(() => { getList(); proxy.$modal.msgSuccess('删除成功') }).catch(() => {})
}

// ---------------- 文档(全屏) ----------------
const docDrawer = ref(false)
const docLoading = ref(false)
const docs = ref([])
const curDataset = ref({})
let pollTimer = null

function openDocs(row) { curDataset.value = row; docDrawer.value = true; getDocs() }
function getDocs() {
  docLoading.value = true
  listDocument({ datasetId: curDataset.value.id, pageNum: 1, pageSize: 200 }).then((res) => {
    docs.value = res.rows; docLoading.value = false; schedulePoll()
  }).catch(() => (docLoading.value = false))
}
function schedulePoll() {
  if (pollTimer) clearTimeout(pollTimer)
  if (docs.value.some((d) => d.status === 2)) {
    pollTimer = setTimeout(async () => {
      for (const d of docs.value.filter((x) => x.status === 2)) {
        try {
          const r = await documentStatus(d.id)
          Object.assign(d, { status: r.data.status, chunkCount: r.data.chunkCount, error: r.data.error })
        } catch (e) { /* ignore */ }
      }
      schedulePoll()
    }, 2000)
  }
}

const docOpen = ref(false)
const docSubmitting = ref(false)
const docForm = ref({})
const docRules = { name: [{ required: true, message: '文档名不能为空', trigger: 'blur' }] }
function handleAddDoc() {
  docForm.value = { documentType: 'upload_file', strategy: 'recursive', contextual: false, chunkSize: 512, chunkOverlap: 100, name: '', uploadedName: '' }
  docOpen.value = true
}
const uploading = ref(false)
const uploadPercent = ref(0)
function onTypeChange() { docForm.value.fileKey = ''; docForm.value.uploadedName = ''; uploading.value = false }
function beforeUpload(file) {
  if (file.size > 50 * 1024 * 1024) { proxy.$modal.msgError('文件不能超过 50MB'); return false }
  uploading.value = true; uploadPercent.value = 0
  return true
}
function onProgress(evt) { uploadPercent.value = Math.round(evt.percent || 0) }
function onUploaded(res, file) {
  // ResponseUtil 把字段铺在顶层:{code, msg, fileName, originalFilename, url}
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
  proxy.$refs.docRef.validate((valid) => {
    if (!valid) return
    const f = docForm.value
    if (f.documentType === 'upload_file' && !f.fileKey) return proxy.$modal.msgError('请先上传文件')
    if (f.documentType === 'text' && !f.text) return proxy.$modal.msgError('请填写文本内容')
    if (f.documentType === 'website' && !f.source) return proxy.$modal.msgError('请填写网页 URL')
    docSubmitting.value = true
    addDocument({
      datasetId: curDataset.value.id, name: f.name, documentType: f.documentType,
      fileKey: f.fileKey, source: f.source, text: f.text, autoTrain: true,
      chunkStrategy: { strategy: f.strategy, contextual: f.contextual, chunk_size: f.chunkSize, chunk_overlap: f.chunkOverlap },
    }).then(() => {
      proxy.$modal.msgSuccess('已创建,开始训练'); docOpen.value = false; getDocs()
    }).finally(() => (docSubmitting.value = false))
  })
}
function doTrain(row) { trainDocument(row.id).then(() => { proxy.$modal.msgSuccess('已开始训练'); getDocs() }) }
function delDoc(row) {
  proxy.$modal.confirm(`删除文档「${row.name}」?`).then(() => delDocument(row.id))
    .then(() => { getDocs(); proxy.$modal.msgSuccess('删除成功') }).catch(() => {})
}

// ---------------- 分段 ----------------
const chunkDrawer = ref(false)
const chunkLoading = ref(false)
const chunks = ref([])
const chunkTotal = ref(0)
const curDoc = ref({})
const chunkQuery = reactive({ pageNum: 1, pageSize: 10 })

function openChunks(row) { curDoc.value = row; chunkDrawer.value = true; chunkQuery.pageNum = 1; getChunks() }
function getChunks() {
  chunkLoading.value = true
  listChunk({ datasetId: curDataset.value.id, documentId: curDoc.value.id, ...chunkQuery }).then((res) => {
    chunks.value = res.rows; chunkTotal.value = res.total; chunkLoading.value = false
  }).catch(() => (chunkLoading.value = false))
}
const chunkOpen = ref(false)
const chunkForm = ref({})
function handleAddQa() { chunkForm.value = { chunkType: 'qa', datasetId: curDataset.value.id, documentId: curDoc.value.id }; chunkOpen.value = true }
function editChunk(row) { chunkForm.value = { ...row, datasetId: curDataset.value.id }; chunkOpen.value = true }
function submitChunk() {
  saveChunk(chunkForm.value).then(() => { proxy.$modal.msgSuccess('保存成功'); chunkOpen.value = false; getChunks(); getDocs() })
}
function delC(row) {
  proxy.$modal.confirm('删除该分段?').then(() => delChunk(row.id))
    .then(() => { getChunks(); proxy.$modal.msgSuccess('删除成功') }).catch(() => {})
}
function toggleStar(row) {
  starChunk(row.id, row.starFlag ? 0 : 1).then(() => { row.starFlag = row.starFlag ? 0 : 1 })
}

onMounted(getList)
onUnmounted(() => { if (pollTimer) clearTimeout(pollTimer) })
</script>

<style scoped>
.fs-header { display: flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 600; }
.fs-header .fs-title { color: #303133; }
.fs-body { padding: 0 4px; }
.up-tip { color: #909399; font-size: 12px; margin-top: 4px; }
.uploaded { display: flex; align-items: center; gap: 8px; margin-top: 8px; padding: 6px 10px; background: #f0f9eb; border-radius: 4px; font-size: 13px; }
.chunk-cfg { display: flex; align-items: center; gap: 8px; color: #606266; }
.chunk-cfg :deep(.el-input-number) { width: 120px; }
.chunk-content { white-space: pre-wrap; line-height: 1.5; max-height: 80px; overflow: hidden; }
</style>
