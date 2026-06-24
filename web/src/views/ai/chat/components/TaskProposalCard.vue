<template>
  <div class="task-proposal" :class="{ 'is-created': created }">
    <div class="tp-head">
      <el-icon class="tp-icon"><Document /></el-icon>
      <span class="tp-title">AI 任务建议</span>
      <el-tag size="small" type="info" effect="plain">{{ tplLabel }}</el-tag>
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
      </el-form>

      <el-dialog title="Cron表达式生成器" v-model="openCron" append-to-body destroy-on-close>
        <crontab @hide="openCron = false" @fill="crontabFill" :expression="expression"></crontab>
      </el-dialog>

      <div class="tp-body">
        <component :is="tplComp" v-if="tplComp" ref="tplRef" :task-params="action.params" />
        <el-alert v-else type="warning" :closable="false" title="暂不支持该任务类型的表单预填" />
      </div>

      <div class="tp-actions">
        <el-button type="primary" :loading="submitting" @click="confirm(true)">创建并运行</el-button>
        <el-button :loading="submitting" @click="confirm(false)">仅创建</el-button>
        <el-button text @click="dismissed = true" v-if="!dismissed">忽略</el-button>
      </div>
      <div v-if="dismissed" class="tp-dismissed">已忽略该建议</div>
    </template>

    <div v-else class="tp-created">
      <el-icon class="tp-ok"><CircleCheckFilled /></el-icon>
      <span>已创建任务「{{ name }}」{{ ranOnce ? '并触发运行' : '' }}</span>
      <el-button text type="primary" @click="goTask">去任务页查看</el-button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, markRaw } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Document, CircleCheckFilled } from '@element-plus/icons-vue'
import { addTask, runTask } from '@/api/task/task'
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

const name = ref(props.action.name || '未命名任务')
const triggerType = ref(props.action.trigger_type || 1)
const crontab = ref(props.action.crontab || '')

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
      crontab: triggerType.value === 2 ? crontab.value.trim() : '',
      status: 1,
    }
    const res = await addTask(model)
    const taskId = res && res.data && res.data.id
    if (runAfter) {
      if (taskId) {
        await runTask(taskId)
        ranOnce.value = true
        ElMessage.success('任务已创建并触发运行')
      } else {
        ElMessage.warning('任务已创建,但未取到任务ID,无法自动运行,请到任务页手动运行')
      }
    } else {
      ElMessage.success('任务已创建')
    }
    created.value = true
  } catch (e) {
    ElMessage.error('创建失败: ' + (e?.message || e))
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
</style>
