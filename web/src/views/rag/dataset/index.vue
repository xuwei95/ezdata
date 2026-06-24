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

    <!-- 新增文档(抽出的可复用组件) -->
    <DocumentImportDialog :dataset-id="curDataset.id" v-model:visible="docOpen" @success="getDocs" />

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
import DocumentImportDialog from '@/views/rag/components/DocumentImportDialog.vue'

const { proxy } = getCurrentInstance()
const STATUS_TEXT = { 1: '待训练', 2: '训练中', 3: '成功', 4: '失败' }
const STATUS_TAG = { 1: 'info', 2: 'warning', 3: 'success', 4: 'danger' }
const TYPE_TEXT = { upload_file: '文件', text: '文本', website: '网页', datamodel: '数据模型' }

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

// 新增文档逻辑已抽到 DocumentImportDialog 组件;此处仅控制打开
const docOpen = ref(false)
function handleAddDoc() { docOpen.value = true }
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
