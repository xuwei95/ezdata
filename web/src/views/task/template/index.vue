<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="模板名称" prop="name">
        <el-input v-model="queryParams.name" placeholder="请输入模板名称" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="模板编码" prop="code">
        <el-input v-model="queryParams.code" placeholder="请输入模板编码" clearable style="width: 200px" @keyup.enter="handleQuery" />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-select v-model="queryParams.status" placeholder="模板状态" clearable style="width: 160px">
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
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['task:template:add']">新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button type="danger" plain icon="Delete" :disabled="multiple" @click="handleDelete" v-hasPermi="['task:template:remove']">删除</el-button>
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="templateList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="模板名称" align="center" prop="name" :show-overflow-tooltip="true" />
      <el-table-column label="模板编码" align="center" prop="code" :show-overflow-tooltip="true" />
      <el-table-column label="表单类型" align="center" prop="type">
        <template #default="scope">
          <el-tag :type="scope.row.type === 2 ? 'warning' : ''">{{ scope.row.type === 2 ? '动态配置' : '内置组件' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="执行器类型" align="center" prop="runnerType">
        <template #default="scope">
          <el-tag :type="scope.row.runnerType === 2 ? 'danger' : 'success'">{{ scope.row.runnerType === 2 ? '动态代码' : '内置runner' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="内置" align="center" prop="builtIn">
        <template #default="scope">
          <el-tag v-if="scope.row.builtIn === 1" type="info">内置</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" align="center" prop="status">
        <template #default="scope">
          <el-tag :type="scope.row.status === 1 ? 'success' : 'danger'">{{ scope.row.status === 1 ? '启用' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="备注" align="center" prop="remark" :show-overflow-tooltip="true" />
      <el-table-column label="操作" align="center" width="160" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['task:template:edit']">修改</el-button>
          <el-button link type="danger" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['task:template:remove']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <pagination v-show="total > 0" :total="total" v-model:page="queryParams.pageNum" v-model:limit="queryParams.pageSize" @pagination="getList" />

    <el-dialog :title="title" v-model="open" fullscreen append-to-body class="template-fullscreen-dialog">
      <el-form ref="templateRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="模板名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模板名称" />
        </el-form-item>
        <el-form-item label="模板编码" prop="code">
          <el-input v-model="form.code" placeholder="如 MyTask(唯一)" :disabled="form.builtIn === 1" />
        </el-form-item>
        <el-form-item label="表单类型" prop="type">
          <el-radio-group v-model="form.type">
            <el-radio :value="1">内置组件</el-radio>
            <el-radio :value="2">动态配置</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="执行器类型" prop="runnerType">
          <el-radio-group v-model="form.runnerType" :disabled="form.builtIn === 1" @change="onRunnerTypeChange">
            <el-radio :value="1">内置runner</el-radio>
            <el-radio :value="2">动态代码</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="动态代码" prop="runnerCode" v-if="form.runnerType === 2">
          <code-editor v-model="form.runnerCode" language="python" height="240px" placeholder="需定义 run(params, logger) 函数" />
        </el-form-item>
        <!-- 动态配置(type=2)：可视化低代码设计参数表单；内置组件(type=1)：指定前端组件 -->
        <el-form-item v-if="form.type === 2" label="参数表单设计" prop="params">
          <schema-designer v-model="form.params" />
        </el-form-item>
        <el-form-item v-else label="前端组件" prop="component">
          <el-input v-model="form.component" placeholder="内置组件路径/名称，任务参数由该内置组件处理" />
          <div class="form-tip">内置组件类型的模板由固定前端组件处理参数，任务表单不再动态配置</div>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio :value="1">启用</el-radio>
            <el-radio :value="0">停用</el-radio>
          </el-radio-group>
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
  </div>
</template>

<script setup name="TaskTemplate">
import { listTemplate, getTemplate, addTemplate, updateTemplate, delTemplate } from '@/api/task/template'
import SchemaDesigner from '@/views/task/components/SchemaDesigner.vue'
import CodeEditor from '@/components/CodeEditor'

const { proxy } = getCurrentInstance()

const templateList = ref([])
const open = ref(false)
const loading = ref(true)
const showSearch = ref(true)
const ids = ref([])
const multiple = ref(true)
const total = ref(0)
const title = ref('')

const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    name: undefined,
    code: undefined,
    status: undefined
  },
  rules: {
    name: [{ required: true, message: '模板名称不能为空', trigger: 'blur' }],
    code: [{ required: true, message: '模板编码不能为空', trigger: 'blur' }],
    params: [{ validator: validateJson, trigger: 'blur' }]
  }
})

const { queryParams, form, rules } = toRefs(data)

function validateJson(rule, value, callback) {
  if (!value) return callback()
  try {
    const parsed = JSON.parse(value)
    if (!Array.isArray(parsed)) return callback(new Error('参数Schema须为JSON数组'))
    callback()
  } catch (e) {
    callback(new Error('参数Schema不是合法JSON'))
  }
}

function getList() {
  loading.value = true
  listTemplate(queryParams.value).then(response => {
    templateList.value = response.rows
    total.value = response.total
    loading.value = false
  })
}

function cancel() {
  open.value = false
  reset()
}

function reset() {
  form.value = {
    id: undefined,
    name: undefined,
    code: undefined,
    type: 2,
    runnerType: 1,
    runnerCode: undefined,
    component: undefined,
    params: undefined,
    builtIn: 0,
    status: 1,
    remark: undefined
  }
  proxy.resetForm('templateRef')
}

// 动态代码默认模板(选择“动态代码”且当前为空时自动填充)
const DEFAULT_RUNNER_CODE = `def run(params, logger):
    logger.info("任务参数: " + str(params))
    return "执行成功"`

function onRunnerTypeChange(val) {
  if (val === 2 && !form.value.runnerCode) {
    form.value.runnerCode = DEFAULT_RUNNER_CODE
  }
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
  open.value = true
  title.value = '新增任务模板'
}

function handleUpdate(row) {
  reset()
  const templateId = row.id || ids.value
  getTemplate(templateId).then(response => {
    form.value = response.data
    open.value = true
    title.value = '修改任务模板'
  })
}

function submitForm() {
  proxy.$refs['templateRef'].validate(valid => {
    if (valid) {
      if (form.value.id != undefined) {
        updateTemplate(form.value).then(() => {
          proxy.$modal.msgSuccess('修改成功')
          open.value = false
          getList()
        })
      } else {
        addTemplate(form.value).then(() => {
          proxy.$modal.msgSuccess('新增成功')
          open.value = false
          getList()
        })
      }
    }
  })
}

function handleDelete(row) {
  const templateIds = row.id || ids.value.join(',')
  proxy.$modal.confirm('是否确认删除选中的任务模板？').then(function () {
    return delTemplate(templateIds)
  }).then(() => {
    getList()
    proxy.$modal.msgSuccess('删除成功')
  }).catch(() => {})
}

getList()
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
.code-area :deep(textarea) {
  font-family: Consolas, Monaco, 'Courier New', monospace;
}
</style>
