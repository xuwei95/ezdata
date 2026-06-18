<template>
  <div class="api-tab" ref="rootEl">
    <!-- 接口地址(置顶) -->
    <el-card shadow="never" class="sec api-addr">
      <template #header>
        <div class="addr-head">
          <span>数据接口地址</span>
          <div class="addr-actions">
            <el-button size="small" icon="DocumentCopy" @click="copyQueryString">复制查询串</el-button>
            <el-button size="small" icon="CopyDocument" @click="copyText(fullUrl)">复制完整URL</el-button>
            <el-button size="small" type="primary" icon="Key" @click="openTokenDlg">管理 apikey</el-button>
          </div>
        </div>
      </template>
      <div class="url-box">
        <span class="method">GET</span>
        <code class="url">{{ fullUrl }}</code>
      </div>
      <div class="hint">
        公开访问需带 <code>apikey</code> 参数(在「管理 apikey」中生成),将 <code>YOUR_APIKEY</code> 替换为真实 key;
        下方筛选条件会实时拼进地址。
      </div>
    </el-card>

    <!-- 条件筛选(平台内预览) -->
    <el-card shadow="never" class="sec">
      <template #header><span>条件筛选(平台内预览)</span></template>
      <div v-for="(f, i) in filters" :key="i" class="filter-row">
        <el-select v-model="f.field" placeholder="字段" filterable style="width: 170px">
          <el-option v-for="c in fields" :key="c.name" :label="c.name" :value="c.name" />
        </el-select>
        <el-select v-model="f.op" placeholder="操作符" style="width: 120px">
          <el-option v-for="o in operators" :key="o.op" :label="o.label" :value="o.op" />
        </el-select>
        <el-input v-model="f.value" placeholder="值" style="width: 180px" v-if="!isSort(f.op)" />
        <el-button icon="Delete" link @click="filters.splice(i, 1)" />
      </div>
      <el-button size="small" icon="Plus" @click="filters.push({ field: '', op: 'eq', value: '' })">加条件</el-button>
      <el-button size="small" type="primary" icon="Search" :loading="loading" @click="preview">预览</el-button>
    </el-card>

    <!-- 预览结果(分页):vxe-table 虚拟滚动 + 高度占满底部 -->
    <div class="grid-wrap" ref="gridWrap">
      <vxe-table :data="rows" :height="gridH" border stripe show-overflow
        :scroll-y="{ enabled: true, gt: 50 }" :scroll-x="{ enabled: true, gt: 20 }"
        :column-config="{ resizable: true }" :loading="loading">
        <vxe-column type="seq" width="60" fixed="left" />
        <vxe-column v-for="c in columns" :key="c" :field="c" :title="c" :width="170" :resizable="true" />
      </vxe-table>
      <el-pagination layout="prev, pager, next, total" :total="total" :page-size="req.pagesize"
        :current-page="req.page" @current-change="(p) => { req.page = p; preview() }" style="margin-top: 8px" />
    </div>

    <!-- apikey 管理弹窗 -->
    <el-dialog v-model="tokenDlg" title="apikey 管理" width="700px" append-to-body>
      <div style="margin-bottom: 10px">
        <el-button type="primary" size="small" icon="Plus" @click="createToken">生成 apikey</el-button>
        <span class="hint" style="margin-left: 10px">apikey 绑定当前模型 <code>{{ model.code }}</code>,仅可访问该数据接口。</span>
      </div>
      <el-table :data="tokens" border size="small" v-loading="tokenLoading">
        <el-table-column label="名称" prop="name" width="150" show-overflow-tooltip />
        <el-table-column label="apikey">
          <template #default="s">
            <el-text class="key" truncated>{{ s.row.token }}</el-text>
            <el-button link icon="CopyDocument" @click="copyText(s.row.token)" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170">
          <template #default="s">
            <el-button link type="primary" @click="copyText(urlOf(s.row.token))">复制完整URL</el-button>
            <el-button link type="danger" @click="removeToken(s.row.id)">删除</el-button>
          </template>
        </el-table-column>
        <template #empty>暂无 apikey,点击「生成 apikey」创建</template>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup name="DataInterfaceTab">
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getOperators, searchModel } from '@/api/dataManage/data'
import { listToken, addToken, delToken } from '@/api/apitoken/token'

const props = defineProps({ model: { type: Object, required: true } })

const operators = ref([])
const fields = ref([])
const filters = ref([])
const rows = ref([])
const columns = ref([])
const total = ref(0)
const loading = ref(false)
const tokens = ref([])
const tokenDlg = ref(false)
const tokenLoading = ref(false)
const req = reactive({ page: 1, pagesize: 20 })
const openBase = location.origin + (import.meta.env.VITE_APP_BASE_API || '')

// 表格高度:贴到所在面板(splitpanes)底部,并给底部分页条预留空间,避免分页被挤出可视区
const PAGER_RESERVE = 60
const gridH = ref(400)
const gridWrap = ref()
const rootEl = ref()
async function computeH() {
  await nextTick()
  const el = gridWrap.value
  // 数据接口 tab 未激活时为 display:none(offsetParent 为 null),量出来全是 0,跳过;
  // 由 ResizeObserver 在 tab 变可见(尺寸 0→实际)时再触发一次,保证拿到真实位置。
  if (!el || el.offsetParent === null) return
  const top = el.getBoundingClientRect().top
  // 以所在面板底部为界(面板高度 = calc(100vh-120px)),而非整个视口,否则分页会落到面板下方被裁掉
  const pane = el.closest('.splitpanes') || el.closest('.right-panel')
  const bottom = pane ? pane.getBoundingClientRect().bottom : window.innerHeight
  gridH.value = Math.max(200, Math.floor(bottom - top - PAGER_RESERVE))
}

const isSort = (op) => op === 'sort_asc' || op === 'sort_desc'

function qs() {
  return filters.value
    .filter((f) => f.field && f.op)
    .map((f) => `${f.op}[${f.field}]=${encodeURIComponent(isSort(f.op) ? '' : f.value)}`)
    .join('&')
}

function urlOf(apikey) {
  const s = qs()
  return `${openBase}/open/data/${props.model.code}?apikey=${apikey}${s ? '&' + s : ''}&page=1&pagesize=20`
}
const fullUrl = computed(() => urlOf('YOUR_APIKEY'))

async function loadTokens() {
  tokenLoading.value = true
  try {
    tokens.value = (await listToken({ tokenType: 'data_api', refId: props.model.code, pageSize: 50 })).rows || []
  } finally {
    tokenLoading.value = false
  }
}

function openTokenDlg() {
  tokenDlg.value = true
  loadTokens()
}

function sync() {
  fields.value = props.model.fields || []
  filters.value = []; rows.value = []; columns.value = []; total.value = 0; req.page = 1
  if (!operators.value.length) getOperators().then((r) => { operators.value = r.data || [] })
  computeH()
}
watch(() => props.model && props.model.id, sync)
// 条件行增减会改变表格起点,重算高度
watch(() => filters.value.length, computeH)

let ro = null
onMounted(() => {
  sync()
  window.addEventListener('resize', computeH)
  // 监听组件根尺寸:从 display:none(tab 未激活)变可见时会触发,届时才量得到真实位置
  ro = new ResizeObserver(() => computeH())
  if (rootEl.value) ro.observe(rootEl.value)
})
onUnmounted(() => {
  window.removeEventListener('resize', computeH)
  if (ro) { ro.disconnect(); ro = null }
})

async function preview() {
  loading.value = true
  try {
    const res = await searchModel(props.model.id, {
      filters: filters.value.filter((f) => f.field && f.op), page: req.page, pagesize: req.pagesize,
    })
    rows.value = res.data.records || []
    columns.value = rows.value.length ? Object.keys(rows.value[0]) : []
    total.value = res.data.total || 0
  } finally {
    loading.value = false
  }
}

function copyText(t) { navigator.clipboard.writeText(t); ElMessage.success('已复制') }

function copyQueryString() {
  const s = qs()
  copyText(`apikey=YOUR_APIKEY${s ? '&' + s : ''}&page=1&pagesize=20`)
}

async function createToken() {
  const { value: name } = await ElMessageBox.prompt('apikey 名称', '生成 apikey', { inputValue: props.model.name + ' 接口' })
  await addToken({ name, tokenType: 'data_api', refId: props.model.code })
  ElMessage.success('已生成')
  loadTokens()
}

async function removeToken(id) {
  await ElMessageBox.confirm('删除该 apikey?', '提示', { type: 'warning' })
  await delToken(id)
  ElMessage.success('已删除')
  loadTokens()
}
</script>

<style scoped>
.sec { margin-bottom: 10px; }
.api-addr .addr-head { display: flex; align-items: center; justify-content: space-between; }
.api-addr .addr-actions { display: flex; gap: 6px; }
.url-box { display: flex; align-items: center; gap: 8px; background: #f5f7fa; border-radius: 4px; padding: 8px 10px; }
.url-box .method { font-weight: 600; color: #67c23a; font-family: monospace; }
.url-box .url { color: #409eff; word-break: break-all; font-size: 13px; }
.grid-wrap { margin-top: 10px; }
.filter-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.key { max-width: 320px; font-family: monospace; }
.hint { font-size: 12px; color: #909399; }
.hint code, .url-box code { color: #409eff; }
</style>
