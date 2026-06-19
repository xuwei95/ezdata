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

    <!-- 列表 -->
    <el-table v-loading="loading" :data="list">
      <el-table-column label="名称" prop="name" min-width="160" show-overflow-tooltip />
      <el-table-column label="描述" prop="remark" min-width="160" show-overflow-tooltip />
      <el-table-column label="Embedding" min-width="160">
        <template #default="s">{{ s.row.embeddingProvider }} / {{ s.row.embeddingModel }}</template>
      </el-table-column>
      <el-table-column label="维度" prop="embeddingDims" width="80" />
      <el-table-column label="向量后端" prop="vectorBackend" width="120" />
      <el-table-column label="状态" width="90">
        <template #default="s">
          <el-tag :type="s.row.status === 1 ? 'success' : 'info'">{{ s.row.status === 1 ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" prop="createTime" width="160" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="s">
          <el-button link type="primary" icon="Document" @click="openDocs(s.row)" v-hasPermi="['rag:dataset:list']">文档</el-button>
          <el-button link type="primary" icon="Edit" @click="handleUpdate(s.row)" v-hasPermi="['rag:dataset:edit']">编辑</el-button>
          <el-button link type="danger" icon="Delete" @click="handleDelete(s.row)" v-hasPermi="['rag:dataset:edit']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize"
      @pagination="getList" />

    <!-- 新建/编辑知识库 -->
    <el-dialog :title="title" v-model="open" width="560px" append-to-body>
      <el-form ref="dsRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="知识库名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="描述(可选)" />
        </el-form-item>
        <template v-if="!form.id">
          <el-form-item label="Embedding">
            <el-input v-model="form.embeddingModel" placeholder="留空=用系统默认(env)" />
            <div class="tip">维度由该模型决定,建库后不可更换 embedding。</div>
          </el-form-item>
          <el-form-item label="向量后端">
            <el-select v-model="form.vectorBackend" style="width: 100%">
              <el-option v-for="b in backends" :key="b" :label="b" :value="b" />
            </el-select>
          </el-form-item>
        </template>
        <el-form-item v-else label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="submitForm">确 定</el-button>
        <el-button @click="open = false">取 消</el-button>
      </template>
    </el-dialog>

    <!-- 文档管理抽屉 -->
    <el-drawer v-model="docDrawer" :title="`文档管理 - ${curDataset.name || ''}`" size="72%" append-to-body>
      <el-row :gutter="10" class="mb8">
        <el-col :span="1.5"><el-button type="primary" plain icon="Plus" @click="handleAddDoc" v-hasPermi="['rag:dataset:edit']">新增文档</el-button></el-col>
        <el-col :span="1.5"><el-button icon="Refresh" @click="getDocs">刷新</el-button></el-col>
      </el-row>
      <el-table v-loading="docLoading" :data="docs">
        <el-table-column label="文档名" prop="name" min-width="180" show-overflow-tooltip />
        <el-table-column label="类型" prop="documentType" width="110" />
        <el-table-column label="状态" width="100">
          <template #default="s">
            <el-tag :type="STATUS_TAG[s.row.status]">{{ STATUS_TEXT[s.row.status] }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="分段数" prop="chunkCount" width="80" />
        <el-table-column label="错误" prop="error" min-width="160" show-overflow-tooltip />
        <el-table-column label="操作" width="240" fixed="right">
          <template #default="s">
            <el-button link type="primary" icon="VideoPlay" @click="doTrain(s.row)" v-hasPermi="['rag:dataset:edit']">训练</el-button>
            <el-button link type="primary" icon="Files" @click="openChunks(s.row)">分段</el-button>
            <el-button link type="danger" icon="Delete" @click="delDoc(s.row)" v-hasPermi="['rag:dataset:edit']">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <!-- 新增文档 -->
    <el-dialog title="新增文档" v-model="docOpen" width="560px" append-to-body>
      <el-form ref="docRef" :model="docForm" :rules="docRules" label-width="90px">
        <el-form-item label="类型" prop="documentType">
          <el-radio-group v-model="docForm.documentType">
            <el-radio value="upload_file">文件</el-radio>
            <el-radio value="text">文本</el-radio>
            <el-radio value="website">网页</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="docForm.name" placeholder="文档名" />
        </el-form-item>
        <el-form-item v-if="docForm.documentType === 'upload_file'" label="文件">
          <el-upload :action="uploadUrl" :headers="uploadHeaders" :limit="1" :on-success="onUploaded"
            :on-remove="() => (docForm.fileKey = '')">
            <el-button type="primary" icon="Upload">选择文件</el-button>
            <template #tip><div class="tip">支持 txt/md/pdf/csv/xlsx/html/docx/json</div></template>
          </el-upload>
        </el-form-item>
        <el-form-item v-if="docForm.documentType === 'text'" label="文本">
          <el-input v-model="docForm.text" type="textarea" :rows="6" placeholder="粘贴文本内容" />
        </el-form-item>
        <el-form-item v-if="docForm.documentType === 'website'" label="URL">
          <el-input v-model="docForm.source" placeholder="https://..." />
        </el-form-item>
        <el-form-item label="切分">
          <el-input-number v-model="docForm.chunkSize" :min="128" :max="4000" :step="128" /> 字
          <span style="margin: 0 6px">重叠</span>
          <el-input-number v-model="docForm.chunkOverlap" :min="0" :max="1000" :step="50" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="submitDoc">确 定(并训练)</el-button>
        <el-button @click="docOpen = false">取 消</el-button>
      </template>
    </el-dialog>

    <!-- 分段抽屉 -->
    <el-drawer v-model="chunkDrawer" :title="`分段 - ${curDoc.name || ''}`" size="60%" append-to-body>
      <el-row :gutter="10" class="mb8">
        <el-col :span="1.5"><el-button type="primary" plain icon="Plus" @click="handleAddQa" v-hasPermi="['rag:dataset:edit']">新增 QA</el-button></el-col>
        <el-col :span="1.5"><el-button icon="Refresh" @click="getChunks">刷新</el-button></el-col>
      </el-row>
      <el-table v-loading="chunkLoading" :data="chunks">
        <el-table-column label="#" prop="position" width="60" />
        <el-table-column label="类型" prop="chunkType" width="80" />
        <el-table-column label="内容/问题" min-width="280">
          <template #default="s">{{ s.row.chunkType === 'qa' ? s.row.question : s.row.content }}</template>
        </el-table-column>
        <el-table-column label="标星" width="70">
          <template #default="s">
            <el-button link :icon="s.row.starFlag ? 'StarFilled' : 'Star'" :type="s.row.starFlag ? 'warning' : 'info'"
              @click="toggleStar(s.row)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
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
      <el-form ref="cRef" :model="chunkForm" label-width="70px">
        <template v-if="chunkForm.chunkType === 'qa'">
          <el-form-item label="问题"><el-input v-model="chunkForm.question" type="textarea" :rows="2" /></el-form-item>
          <el-form-item label="答案"><el-input v-model="chunkForm.answer" type="textarea" :rows="4" /></el-form-item>
        </template>
        <el-form-item v-else label="内容"><el-input v-model="chunkForm.content" type="textarea" :rows="6" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="submitChunk">确 定</el-button>
        <el-button @click="chunkOpen = false">取 消</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="RagDataset">
import {
  listDataset, addDataset, updateDataset, delDataset, vectorBackends,
  listDocument, addDocument, delDocument, trainDocument, documentStatus,
  listChunk, saveChunk, delChunk, starChunk,
} from '@/api/rag'
import { getToken } from '@/utils/auth'

const { proxy } = getCurrentInstance()
const STATUS_TEXT = { 1: '待训练', 2: '训练中', 3: '成功', 4: '失败' }
const STATUS_TAG = { 1: 'info', 2: 'warning', 3: 'success', 4: 'danger' }

const uploadUrl = import.meta.env.VITE_APP_BASE_API + '/common/upload'
const uploadHeaders = { Authorization: 'Bearer ' + getToken() }

const loading = ref(false)
const showSearch = ref(true)
const list = ref([])
const total = ref(0)
const backends = ref(['elasticsearch'])
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
function handleAdd() {
  form.value = { vectorBackend: 'elasticsearch', status: 1 }
  title.value = '新建知识库'; open.value = true
}
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

// ---------------- 文档 ----------------
const docDrawer = ref(false)
const docLoading = ref(false)
const docs = ref([])
const curDataset = ref({})
let pollTimer = null

function openDocs(row) { curDataset.value = row; docDrawer.value = true; getDocs() }
function getDocs() {
  docLoading.value = true
  listDocument({ datasetId: curDataset.value.id, pageNum: 1, pageSize: 100 }).then((res) => {
    docs.value = res.rows; docLoading.value = false; schedulePoll()
  }).catch(() => (docLoading.value = false))
}
function schedulePoll() {
  if (pollTimer) clearTimeout(pollTimer)
  if (docs.value.some((d) => d.status === 2)) {
    pollTimer = setTimeout(async () => {
      for (const d of docs.value.filter((x) => x.status === 2)) {
        const r = await documentStatus(d.id); Object.assign(d, { status: r.data.status, chunkCount: r.data.chunkCount, error: r.data.error })
      }
      schedulePoll()
    }, 2000)
  }
}

const docOpen = ref(false)
const docForm = ref({})
const docRules = { name: [{ required: true, message: '名称不能为空', trigger: 'blur' }] }
function handleAddDoc() {
  docForm.value = { documentType: 'upload_file', chunkSize: 512, chunkOverlap: 100, name: '' }
  docOpen.value = true
}
function onUploaded(res) {
  docForm.value.fileKey = res.fileName
  if (!docForm.value.name) docForm.value.name = res.originalFilename || res.newFileName
}
function submitDoc() {
  proxy.$refs.docRef.validate((valid) => {
    if (!valid) return
    const f = docForm.value
    if (f.documentType === 'upload_file' && !f.fileKey) return proxy.$modal.msgError('请先上传文件')
    if (f.documentType === 'text' && !f.text) return proxy.$modal.msgError('请填写文本')
    if (f.documentType === 'website' && !f.source) return proxy.$modal.msgError('请填写 URL')
    addDocument({
      datasetId: curDataset.value.id, name: f.name, documentType: f.documentType,
      fileKey: f.fileKey, source: f.source, text: f.text, autoTrain: true,
      chunkStrategy: { chunk_size: f.chunkSize, chunk_overlap: f.chunkOverlap },
    }).then(() => { proxy.$modal.msgSuccess('已创建,开始训练'); docOpen.value = false; getDocs() })
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
  saveChunk(chunkForm.value).then(() => { proxy.$modal.msgSuccess('保存成功'); chunkOpen.value = false; getChunks() })
}
function delC(row) {
  proxy.$modal.confirm('删除该分段?').then(() => delChunk(row.id))
    .then(() => { getChunks(); proxy.$modal.msgSuccess('删除成功') }).catch(() => {})
}
function toggleStar(row) {
  starChunk(row.id, row.starFlag ? 0 : 1).then(() => { row.starFlag = row.starFlag ? 0 : 1 })
}

onMounted(() => {
  getList()
  vectorBackends().then((res) => { backends.value = res.data || ['elasticsearch'] }).catch(() => {})
})
onUnmounted(() => { if (pollTimer) clearTimeout(pollTimer) })
</script>

<style scoped>
.tip { color: #909399; font-size: 12px; line-height: 1.4; }
</style>
