<template>
  <div class="task-proposal" :class="{ 'is-created': created }">
    <div class="tp-head">
      <el-icon class="tp-icon"><Document /></el-icon>
      <span class="tp-title">{{ isUpdate ? "AI 任务修改建议" : "AI 任务建议" }}</span>
      <el-tag size="small" :type="isUpdate ? 'warning' : 'info'" effect="plain">{{ tplLabel }}</el-tag>
      <el-tag v-if="isUpdate" size="small" type="warning" effect="light">修改已有</el-tag>
      <span v-if="action.summary" class="tp-summary">{{ action.summary }}</span>
    </div>

    <template v-if="!created">
      <el-form label-width="80px" class="tp-meta">
        <el-form-item label="任务名称">
          <el-input v-model="name" placeholder="任务名称" />
        </el-form-item>
        <el-form-item label="触发方式">
          <el-radio-group v-model="triggerType">
            <el-radio :value="1">单次</el-radio>
            <el-radio :value="2">定时</el-radio>
          </el-radio-group>
          <el-input
            v-if="triggerType === 2"
            v-model="crontab"
            placeholder="Cron 表达式"
            style="width: 300px; margin-left: 12px"
          >
            <template #append>
              <el-button @click="handleShowCron">生成表达式</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item v-if="isUpdate" label="状态">
          <el-radio-group v-model="status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <el-dialog title="Cron表达式生成器" v-model="openCron" append-to-body destroy-on-close>
        <!-- 必须用 PascalCase <Crontab>:本组件里有个同名 ref `crontab`,kebab 的 <crontab> 会被解析成那个 ref 而非组件 -->
        <Crontab @hide="openCron = false" @fill="crontabFill" :expression="expression"></Crontab>
      </el-dialog>

      <!-- 调试运行日志(不落任务,流式看这次试跑的日志) -->
      <el-dialog title="调试运行 · 实时日志" v-model="debugOpen" width="820px" append-to-body @close="stopDebugPolling">
        <div ref="debugConsoleRef" class="tp-log-console">
          <div v-for="(line, i) in debugLogs" :key="i" :class="['tp-log-line', 'lvl-' + (line.level || 'INFO')]">
            <span class="tp-log-time">{{ line.createTime }}</span>
            <span class="tp-log-level">{{ line.level }}</span>
            <span class="tp-log-content">{{ line.content }}</span>
          </div>
          <el-empty v-if="!debugLogs.length" description="等待日志输出…" :image-size="50" />
        </div>
        <div class="tp-log-tip">调试实例 {{ debugUuid }} · 已 {{ debugLogs.length }} 条,新日志持续追加</div>
      </el-dialog>

      <div class="tp-body">
        <component :is="tplComp" v-if="tplComp" ref="tplRef" :task-params="action.params" />
        <el-alert v-else type="warning" :closable="false" title="暂不支持该任务类型的表单预填" />
      </div>

      <div class="tp-actions">
        <el-button type="primary" :loading="submitting" @click="confirm(true)">{{ isUpdate ? "保存并运行" : "创建并运行" }}</el-button>
        <el-button :loading="submitting" @click="confirm(false)">{{ isUpdate ? "保存修改" : "仅创建" }}</el-button>
        <el-button icon="VideoPlay" :loading="debugLoading" @click="debugRun">调试运行</el-button>
        <el-button text @click="dismissed = true" v-if="!dismissed">忽略</el-button>
      </div>
      <div class="tp-hint">「调试运行」不创建任务,用当前配置直接跑一次并实时看日志(数据集成会真实写入目标)。</div>
      <div v-if="dismissed" class="tp-dismissed">已忽略该建议</div>
    </template>

    <div v-else class="tp-created">
      <el-icon class="tp-ok"><CircleCheckFilled /></el-icon>
      <span>{{ isUpdate ? "已更新任务" : "已创建任务" }}「{{ name }}」{{ ranOnce ? '并触发运行' : '' }}</span>
      <el-button text type="primary" @click="goTask">去任务页查看</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, markRaw, nextTick, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, CircleCheckFilled } from '@element-plus/icons-vue'
import { addTask, updateTask, runTask, debugTask } from '@/api/task/task'
import { listTaskLog } from '@/api/task/log'
import Crontab from '@/components/Crontab'
import DataIntegrationTask from '../../../task/components/templates/DataIntegrationTask.vue'
import PythonTask from '../../../task/components/templates/PythonTask.vue'
import ShellTask from '../../../task/components/templates/ShellTask.vue'

const props = defineProps({
  action: { type: Object, required: true },
})

const TPL_MAP = {
  DataIntegrationTask: { comp: markRaw(DataIntegrationTask), label: '数据集成' },
  PythonTask: { comp: markRaw(PythonTask), label: 'Python 脚本' },
  ShellTask: { comp: markRaw(ShellTask), label: 'Shell 脚本' },
}

const tplComp = computed(() => (TPL_MAP[props.action.template_code] || {}).comp || null)
const tplLabel = computed(() => (TPL_MAP[props.action.template_code] || {}).label || props.action.template_code)

// 修改已有任务模式:action 带 task_id / kind=task_update_proposal → 走 updateTask
const isUpdate = computed(() => props.action.kind === 'task_update_proposal' || !!props.action.task_id)
const name = ref(props.action.name || '未命名任务')
const triggerType = ref(props.action.trigger_type || 1)
const crontab = ref(props.action.crontab || '')
const status = ref(props.action.status === 0 ? 0 : 1)

// Cron 表达式生成器
const openCron = ref(false)
const expression = ref('')
function handleShowCron() {
  expression.value = crontab.value
  openCron.value = true
}
function crontabFill(value) {
  crontab.value = value
}

const tplRef = ref(null)
const submitting = ref(false)
const created = ref(false)
const ranOnce = ref(false)
const dismissed = ref(false)
const router = useRouter()

// 调试运行:不落任务、不投调度,用当前表单参数直接跑一次,按 taskUuid 流式拉日志
const debugLoading = ref(false)
const debugOpen = ref(false)
const debugLogs = ref([])
const debugUuid = ref('')
const debugCursor = ref('')
const debugConsoleRef = ref(null)
let debugTimer = null

async function debugRun() {
  const r = tplRef.value && tplRef.value.genTaskParams ? tplRef.value.genTaskParams() : { error: '表单未就绪' }
  if (r.error) { ElMessage.error(r.error); return }
  debugLoading.value = true
  try {
    // 卡片模板均为内置组件(runnerType=1,无动态执行器代码)
    const res = await debugTask({ templateCode: props.action.template_code, runnerType: 1, runnerCode: null, params: r.params || {} })
    const uuid = res && res.data && res.data.taskUuid
    if (!uuid) { ElMessage.warning('调试已触发,但未取到实例ID,无法查看日志'); return }
    debugUuid.value = uuid
    debugLogs.value = []
    debugCursor.value = ''
    debugOpen.value = true
    ElMessage.success('调试已触发')
    reloadDebugLog()
    stopDebugPolling()
    debugTimer = setInterval(getDebugLog, 2000)
    // 兜底:5 分钟后自动停止轮询,避免无限拉取
    setTimeout(stopDebugPolling, 300000)
  } catch (e) {
    ElMessage.error('调试失败: ' + (e?.message || e))
  } finally {
    debugLoading.value = false
  }
}
function reloadDebugLog() {
  if (!debugUuid.value) return
  listTaskLog({ taskUuid: debugUuid.value, pageSize: 200 }).then((resp) => {
    debugLogs.value = resp.rows || []
    updateDebugCursor()
    scrollDebugBottom()
  }).catch(() => {})
}
function getDebugLog() {
  if (!debugUuid.value) return
  listTaskLog({ taskUuid: debugUuid.value, after: debugCursor.value }).then((resp) => {
    const rows = resp.rows || []
    if (rows.length) { debugLogs.value.push(...rows); updateDebugCursor(); scrollDebugBottom() }
  }).catch(() => {})
}
function updateDebugCursor() {
  const rows = debugLogs.value
  const last = rows.length ? rows[rows.length - 1] : null
  if (last && last.cursor != null) debugCursor.value = last.cursor
}
function scrollDebugBottom() {
  nextTick(() => { const el = debugConsoleRef.value; if (el) el.scrollTop = el.scrollHeight })
}
function stopDebugPolling() {
  if (debugTimer) { clearInterval(debugTimer); debugTimer = null }
}
onUnmounted(stopDebugPolling)

async function confirm(runAfter) {
  if (!name.value || !name.value.trim()) {
    ElMessage.error('请填写任务名称')
    return
  }
  if (triggerType.value === 2 && !crontab.value.trim()) {
    ElMessage.error('定时任务需填写 Cron 表达式')
    return
  }
  // 由模板组件生成并校验参数
  const r = tplRef.value && tplRef.value.genTaskParams ? tplRef.value.genTaskParams() : { error: '表单未就绪' }
  if (r.error) {
    ElMessage.error(r.error)
    return
  }
  submitting.value = true
  try {
    const model = {
      templateCode: props.action.template_code,
      name: name.value.trim(),
      params: JSON.stringify(r.params || {}),
      taskType: 1,
      triggerType: triggerType.value,
      // triggerType 必须与 crontab 一起提交:后端据此重建调度,漏传会丢掉定时
      crontab: triggerType.value === 2 ? crontab.value.trim() : '',
      status: isUpdate.value ? status.value : 1,
    }
    let taskId
    if (isUpdate.value) {
      model.id = props.action.task_id
      await updateTask(model)
      taskId = props.action.task_id
    } else {
      const res = await addTask(model)
      taskId = res && res.data && res.data.id
    }
    if (runAfter) {
      if (taskId) {
        await runTask(taskId)
        ranOnce.value = true
        ElMessage.success(isUpdate.value ? '任务已更新并触发运行' : '任务已创建并触发运行')
      } else {
        ElMessage.warning('已保存,但未取到任务ID,无法自动运行,请到任务页手动运行')
      }
    } else {
      ElMessage.success(isUpdate.value ? '任务已更新' : '任务已创建')
    }
    created.value = true
  } catch (e) {
    ElMessage.error((isUpdate.value ? '更新失败: ' : '创建失败: ') + (e?.message || e))
  } finally {
    submitting.value = false
  }
}

function goTask() {
  router.push('/task/info')
}
</script>

<style scoped>
.task-proposal {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  padding: 12px 14px;
  margin: 10px 0;
  background: var(--el-fill-color-light);
}
.task-proposal.is-created {
  background: var(--el-color-success-light-9);
  border-color: var(--el-color-success-light-5);
}
.tp-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
.tp-icon {
  color: var(--el-color-primary);
}
.tp-title {
  font-weight: 600;
}
.tp-summary {
  color: var(--el-text-color-secondary);
  font-size: 12px;
}
.tp-meta {
  margin-bottom: 4px;
}
.tp-body {
  border-top: 1px dashed var(--el-border-color);
  padding-top: 10px;
  margin-bottom: 10px;
}
.tp-actions {
  display: flex;
  gap: 8px;
}
.tp-dismissed {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-top: 6px;
}
.tp-created {
  display: flex;
  align-items: center;
  gap: 8px;
}
.tp-ok {
  color: var(--el-color-success);
  font-size: 18px;
}
.tp-hint {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-top: 6px;
}
.tp-log-console {
  height: 380px;
  overflow-y: auto;
  background: #1e1e1e;
  border-radius: 6px;
  padding: 10px 12px;
  font-family: Consolas, Menlo, monospace;
  font-size: 12px;
  line-height: 1.6;
}
.tp-log-line {
  display: flex;
  gap: 8px;
  color: #d4d4d4;
  white-space: pre-wrap;
  word-break: break-word;
}
.tp-log-time { color: #6a9955; flex-shrink: 0; }
.tp-log-level { color: #569cd6; flex-shrink: 0; width: 46px; }
.tp-log-content { flex: 1; }
.tp-log-line.lvl-ERROR .tp-log-content { color: #f48771; }
.tp-log-line.lvl-WARNING .tp-log-content, .tp-log-line.lvl-WARN .tp-log-content { color: #dcdcaa; }
.tp-log-tip {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin-top: 8px;
}
</style>
