<template>
  <div class="app-container">
    <el-row :gutter="16">
      <!-- 参数 -->
      <el-col :span="9">
        <el-card shadow="never">
          <template #header>召回参数</template>
          <el-form label-width="90px">
            <el-form-item label="知识库">
              <el-select v-model="datasetIds" multiple filterable placeholder="选择一个或多个知识库" style="width: 100%">
                <el-option v-for="d in datasets" :key="d.id" :label="d.name" :value="d.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="查询">
              <el-input v-model="query" type="textarea" :rows="3" placeholder="输入查询问题" />
            </el-form-item>
            <el-form-item label="检索模式">
              <el-radio-group v-model="retrievalType">
                <el-radio-button value="hybrid">混合</el-radio-button>
                <el-radio-button value="vector">向量</el-radio-button>
                <el-radio-button value="keyword">全文</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="TopK">
              <el-input-number v-model="topK" :min="1" :max="50" />
            </el-form-item>
            <el-form-item label="重排">
              <el-switch v-model="rerank" />
              <span class="tip">启用 rerank 模型二次排序(需配置 RERANK)</span>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" icon="Search" :loading="loading" @click="doSearch">召回测试</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 结果 -->
      <el-col :span="15">
        <el-card shadow="never" v-loading="loading">
          <template #header>召回结果 ({{ records.length }})</template>
          <el-empty v-if="!records.length" description="暂无结果" />
          <div v-for="(r, i) in records" :key="r.chunkId || i" class="hit">
            <div class="hit-head">
              <el-tag size="small" :type="r.chunkType === 'qa' ? 'warning' : 'primary'">{{ r.chunkType }}</el-tag>
              <span class="score">score: {{ (r.score ?? 0).toFixed ? (r.score ?? 0).toFixed(4) : r.score }}</span>
            </div>
            <div class="hit-body">{{ r.content }}</div>
            <div class="hit-meta">库:{{ dsName(r.datasetId) }} · 文档:{{ r.documentId }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup name="RagRetrieval">
import { listDataset, retrieval } from '@/api/rag'

const { proxy } = getCurrentInstance()
const datasets = ref([])
const datasetIds = ref([])
const query = ref('')
const retrievalType = ref('hybrid')
const topK = ref(5)
const rerank = ref(false)
const loading = ref(false)
const records = ref([])

function dsName(id) { return datasets.value.find((d) => d.id === id)?.name || id }

function doSearch() {
  if (!datasetIds.value.length) return proxy.$modal.msgError('请选择知识库')
  if (!query.value.trim()) return proxy.$modal.msgError('请输入查询')
  loading.value = true
  retrieval({
    query: query.value, datasetIds: datasetIds.value, topK: topK.value,
    retrievalType: retrievalType.value, rerank: rerank.value,
  }).then((res) => {
    records.value = res.data?.records || []; loading.value = false
  }).catch(() => (loading.value = false))
}

onMounted(() => {
  listDataset({ pageNum: 1, pageSize: 100 }).then((res) => { datasets.value = res.rows || [] })
})
</script>

<style scoped>
.tip { color: #909399; font-size: 12px; margin-left: 8px; }
.hit { border: 1px solid #ebeef5; border-radius: 6px; padding: 10px 12px; margin-bottom: 10px; }
.hit-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.hit-head .score { color: #67c23a; font-size: 12px; }
.hit-body { color: #303133; font-size: 14px; line-height: 1.6; white-space: pre-wrap; }
.hit-meta { color: #909399; font-size: 12px; margin-top: 6px; }
</style>
