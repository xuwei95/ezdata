<template>
  <div class="query-tab">
    <el-radio-group v-model="mode" size="small" style="margin-bottom: 10px">
      <el-radio-button label="native">原生查询</el-radio-button>
      <el-radio-button label="ai">AI 取数</el-radio-button>
    </el-radio-group>

    <!-- AI 取数:自然语言 → 生成原生查询 → 执行 -->
    <div v-if="mode === 'ai'" class="ai-bar">
      <el-input v-model="question" placeholder="用自然语言描述你想查什么,例如:最近一周金额最高的 10 笔订单"
        @keyup.enter="runAi">
        <template #prepend><el-icon><MagicStick /></el-icon></template>
        <template #append>
          <el-button :loading="loading" @click="runAi">生成并查询</el-button>
        </template>
      </el-input>
      <div v-if="genSql" class="gen-sql">
        <span class="lbl">AI 生成:</span><code>{{ genSql }}</code>
      </div>
    </div>

    <!-- 原生查询 -->
    <div v-else class="native-bar">
      <el-input v-model="native" type="textarea" :rows="4"
        placeholder="原生查询(SQL 字符串 / DSL JSON),例如:SELECT * FROM xxx WHERE ..." />
      <el-button type="primary" icon="Search" :loading="loading" @click="runNative" style="margin-top: 8px">查询</el-button>
    </div>

    <div class="result-bar">
      <span class="count" v-if="rows.length">共 {{ rows.length }} 行(虚拟滚动,不分页)</span>
      <span class="count" v-else>暂无数据</span>
      <el-button size="small" icon="Download" :disabled="!rows.length" @click="exportExcel">导出 Excel</el-button>
    </div>

    <!-- vxe-table 数据网格:行/列虚拟滚动 + 列可拖宽 + 高度占满底部 -->
    <div class="grid-wrap" ref="gridWrap">
      <vxe-table :data="rows" :height="gridH" border stripe show-overflow
        :scroll-y="{ enabled: true, gt: 50 }" :scroll-x="{ enabled: true, gt: 20 }"
        :column-config="{ resizable: true }" :loading="loading">
        <vxe-column type="seq" width="60" fixed="left" />
        <vxe-column v-for="c in columns" :key="c" :field="c" :title="c" :width="170" :resizable="true" />
      </vxe-table>
    </div>
  </div>
</template>

<script setup name="DataQueryTab">
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import * as XLSX from 'xlsx'
import { queryModel, aiQueryModel, getSampleQuery } from '@/api/dataManage/data'

const props = defineProps({ model: { type: Object, required: true } })

const mode = ref('native')
const question = ref('')
const genSql = ref('')
const native = ref('')
const rows = ref([])
const columns = ref([])
const loading = ref(false)

// 表格高度:按表格实际位置算,正好贴到视口底部(留出横向滚动条空间)
const gridH = ref(400)
const gridWrap = ref()
async function computeH() {
  await nextTick()
  const top = gridWrap.value ? gridWrap.value.getBoundingClientRect().top : 240
  gridH.value = Math.max(240, Math.floor(window.innerHeight - top - 24))
}

function exportExcel() {
  if (!rows.value.length) return
  const ws = XLSX.utils.json_to_sheet(rows.value, { header: columns.value })
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'data')
  XLSX.writeFile(wb, `${props.model.name || 'data'}_${Date.now()}.xlsx`)
}

async function syncModel() {
  question.value = ''; genSql.value = ''; native.value = ''; rows.value = []; columns.value = []
  if (!props.model || !props.model.id) return
  // 预填原生查询默认示例(各源对应方言,limit 100)
  try {
    const q = (await getSampleQuery(props.model.id)).data.native
    native.value = typeof q === 'string' ? q : JSON.stringify(q, null, 2)
  } catch (e) { /* 忽略 */ }
}
watch(() => props.model && props.model.id, syncModel)
// 模式切换(AI 单行/原生多行)、AI 生成 SQL 行出现都会改变表格起点,重算高度
watch([mode, genSql], computeH)
onMounted(() => { syncModel(); computeH(); window.addEventListener('resize', computeH) })
onUnmounted(() => window.removeEventListener('resize', computeH))

function fill(records) {
  rows.value = records || []
  columns.value = rows.value.length ? Object.keys(rows.value[0]) : []
}

async function runAi() {
  if (!question.value.trim()) { ElMessage.warning('请输入查询需求'); return }
  loading.value = true
  try {
    const res = await aiQueryModel(props.model.id, { question: question.value })
    genSql.value = res.data.query
    fill(res.data.records)
    ElMessage.success(`AI 取数 ${res.data.total} 行`)
  } catch (e) {
    ElMessage.error('AI 取数失败:' + (e?.msg || e?.message || '请检查是否已配置 AI 模型'))
  } finally {
    loading.value = false
  }
}

async function runNative() {
  if (!native.value.trim()) { ElMessage.warning('请输入查询语句'); return }
  loading.value = true
  try {
    let n = native.value.trim()
    try { n = JSON.parse(n) } catch (e) { /* 当作 SQL 字符串 */ }
    const res = await queryModel(props.model.id, { native: n })
    fill(res.data.records)
    ElMessage.success(`查询到 ${res.data.total} 行`)
  } catch (e) {
    ElMessage.error('查询失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.result-bar { display: flex; align-items: center; justify-content: space-between; margin: 10px 0 6px; }
.count { color: #909399; font-size: 13px; }
.gen-sql { margin-top: 8px; font-size: 13px; background: #f5f7fa; padding: 6px 10px; border-radius: 4px; }
.gen-sql .lbl { color: #909399; margin-right: 6px; }
.gen-sql code { color: #409eff; word-break: break-all; }
</style>
