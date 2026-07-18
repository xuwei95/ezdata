<template>
  <div class="app-container dash-mgr">
    <div class="bar">
      <el-radio-group v-model="typeFilter">
        <el-radio-button label="">全部</el-radio-button>
        <el-radio-button label="chart">单图</el-radio-button>
        <el-radio-button label="board">多图</el-radio-button>
        <el-radio-button label="screen">大屏</el-radio-button>
      </el-radio-group>
      <el-input v-model="kw" placeholder="搜索看板名称" clearable prefix-icon="Search" class="kw" style="width: 220px" />
      <el-dropdown class="new-btn" @command="onNew">
        <el-button type="primary" icon="Plus">新建<el-icon class="el-icon--right"><ArrowDown /></el-icon></el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="chart">单图看板</el-dropdown-item>
            <el-dropdown-item command="board">多图看板</el-dropdown-item>
            <el-dropdown-item command="screen">数据大屏</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
      <el-button icon="Refresh" @click="loadList">刷新</el-button>
    </div>

    <el-table :data="filteredList" border v-loading="loading">
      <el-table-column type="index" label="#" width="55" />
      <el-table-column label="名称" prop="name" min-width="200" show-overflow-tooltip />
      <el-table-column label="类型" width="90">
        <template #default="s"><el-tag size="small" :type="TAG[s.row.dashType] || 'info'">{{ TYPE_LABEL[s.row.dashType] || '单图' }}</el-tag></template>
      </el-table-column>
      <el-table-column label="更新时间" prop="updateTime" width="170" />
      <el-table-column label="操作" width="320" fixed="right">
        <template #default="s">
          <el-button link type="primary" icon="View" @click="toView(s.row)">预览</el-button>
          <el-button link type="primary" icon="Edit" @click="toEditor(s.row)">编辑</el-button>
          <el-button link :type="s.row.shareToken ? 'success' : 'primary'" icon="Share" @click="openShare(s.row)">
            {{ s.row.shareToken ? '已分享' : '分享' }}</el-button>
          <el-button link type="danger" icon="Delete" @click="del(s.row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>暂无看板,点「新建」创建</template>
    </el-table>

    <el-dialog v-model="sh.visible" title="分享看板" width="620px" append-to-body>
      <div v-if="!sh.token" class="sh-empty">
        <el-empty description="尚未开启分享" :image-size="60" />
        <div class="sh-enable">
          <el-button type="primary" :loading="sh.loading" @click="enableShare">开启匿名分享</el-button>
          <div class="tip">开启后任何人凭链接免登录查看,可随时关闭。</div>
        </div>
      </div>
      <div v-else>
        <el-form label-width="76px">
          <el-form-item label="公开链接">
            <el-input v-model="shareUrl" readonly><template #append><el-button icon="CopyDocument" @click="copyText(shareUrl)" /></template></el-input>
          </el-form-item>
          <el-form-item label="嵌入代码"><el-input v-model="embedCode" type="textarea" :rows="2" readonly /></el-form-item>
        </el-form>
        <div class="sh-actions">
          <el-button size="small" icon="CopyDocument" @click="copyText(embedCode)">复制嵌入代码</el-button>
          <el-button size="small" :loading="sh.loading" @click="enableShare">重置链接</el-button>
          <el-button size="small" type="danger" :loading="sh.loading" @click="disableShare">关闭分享</el-button>
        </div>
      </div>
    </el-dialog>

    <!-- 编辑器:统一全屏弹窗(单图 / 多图·大屏),保存后回调刷新列表 -->
    <ChartEditor v-model="chartEd.visible" :id="chartEd.id" @saved="loadList" />
    <DashEditor v-model="boardEd.visible" :id="boardEd.id" :dash-type="boardEd.dashType" @saved="loadList" />
    <!-- 预览:统一全屏弹窗;内含「新标签纯图页」跳转 -->
    <PreviewDialog v-model="pv.visible" :row="pv.row" />
  </div>
</template>

<script setup name="DashboardList">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { listDashboards, delDashboard, genDashboardShare, revokeDashboardShare } from '@/api/dataManage/data'
import ChartEditor from './ChartEditor.vue'
import DashEditor from './DashEditor.vue'
import PreviewDialog from './PreviewDialog.vue'
import { copyToClipboard } from '@/utils/clipboard'

const router = useRouter()
const loading = ref(false)
const list = ref([])
const typeFilter = ref('')
const kw = ref('')
const TYPE_LABEL = { chart: '单图', board: '多图', screen: '大屏' }
const TAG = { chart: '', board: 'success', screen: 'warning' }

// 编辑器弹窗状态(单图 / 多图·大屏)
const chartEd = reactive({ visible: false, id: '' })
const boardEd = reactive({ visible: false, id: '', dashType: 'board' })
// 预览弹窗(单图/多图/大屏统一)
const pv = reactive({ visible: false, row: null })

const filteredList = computed(() => {
  const t = typeFilter.value
  const k = kw.value.trim().toLowerCase()
  return list.value.filter((r) =>
    (!t || (r.dashType || 'chart') === t) &&
    (!k || (r.name || '').toLowerCase().includes(k))
  )
})

async function loadList() {
  loading.value = true
  try { list.value = (await listDashboards()).data || [] } finally { loading.value = false }
}
function onNew(type) {
  if (type === 'chart') { chartEd.id = ''; chartEd.visible = true }
  else { boardEd.id = ''; boardEd.dashType = type; boardEd.visible = true }
}
function toEditor(row) {
  if ((row.dashType || 'chart') === 'chart') { chartEd.id = row.id; chartEd.visible = true }
  else { boardEd.id = row.id; boardEd.dashType = row.dashType || 'board'; boardEd.visible = true }
}
function toView(row) {
  pv.row = row
  pv.visible = true
}
async function del(row) {
  try { await ElMessageBox.confirm(`删除「${row.name}」?`, '提示', { type: 'warning' }) } catch (e) { return }
  await delDashboard(row.id); ElMessage.success('已删除'); loadList()
}

// ---- 分享(统一走 dashboard 接口,单图/多图/大屏通用)----
const sh = reactive({ visible: false, row: null, token: '', loading: false })
const shareUrl = computed(() => (sh.token ? location.origin + router.resolve({ name: 'DashShare', params: { token: sh.token } }).href : ''))
const embedCode = computed(() => (sh.token ? `<iframe src="${shareUrl.value}" width="1280" height="720" frameborder="0"></iframe>` : ''))
function openShare(row) { sh.visible = true; sh.row = row; sh.token = row.shareToken || '' }
async function enableShare() {
  sh.loading = true
  try { const t = (await genDashboardShare(sh.row.id)).data.token; sh.token = t; sh.row.shareToken = t; ElMessage.success('已开启分享') }
  catch (e) { ElMessage.error('操作失败') } finally { sh.loading = false }
}
async function disableShare() {
  sh.loading = true
  try { await revokeDashboardShare(sh.row.id); sh.token = ''; sh.row.shareToken = ''; ElMessage.success('已关闭分享') }
  catch (e) { ElMessage.error('操作失败') } finally { sh.loading = false }
}
async function copyText(t) { (await copyToClipboard(t)) ? ElMessage.success('已复制') : ElMessage.warning('复制失败,请手动选择复制') }

loadList()
</script>

<style scoped>
.dash-mgr .bar { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.dash-mgr .new-btn { margin-left: auto; }
.sh-enable { text-align: center; }
.sh-enable .tip { margin-top: 8px; font-size: 12px; color: #909399; }
.sh-actions { display: flex; gap: 8px; justify-content: flex-end; }
</style>
