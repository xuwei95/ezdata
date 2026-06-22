<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="任务名称" prop="name">
        <el-input v-model="queryParams.name" placeholder="请输入任务名称" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="触发方式" prop="triggerType">
        <el-select v-model="queryParams.triggerType" placeholder="触发方式" clearable style="width: 160px">
          <el-option label="单次" :value="1" />
          <el-option label="定时" :value="2" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="任务状态" clearable style="width: 160px">
          <el-option label="启用" :value="1" />
          <el-option label="停用" :value="0" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['task:info:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['task:info:remove']">删除</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="taskList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="任务名称" align="center" prop="name" :show-overflow-tooltip="true" />
      <el-table-column label="模板" align="center" prop="templateCode" :show-overflow-tooltip="true" />
      <el-table-column label="触发方式" align="center" prop="triggerType">
        <template #default="scope">
          <el-tag :type="scope.row.triggerType === 2 ? 'success' : 'info'">{{ scope.row.triggerType === 2 ? '定时' : '单次' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="定时表达式" align="center" prop="crontab" :show-overflow-tooltip="true" />
      <el-table-column label="运行队列" align="center" prop="runQueue" width="100" />
      <el-table-column label="状态" align="center" prop="status">
        <template #default="scope">
          <el-switch v-model="scope.row.status" :active-value="1" :inactive-value="0" @change="handleStatusChange(scope.row)" />
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" width="260" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['task:info:edit']">修改</el-button>
          <el-button link type="primary" icon="CaretRight" @click="handleRun(scope.row)" v-hasPermi="['task:info:run']">执行</el-button>
          <el-button link type="primary" icon="Histogram" @click="openRecords(scope.row)" v-hasPermi="['task:instance:query']">记录</el-button>
          <el-button link type="primary" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['task:info:remove']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />

    <!-- 新增/修改任务（模板驱动的低代码表单） -->
    <el-dialog :title="title" v-model="open" fullscreen append-to-body class="task-form-dialog">
      <el-form ref="taskRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="任务模板" prop="templateCode">
          <el-select v-model="form.templateCode" placeholder="请选择任务模板" style="width: 100%" @change="handleTemplateChange">
            <el-option v-for="t in templateOptions" :key="t.code" :label="t.name + ' (' + t.code + ')'" :value="t.code" />
          </el-select>
        </el-form-item>

        <!-- 模板参数：动态配置模板(type=2)以低代码渲染；内置组件模板(type=1)渲染其专属前端组件 -->
        <template v-if="form.templateCode">
          <el-divider content-position="left">任务参数</el-divider>
          <schema-renderer v-if="selectedTemplateType === 2" ref="paramsRendererRef" :schema="paramsSchema" v-model="paramsModel" />
          <component
            v-else-if="builtinComp"
            :is="builtinComp"
            ref="builtinFormRef"
            :task-params="paramsModel"
            :template-info="selectedTemplate"
          />
          <el-alert
            v-else
            type="info"
            :closable="false"
            show-icon
            title="该模板为「内置组件」类型，但未找到对应前端组件，请检查模板 component 配置"
          />
          <el-form-item>
            <el-button icon="VideoPlay" :loading="debugLoading" @click="debugRun">调试运行</el-button>
            <span class="form-tip" style="margin-left: 8px">不保存任务、不投调度，执行一次并打开日志窗口实时查看</span>
          </el-form-item>
        </template>

        <el-divider content-position="left">调度配置</el-divider>
        <el-form-item label="触发方式" prop="triggerType">
          <el-radio-group v-model="form.triggerType">
            <el-radio :value="1">单次(手动触发)</el-radio>
            <el-radio :value="2">定时</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="定时表达式" prop="crontab" v-if="form.triggerType === 2">
          <el-input v-model="form.crontab" placeholder="请输入cron执行表达式">
            <template #append>
              <el-button type="primary" @click="handleShowCron">生成表达式</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-row>
          <el-col :span="12">
            <el-form-item label="运行队列" prop="runQueue">
              <el-select v-model="form.runQueue" placeholder="请选择运行队列" style="width: 100%">
                <el-option v-for="q in runQueueOptions" :key="q" :label="q" :value="q" />
                <!-- 兼容历史值不在当前队列列表中的情况 -->
                <el-option v-if="form.runQueue && !runQueueOptions.includes(form.runQueue)" :key="form.runQueue" :label="form.runQueue" :value="form.runQueue" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-input-number v-model="form.priority" :min="1" :max="10" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="重试次数" prop="retry">
              <el-input-number v-model="form.retry" :min="0" :max="10" controls-position="right" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="重试间隔" prop="countdown">
              <el-input-number v-model="form.countdown" :min="0" controls-position="right" style="width: 100%" />
              <div class="form-tip">单位：秒</div>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="失败告警">
          <el-select v-model="alertStrategyIdsArr" multiple clearable placeholder="选择告警策略(失败重试耗尽时触发,可多选)" style="width: 100%">
            <el-option v-for="s in strategyOptions" :key="s.strategyId" :label="s.strategyName" :value="s.strategyId" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog title="Cron表达式生成器" v-model="openCron" append-to-body destroy-on-close>
      <crontab ref="crontabRef" @hide="openCron = false" @fill="crontabFill" :expression="expression"></crontab>
    </el-dialog>

    <!-- 执行记录抽屉 -->
    <el-drawer v-model="recordOpen" :title="'执行记录 - ' + recordTaskName" size="62%" append-to-body>
      <div style="margin-bottom: 10px">
        <el-button size="small" icon="Refresh" @click="getRecords">刷新</el-button>
      </div>
      <el-table v-loading="recordLoading" :data="recordList" size="small">
        <el-table-column label="实例ID" prop="id" :show-overflow-tooltip="true" min-width="200" />
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="statusTagType(scope.row.status)">{{ scope.row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="进度" width="130">
          <template #default="scope">
            <el-progress :percentage="Math.round(scope.row.progress || 0)" :status="scope.row.status === 'FAILURE' ? 'exception' : (scope.row.progress >= 100 ? 'success' : '')" />
          </template>
        </el-table-column>
        <el-table-column label="开始时间" prop="startTime" width="160" />
        <el-table-column label="操作" width="170">
          <template #default="scope">
            <el-button link type="primary" icon="Document" @click="viewLog(scope.row)" v-hasPermi="['task:instance:query']">日志</el-button>
            <el-button v-if="scope.row.closed !== 1" link type="warning" icon="VideoPause" @click="stopRecord(scope.row)" v-hasPermi="['task:instance:stop']">终止</el-button>
            <el-button link type="danger" icon="Delete" @click="delRecord(scope.row)" v-hasPermi="['task:instance:remove']">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <pagination v-show="recordTotal > 0" :total="recordTotal" v-model:page="recordQuery.pageNum" v-model:limit="recordQuery.pageSize" @pagination="getRecords" />
    </el-drawer>

    <!-- 执行明细日志 -->
    <el-dialog title="执行明细日志" v-model="logOpen" width="900px" append-to-body destroy-on-close>
      <el-alert v-if="!logViewable" title="当前任务执行日志后端不支持在线查看(file模式)，请查看日志文件" type="warning" :closable="false" show-icon />
      <template v-else>
        <div class="log-toolbar">
          <el-switch v-model="logAutoRefresh" active-text="自动刷新(3s)" @change="toggleLogAuto" />
          <el-button size="small" icon="Refresh" @click="getLogList">刷新</el-button>
          <span class="log-count-label">初始加载</span>
          <el-input-number v-model="logLimit" :min="10" :max="2000" :step="50" size="small"
            controls-position="right" style="width: 110px" @change="reloadLog" />
          <span class="log-count-label">条 (新日志自动追加)</span>
        </div>
        <div ref="logConsoleRef" class="log-console">
        <div v-for="(line, idx) in logLines" :key="idx" :class="['log-line', 'lvl-' + (line.level || 'INFO')]">
          <span class="log-time">{{ line.createTime }}</span>
          <span class="log-level">{{ line.level }}</span>
          <span class="log-content">{{ line.content }}</span>
        </div>
        <el-empty v-if="!logLoading && !logLines.length" description="暂无日志" :image-size="60" />
        </div>
        <div class="log-tip">已展示 {{ logLines.length }} 条日志，新日志将持续追加在末尾</div>
      </template>
    </el-dialog>

  </div>
</template>

<script setup name="Task">
import { listTask, getTask, addTask, updateTask, delTask, changeTaskStatus, runTask, debugTask, listRunQueues } from '@/api/task/task'
import { listTemplateAll } from '@/api/task/template'
import { listStrategyAll } from '@/api/alert/strategy'
import { listInstance, stopInstance, delInstance } from '@/api/task/instance'
import { getTaskLogViewable, listTaskLog } from '@/api/task/log'
import Crontab from '@/components/Crontab'
import SchemaRenderer from '@/views/task/components/SchemaRenderer.vue'
import { getTaskComponent } from '@/views/task/components/templates'

const { proxy } = getCurrentInstance()
// 运行队列：实时从在线 worker 获取(无 worker 时后端回退到配置队列)
const runQueueOptions = ref([])
function loadRunQueues() {
  return listRunQueues().then(res => {
    runQueueOptions.value = res.data || []
  }).catch(() => {
    runQueueOptions.value = []
  })
}

const taskList = ref([])
const templateOptions = ref([])
const strategyOptions = ref([])
const alertStrategyIdsArr = ref([])
const selectedTemplateType = ref(2)
const open = ref(false)
const loading = ref(true)
const showSearch = ref(true)
const ids = ref([])
const multiple = ref(true)
const total = ref(0)
const title = ref('')

const openCron = ref(false)
const expression = ref('')
const paramsSchema = ref([])
const paramsModel = ref({})

// 调试运行(不落实例,触发后打开日志弹窗流式查看)
const debugLoading = ref(false)

// 当前选中的模板对象 / 内置组件(type=1 时按 component 字段解析专属前端组件)
const selectedTemplate = computed(() => templateOptions.value.find(t => t.code === form.value.templateCode) || {})
const builtinComp = computed(() =>
  selectedTemplate.value.type === 1 ? getTaskComponent(selectedTemplate.value.component || selectedTemplate.value.code) : null
)

// 执行记录抽屉
const recordOpen = ref(false)
const recordLoading = ref(false)
const recordList = ref([])
const recordTotal = ref(0)
const recordTaskName = ref('')
const recordQuery = reactive({ taskId: undefined, pageNum: 1, pageSize: 10 })

// 执行明细日志
const logOpen = ref(false)
const logLoading = ref(false)
const logViewable = ref(true)
const logLines = ref([])
const logQuery = reactive({ taskUuid: undefined, pageNum: 1, pageSize: 100 })
const logConsoleRef = ref(null)
// 初始加载/重置时拉取最近 N 条(可调,默认100)
const logLimit = ref(100)
// 增量游标(对前端透明的字符串,db后端=日志id/es后端=时间戳):刷新时只拉该游标之后的新日志并追加
const logCursor = ref('')
// 日志自动刷新
const logAutoRefresh = ref(false)
let logTimer = null
function toggleLogAuto(val) {
  if (val) {
    logTimer = setInterval(getLogList, 3000)
  } else if (logTimer) {
    clearInterval(logTimer)
    logTimer = null
  }
}
function stopLogAuto() {
  logAutoRefresh.value = false
  if (logTimer) {
    clearInterval(logTimer)
    logTimer = null
  }
}
// 关闭日志对话框/卸载组件时停止自动刷新
watch(logOpen, val => {
  if (!val) stopLogAuto()
})
onBeforeUnmount(stopLogAuto)

function statusTagType(status) {
  if (status === 'SUCCESS') return 'success'
  if (status === 'FAILURE') return 'danger'
  if (status === 'STARTED' || status === 'RETRY') return 'warning'
  return 'info'
}

function openRecords(row) {
  recordTaskName.value = row.name
  recordQuery.taskId = row.id
  recordQuery.pageNum = 1
  recordOpen.value = true
  getRecords()
}

function getRecords() {
  recordLoading.value = true
  listInstance(recordQuery).then(response => {
    recordList.value = response.rows
    recordTotal.value = response.total
    recordLoading.value = false
  }).catch(() => {
    recordLoading.value = false
  })
}

function stopRecord(row) {
  proxy.$modal.confirm('确认终止执行实例"' + row.id + '"吗?').then(() => stopInstance(row.id)).then(() => {
    getRecords()
    proxy.$modal.msgSuccess('终止指令已发送')
  }).catch(() => {})
}

function delRecord(row) {
  proxy.$modal.confirm('确认删除该执行记录及其日志吗?').then(() => delInstance(row.id)).then(() => {
    getRecords()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

function viewLog(row) {
  logQuery.taskUuid = row.id
  logOpen.value = true
  getTaskLogViewable().then(response => {
    logViewable.value = response.data
    if (logViewable.value) reloadLog()
  })
}

// 重新加载:取最近 logLimit 条替换(打开日志/修改条数时调用)
function reloadLog() {
  if (!logQuery.taskUuid) return
  logLines.value = []
  logCursor.value = ''
  logLoading.value = true
  listTaskLog({ taskUuid: logQuery.taskUuid, pageSize: logLimit.value }).then(response => {
    logLines.value = response.rows || []
    updateLogCursor()
    logLoading.value = false
    scrollLogToBottom()
  }).catch(() => {
    logLoading.value = false
  })
}

// 增量刷新:只拉取 id 大于游标的新日志并追加,老日志保留(自动刷新/手动刷新调用)
function getLogList() {
  if (!logQuery.taskUuid) return
  listTaskLog({ taskUuid: logQuery.taskUuid, after: logCursor.value }).then(response => {
    const rows = response.rows || []
    if (rows.length) {
      logLines.value.push(...rows)
      updateLogCursor()
      scrollLogToBottom()
    }
  }).catch(() => {})
}

// 用当前日志末尾行的 cursor 更新增量游标(后端无关:db=id/es=时间戳)
function updateLogCursor() {
  const rows = logLines.value
  const last = rows.length ? rows[rows.length - 1] : null
  if (last && last.cursor != null) logCursor.value = last.cursor
}

function scrollLogToBottom() {
  nextTick(() => {
    const el = logConsoleRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    name: undefined,
    triggerType: undefined,
    status: undefined
  },
  rules: {
    name: [{ required: true, message: '任务名称不能为空', trigger: 'blur' }],
    templateCode: [{ required: true, message: '请选择任务模板', trigger: 'change' }],
    crontab: [{ required: true, message: 'cron执行表达式不能为空', trigger: 'change' }]
  }
})

const { queryParams, form, rules } = toRefs(data)

function getList() {
  loading.value = true
  listTask(queryParams.value).then(response => {
    taskList.value = response.rows
    total.value = response.total
    loading.value = false
  })
}

function loadTemplates() {
  return listTemplateAll().then(response => {
    templateOptions.value = response.data || []
  })
}

function loadStrategies() {
  listStrategyAll().then(response => {
    strategyOptions.value = response.data || []
  })
}

/** 切换模板时，按模板的参数schema重置低代码表单(仅动态配置模板渲染) */
function handleTemplateChange(code) {
  const tpl = templateOptions.value.find(t => t.code === code)
  selectedTemplateType.value = (tpl && tpl.type) || 2
  paramsSchema.value = selectedTemplateType.value === 2 ? parseSchema(tpl && tpl.params) : []
  // 重置参数模型，仅保留schema中定义的字段默认值
  const model = {}
  paramsSchema.value.forEach(item => {
    model[item.field] = item.default !== undefined ? item.default : undefined
  })
  paramsModel.value = model
}

function parseSchema(raw) {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed : []
  } catch (e) {
    return []
  }
}

function cancel() {
  open.value = false
  reset()
}

function reset() {
  form.value = {
    id: undefined,
    name: undefined,
    templateCode: undefined,
    taskType: 1,
    params: undefined,
    triggerType: 1,
    crontab: undefined,
    runQueue: 'default',
    priority: 1,
    retry: 0,
    countdown: 60,
    status: 0,
    remark: undefined
  }
  paramsSchema.value = []
  paramsModel.value = {}
  alertStrategyIdsArr.value = []
  proxy.resetForm('taskRef')
}

function handleQuery() {
  queryParams.value.pageNum = 1
  getList()
}

function resetQuery() {
  proxy.resetForm('queryRef')
  handleQuery()
}

function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.id)
  multiple.value = !selection.length
}

function handleAdd() {
  reset()
  loadTemplates()
  loadStrategies()
  loadRunQueues()
  open.value = true
  title.value = '新增任务'
}

function handleUpdate(row) {
  reset()
  loadStrategies()
  loadRunQueues()
  Promise.all([loadTemplates(), getTask(row.id)]).then(([, response]) => {
    form.value = response.data
    // 还原低代码参数表单(仅动态配置模板)
    const tpl = templateOptions.value.find(t => t.code === form.value.templateCode)
    selectedTemplateType.value = (tpl && tpl.type) || 2
    paramsSchema.value = selectedTemplateType.value === 2 ? parseSchema(tpl && tpl.params) : []
    paramsModel.value = form.value.params ? safeParse(form.value.params) : {}
    // 还原告警策略多选(CSV -> number[])
    alertStrategyIdsArr.value = form.value.alertStrategyIds
      ? String(form.value.alertStrategyIds).split(',').filter(Boolean).map(Number)
      : []
    open.value = true
    title.value = '修改任务'
  })
}

function safeParse(raw) {
  try {
    return JSON.parse(raw)
  } catch (e) {
    return {}
  }
}

function submitForm() {
  proxy.$refs['taskRef'].validate(valid => {
    if (!valid) return
    // 校验低代码动态参数的必填项(仅动态配置模板)
    if (selectedTemplateType.value === 2 && proxy.$refs.paramsRendererRef) {
      const paramErr = proxy.$refs.paramsRendererRef.validate()
      if (paramErr) {
        proxy.$modal.msgError(paramErr)
        return
      }
    }
    // 内置组件模板(type=1)：由其专属组件生成并校验参数
    if (selectedTemplateType.value === 1 && proxy.$refs.builtinFormRef) {
      const r = proxy.$refs.builtinFormRef.genTaskParams()
      if (r.error) {
        proxy.$modal.msgError(r.error)
        return
      }
      paramsModel.value = r.params || {}
    }
    // 序列化参数
    form.value.params = JSON.stringify(paramsModel.value || {})
    // 告警策略多选(number[] -> CSV)
    form.value.alertStrategyIds = (alertStrategyIdsArr.value || []).join(',')
    if (form.value.id != undefined) {
      updateTask(form.value).then(() => {
        proxy.$modal.msgSuccess('修改成功')
        open.value = false
        getList()
      })
    } else {
      addTask(form.value).then(() => {
        proxy.$modal.msgSuccess('新增成功')
        open.value = false
        getList()
      })
    }
  })
}

// 调试运行:复用表单取参逻辑,不保存任务、不投调度,直接把结果/日志展示在抽屉
function debugRun() {
  proxy.$refs['taskRef'].validate(valid => {
    if (!valid) return
    let params = {}
    if (selectedTemplateType.value === 2 && proxy.$refs.paramsRendererRef) {
      const paramErr = proxy.$refs.paramsRendererRef.validate()
      if (paramErr) { proxy.$modal.msgError(paramErr); return }
      params = paramsModel.value || {}
    } else if (selectedTemplateType.value === 1 && proxy.$refs.builtinFormRef) {
      const r = proxy.$refs.builtinFormRef.genTaskParams()
      if (r.error) { proxy.$modal.msgError(r.error); return }
      params = r.params || {}
    } else {
      params = paramsModel.value || {}
    }
    const tpl = selectedTemplate.value
    debugLoading.value = true
    debugTask({
      templateCode: form.value.templateCode,
      runnerType: tpl.runnerType || 1,
      runnerCode: tpl.runnerCode || null,
      params
    }).then(res => {
      proxy.$modal.msgSuccess('调试已触发')
      // 复用执行日志弹窗:按 taskUuid 流式自动刷新读取日志库,与正式任务一致
      const uuid = res && res.data && res.data.taskUuid
      if (uuid) openInstanceLog(uuid)
    }).finally(() => {
      debugLoading.value = false
    })
  })
}

function handleStatusChange(row) {
  const text = row.status === 1 ? '启用' : '停用'
  proxy.$modal.confirm('确认要"' + text + '""' + row.name + '"任务吗?').then(function () {
    return changeTaskStatus(row.id, row.status)
  }).then(() => {
    proxy.$modal.msgSuccess(text + '成功')
  }).catch(() => {
    row.status = row.status === 1 ? 0 : 1
  })
}

function handleRun(row) {
  proxy.$modal.confirm('确认要立即执行一次"' + row.name + '"任务吗?').then(function () {
    return runTask(row.id)
  }).then((res) => {
    proxy.$modal.msgSuccess('已触发执行')
    // 立即弹出该执行实例的日志窗口并开启自动刷新, 实时查看执行输出
    const iid = res && res.data && res.data.instanceId
    if (iid) openInstanceLog(iid)
  }).catch(() => {})
}

// 打开指定执行实例的日志弹窗, 并默认开启自动刷新(实时滚动)
function openInstanceLog(instanceId) {
  logQuery.taskUuid = instanceId
  logLines.value = []
  logOpen.value = true
  getTaskLogViewable().then(response => {
    logViewable.value = response.data
    if (logViewable.value) {
      reloadLog()
      if (!logAutoRefresh.value) {
        logAutoRefresh.value = true
        toggleLogAuto(true)
      }
    }
  })
}

function handleDelete(row) {
  const taskIds = row.id || ids.value.join(',')
  proxy.$modal.confirm('是否确认删除选中的任务？').then(function () {
    return delTask(taskIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

function handleShowCron() {
  expression.value = form.value.crontab
  openCron.value = true
}

function crontabFill(value) {
  form.value.crontab = value
}

getList()
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
.log-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.log-count-label {
  font-size: 12px;
  color: #909399;
}
.log-tip {
  margin-top: 6px;
  font-size: 12px;
  color: #909399;
  text-align: right;
}
.log-console {
  height: 480px;
  overflow-y: auto;
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 10px;
  border-radius: 4px;
  font-family: Consolas, Monaco, 'Courier New', monospace;
  font-size: 12px;
}
.log-line {
  white-space: pre-wrap;
  word-break: break-all;
  line-height: 1.6;
}
.log-time {
  color: #6a9955;
  margin-right: 8px;
}
.log-level {
  display: inline-block;
  width: 64px;
  margin-right: 8px;
}
.lvl-ERROR .log-level,
.lvl-ERROR .log-content {
  color: #f48771;
}
.lvl-WARNING .log-level {
  color: #dcdcaa;
}
.lvl-INFO .log-level {
  color: #569cd6;
}
</style>

<!-- 全屏任务表单:内容居中限宽,避免输入框拉满过宽 -->
<style>
.task-form-dialog .el-dialog__body {
  max-width: 1180px;
  margin: 0 auto;
}
</style>
