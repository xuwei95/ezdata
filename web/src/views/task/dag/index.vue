<template>
  <div class="app-container">
    <el-form :inline="true" v-show="showSearch">
      <el-form-item label="名称">
        <el-input v-model="query.name" placeholder="DAG 名称" clearable style="width: 200px" @keyup.enter="getList" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="getList">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['task:dag:edit']">新建 DAG</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList" />
    </el-row>

    <el-table v-loading="loading" :data="list">
      <el-table-column label="名称" align="center" prop="name" show-overflow-tooltip />
      <el-table-column label="运行队列" align="center" prop="runQueue" width="120" />
      <el-table-column label="状态" align="center" width="90">
        <template #default="s">
          <el-tag :type="s.row.status === 1 ? 'success' : 'info'">{{ s.row.status === 1 ? '启用' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="已发布" align="center" width="90">
        <template #default="s">
          <el-tag :type="s.row.publishedVersionId ? 'success' : 'warning'" size="small">
            {{ s.row.publishedVersionId ? '是' : '草稿' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" align="center" prop="createTime" width="170" />
      <el-table-column label="操作" align="center" width="220">
        <template #default="s">
          <el-button link type="primary" icon="Share" @click="openEditor(s.row)" v-hasPermi="['task:dag:list']">编排</el-button>
          <el-button link type="danger" icon="Delete" @click="handleDelete(s.row)" v-hasPermi="['task:dag:edit']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <pagination v-show="total > 0" :total="total" v-model:page="query.pageNum" v-model:limit="query.pageSize" @pagination="getList" />

    <DagEditor v-model="editorVisible" :dag-id="curDag.id" :dag-name="curDag.name" />
  </div>
</template>

<script setup name="DagList">
import { ref, reactive, getCurrentInstance } from 'vue'
import { listDag, createDag, delDag } from '@/api/task/dag'
import DagEditor from './editor.vue'

const { proxy } = getCurrentInstance()
const list = ref([])
const total = ref(0)
const loading = ref(false)
const showSearch = ref(true)
const query = reactive({ pageNum: 1, pageSize: 10, name: undefined })
const editorVisible = ref(false)
const curDag = ref({})

function getList() {
  loading.value = true
  listDag(query).then((res) => {
    list.value = res.rows || []
    total.value = res.total || 0
  }).finally(() => (loading.value = false))
}
function resetQuery() {
  query.name = undefined; query.pageNum = 1; getList()
}
function handleAdd() {
  proxy.$prompt('请输入 DAG 名称', '新建 DAG', { inputPattern: /\S/, inputErrorMessage: '名称不能为空' }).then(({ value }) => {
    return createDag({ name: value, runQueue: 'default' })
  }).then((res) => {
    proxy.$modal.msgSuccess('创建成功')
    getList()
    curDag.value = { id: res.data.id, name: '新建 DAG' }
    editorVisible.value = true
  }).catch(() => {})
}
function openEditor(row) {
  curDag.value = { id: row.id, name: row.name }
  editorVisible.value = true
}
function handleDelete(row) {
  proxy.$modal.confirm(`确认删除 DAG「${row.name}」?`).then(() => delDag(row.id)).then(() => {
    proxy.$modal.msgSuccess('删除成功'); getList()
  }).catch(() => {})
}

getList()
</script>
