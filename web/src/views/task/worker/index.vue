<template>
  <div class="app-container">
    <el-card shadow="never">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>Worker 列表</span>
          <div>
            <el-switch v-model="autoRefresh" active-text="自动刷新" inline-prompt style="margin-right: 12px" @change="toggleAuto" />
            <el-button type="primary" icon="Refresh" :loading="loading" @click="getList">刷新</el-button>
          </div>
        </div>
      </template>

      <el-table v-loading="loading" :data="workerList" border>
        <el-table-column label="Worker" prop="name" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="90" align="center">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'online' ? 'success' : 'info'">
              {{ scope.row.status === 'online' ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="并发" prop="maxConcurrency" width="80" align="center" />
        <el-table-column label="进程" width="110" align="center">
          <template #default="scope">{{ Array.isArray(scope.row.processes) ? scope.row.processes.length : '-' }}</template>
        </el-table-column>
        <el-table-column label="运行中" width="90" align="center">
          <template #default="scope">
            <el-link type="primary" :underline="false" @click="openTasks(scope.row)">{{ scope.row.activeCount }}</el-link>
          </template>
        </el-table-column>
        <el-table-column label="消费队列" min-width="200">
          <template #default="scope">
            <el-tag v-for="q in scope.row.queues" :key="q" class="qtag" type="warning" effect="plain">{{ q }}</el-tag>
            <span v-if="!scope.row.queues || !scope.row.queues.length" class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320" align="center">
          <template #default="scope">
            <el-button link type="primary" icon="Operation" @click="openQueue(scope.row)" v-hasPermi="['task:worker:consumer']">队列管理</el-button>
            <el-button link type="primary" icon="ScaleToOriginal" @click="openScale(scope.row)" v-hasPermi="['task:worker:scale']">并发伸缩</el-button>
            <el-button link type="primary" icon="List" @click="openTasks(scope.row)">运行任务</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 队列管理 -->
    <el-dialog v-model="queueOpen" :title="'队列管理 - ' + current.name" width="520px" append-to-body>
      <div style="margin-bottom: 12px">
        <el-tag v-for="q in current.queues" :key="q" closable class="qtag" type="warning" @close="doCancelConsumer(q)">{{ q }}</el-tag>
        <span v-if="!current.queues || !current.queues.length" class="text-muted">当前无消费队列</span>
      </div>
      <el-input v-model="newQueue" placeholder="输入要订阅的队列名" style="width: 320px; margin-right: 8px" />
      <el-button type="primary" :disabled="!newQueue" @click="doAddConsumer">添加订阅</el-button>
    </el-dialog>

    <!-- 并发伸缩 -->
    <el-dialog v-model="scaleOpen" :title="'并发伸缩 - ' + current.name" width="460px" append-to-body>
      <el-alert type="info" :closable="false" show-icon style="margin-bottom: 12px"
        title="并发伸缩仅 prefork 池有效。固定并发(--concurrency 启动)用「增加/减少」；弹性并发(--autoscale 启动)用下方 autoscale 设置范围。两种模式互斥，按 worker 实际启动方式选择对应操作即可。" />
      <el-form label-width="100px">
        <el-form-item label="当前并发">{{ current.maxConcurrency }}</el-form-item>
        <el-form-item label="增减步长">
          <el-input-number v-model="scaleN" :min="1" :max="50" controls-position="right" />
          <el-button type="success" plain style="margin-left: 8px" @click="doGrow">增加</el-button>
          <el-button type="warning" plain @click="doShrink">减少</el-button>
        </el-form-item>
        <el-divider content-position="left">弹性并发(autoscale)</el-divider>
        <el-form-item label="最小/最大">
          <el-input-number v-model="scaleMin" :min="0" :max="50" controls-position="right" />
          <span style="margin: 0 8px">~</span>
          <el-input-number v-model="scaleMax" :min="1" :max="50" controls-position="right" />
          <el-button type="primary" plain style="margin-left: 8px" @click="doAutoscale">应用</el-button>
        </el-form-item>
      </el-form>
    </el-dialog>

    <!-- 运行中任务 -->
    <el-drawer v-model="tasksOpen" :title="'运行中任务 - ' + current.name" size="60%" append-to-body>
      <div style="margin-bottom: 10px">
        <el-button size="small" icon="Refresh" @click="getTasks">刷新</el-button>
      </div>
      <el-table v-loading="tasksLoading" :data="taskList" border size="small">
        <el-table-column label="任务实例ID" prop="id" min-width="260" show-overflow-tooltip />
        <el-table-column label="任务" prop="name" min-width="200" show-overflow-tooltip />
        <el-table-column label="参数" prop="args" min-width="160" show-overflow-tooltip />
        <el-table-column label="开始时间" width="170">
          <template #default="scope">{{ fmtTime(scope.row.timeStart) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="center">
          <template #default="scope">
            <el-button link type="warning" icon="VideoPause" @click="doRevoke(scope.row)" v-hasPermi="['task:instance:stop']">终止</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!tasksLoading && !taskList.length" description="该 Worker 当前无运行任务" />
    </el-drawer>
  </div>
</template>

<script setup name="TaskWorker">
import { listWorkers, listWorkerTasks, addConsumer, cancelConsumer, poolGrow, poolShrink, autoscale } from '@/api/task/worker'
import { stopInstance } from '@/api/task/instance'

const { proxy } = getCurrentInstance()

const loading = ref(false)
const workerList = ref([])
const autoRefresh = ref(false)
let timer = null

const current = ref({})
const queueOpen = ref(false)
const newQueue = ref('')
const scaleOpen = ref(false)
const scaleN = ref(1)
const scaleMin = ref(1)
const scaleMax = ref(4)
const tasksOpen = ref(false)
const tasksLoading = ref(false)
const taskList = ref([])

function getList() {
  loading.value = true
  listWorkers().then(res => {
    workerList.value = res.data || []
    // 同步刷新当前已打开对话框里的 worker 信息
    if (current.value.name) {
      const found = workerList.value.find(w => w.name === current.value.name)
      if (found) current.value = found
    }
  }).finally(() => { loading.value = false })
}

function toggleAuto(val) {
  if (val) {
    timer = setInterval(getList, 5000)
  } else if (timer) {
    clearInterval(timer); timer = null
  }
}

onMounted(getList)
onBeforeUnmount(() => { if (timer) clearInterval(timer) })

function fmtTime(ts) {
  if (!ts) return '-'
  const d = new Date(ts * 1000)
  const p = n => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

// 队列管理
function openQueue(row) { current.value = row; newQueue.value = ''; queueOpen.value = true }
function doAddConsumer() {
  addConsumer({ worker: current.value.name, queue: newQueue.value }).then(() => {
    proxy.$modal.msgSuccess('增加消费队列成功')
    newQueue.value = ''
    getList()
  })
}
function doCancelConsumer(queue) {
  proxy.$modal.confirm(`确认移除队列「${queue}」的订阅吗?`).then(() => cancelConsumer({ worker: current.value.name, queue })).then(() => {
    proxy.$modal.msgSuccess('移除消费队列成功')
    getList()
  }).catch(() => {})
}

// 并发伸缩
function openScale(row) { current.value = row; scaleN.value = 1; scaleMin.value = 1; scaleMax.value = Math.max(2, row.maxConcurrency || 4); scaleOpen.value = true }
function doGrow() {
  poolGrow({ worker: current.value.name, n: scaleN.value }).then(() => { proxy.$modal.msgSuccess('增加并发成功'); getList() })
}
function doShrink() {
  poolShrink({ worker: current.value.name, n: scaleN.value }).then(() => { proxy.$modal.msgSuccess('减少并发成功'); getList() })
}
function doAutoscale() {
  if (scaleMax.value < scaleMin.value) { proxy.$modal.msgError('最大并发不能小于最小并发'); return }
  autoscale({ worker: current.value.name, max: scaleMax.value, min: scaleMin.value }).then(() => { proxy.$modal.msgSuccess('设置弹性并发成功'); getList() })
}

// 运行任务
function openTasks(row) { current.value = row; tasksOpen.value = true; getTasks() }
function getTasks() {
  tasksLoading.value = true
  listWorkerTasks(current.value.name).then(res => { taskList.value = res.data || [] }).finally(() => { tasksLoading.value = false })
}
function doRevoke(row) {
  proxy.$modal.confirm(`确认终止任务实例「${row.id}」吗?`).then(() => stopInstance(row.id)).then(() => {
    proxy.$modal.msgSuccess('终止指令已发送')
    setTimeout(getTasks, 1000)
  }).catch(() => {})
}
</script>

<style scoped>
.qtag { margin: 2px 6px 2px 0; }
.text-muted { color: var(--el-text-color-secondary, #909399); }
</style>
