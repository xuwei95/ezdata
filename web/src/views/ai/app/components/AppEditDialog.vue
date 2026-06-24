<template>
  <el-dialog
    :title="form.appId ? '编辑应用' : '新建应用'"
    v-model="visible"
    width="760px"
    append-to-body
    @open="onOpen"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="92px">
      <el-row :gutter="12">
        <el-col :span="12">
          <el-form-item label="应用名称" prop="name">
            <el-input v-model="form.name" placeholder="如:数据分析助手" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态">
            <el-radio-group v-model="form.status">
              <el-radio value="0">发布</el-radio>
              <el-radio value="1">草稿</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
        <el-col :span="24">
          <el-form-item label="应用描述">
            <el-input v-model="form.description" placeholder="一句话介绍这个应用" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">人设与开场</el-divider>
      <el-form-item label="系统提示词">
        <div style="width: 100%">
          <el-input v-model="cfg.prompt" type="textarea" :rows="5" placeholder="设定应用的角色/技能/限制(可点右侧 AI 生成)" />
          <div style="margin-top: 6px; display: flex; gap: 8px">
            <el-input v-model="genReq" placeholder="一句话描述应用定位,AI 帮你写提示词" size="small" />
            <el-button size="small" type="primary" :loading="generating" @click="doGenerate">AI 生成</el-button>
          </div>
        </div>
      </el-form-item>
      <el-form-item label="开场白">
        <el-input v-model="cfg.prologue" type="textarea" :rows="2" placeholder="进入对话时的欢迎语" />
      </el-form-item>
      <el-form-item label="预设问题">
        <div style="width: 100%">
          <div v-for="(q, i) in cfg.presetQuestions" :key="i" style="display: flex; gap: 8px; margin-bottom: 6px">
            <el-input v-model="cfg.presetQuestions[i]" placeholder="点击即发送的示例问题" />
            <el-button icon="Delete" @click="cfg.presetQuestions.splice(i, 1)" />
          </div>
          <el-button size="small" icon="Plus" @click="cfg.presetQuestions.push('')">添加问题</el-button>
        </div>
      </el-form-item>
      <el-form-item label="快捷指令">
        <div style="width: 100%">
          <div v-for="(c, i) in cfg.quickCommands" :key="i" style="display: flex; gap: 8px; margin-bottom: 6px">
            <el-input v-model="c.name" placeholder="按钮名" style="width: 140px" />
            <el-input v-model="c.content" placeholder="点击后发送的指令内容" />
            <el-button icon="Delete" @click="cfg.quickCommands.splice(i, 1)" />
          </div>
          <el-button size="small" icon="Plus" @click="cfg.quickCommands.push({ name: '', content: '' })"
            >添加指令</el-button
          >
        </div>
      </el-form-item>

      <el-divider content-position="left">能力绑定</el-divider>
      <el-form-item label="工具">
        <el-select v-model="cfg.toolIds" multiple filterable clearable placeholder="选择应用可用的工具(MCP/内置)" style="width: 100%">
          <el-option
            v-for="t in toolOptions"
            :key="t.toolId"
            :label="`${t.name} (${t.toolType === 'builtin' ? '内置' : 'MCP'})`"
            :value="t.toolId"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="知识库">
        <el-select v-model="cfg.datasetIds" multiple filterable clearable placeholder="选择应用检索的知识库" style="width: 100%">
          <el-option v-for="d in datasetOptions" :key="d.id" :label="d.name" :value="d.id" />
        </el-select>
      </el-form-item>

      <el-divider content-position="left">模型参数</el-divider>
      <el-row :gutter="12">
        <el-col :span="10">
          <el-form-item label="模型">
            <el-select v-model="cfg.model.modelId" placeholder="模型" style="width: 100%">
              <el-option v-for="m in modelOptions" :key="m.modelId" :label="m.modelName || m.modelCode" :value="m.modelId" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="7">
          <el-form-item label="温度">
            <el-input-number v-model="cfg.model.temperature" :min="0" :max="2" :step="0.1" :precision="1" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="7">
          <el-form-item label="最大输出">
            <el-input-number v-model="cfg.model.maxTokens" :min="0" :step="1000" style="width: 100%" placeholder="留空用默认" />
          </el-form-item>
        </el-col>
      </el-row>

      <template v-if="form.appId">
        <el-divider content-position="left">对外 API Key</el-divider>
        <div style="padding: 0 8px">
          <el-button size="small" type="primary" icon="Plus" :loading="tokenLoading" @click="genToken">生成 API Key</el-button>
          <el-table :data="tokens" size="small" style="margin-top: 8px" empty-text="暂无 API Key">
            <el-table-column label="名称" prop="name" width="120" show-overflow-tooltip />
            <el-table-column label="API Key" prop="apiKey" show-overflow-tooltip>
              <template #default="{ row }">
                <span style="font-family: monospace">{{ row.apiKey }}</span>
                <el-button link type="primary" size="small" @click="copy(row.apiKey)">复制</el-button>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="90">
              <template #default="{ row }">
                <el-switch
                  v-model="row.status"
                  active-value="0"
                  inactive-value="1"
                  @change="setAppTokenStatus({ tokenId: row.tokenId, status: row.status }).then(loadTokens)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="70">
              <template #default="{ row }">
                <el-button link type="danger" size="small" @click="removeToken(row.tokenId)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 6px; color: var(--el-text-color-secondary); font-size: 12px">
            调用:POST {{ apiBase }}/ai/app/api/chat,Header「X-API-Key: 上面的key」,body {"message":"你好"}
          </div>
        </div>
      </template>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="saving" @click="submit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup name="AppEditDialog">
import { reactive, ref } from "vue";
import { ElMessage } from "element-plus";
import {
  getApp,
  addApp,
  updateApp,
  generatePrompt,
  listAppTokens,
  createAppToken,
  setAppTokenStatus,
  delAppToken,
} from "@/api/ai/app";
import { listTool } from "@/api/ai/tool";
import { listModelAll } from "@/api/ai/model";
import { listDataset } from "@/api/rag";

const visible = defineModel("visible", { type: Boolean, default: false });
const props = defineProps({ appId: { type: [Number, String], default: null } });
const emit = defineEmits(["success"]);

const formRef = ref(null);
const saving = ref(false);
const generating = ref(false);
const genReq = ref("");
const toolOptions = ref([]);
const modelOptions = ref([]);
const datasetOptions = ref([]);
const tokens = ref([]);
const tokenLoading = ref(false);
const apiBase = import.meta.env.VITE_APP_BASE_API || "";

function loadTokens() {
  if (!form.appId) return;
  listAppTokens(form.appId).then((res) => (tokens.value = res.data || []));
}
function genToken() {
  tokenLoading.value = true;
  createAppToken({ appId: form.appId, name: "key" + (tokens.value.length + 1) })
    .then(() => loadTokens())
    .finally(() => (tokenLoading.value = false));
}
function removeToken(id) {
  delAppToken(id).then(() => loadTokens());
}
function copy(text) {
  navigator.clipboard?.writeText(text);
  ElMessage.success("已复制");
}

const defaultCfg = () => ({
  prompt: "",
  prologue: "",
  presetQuestions: [],
  quickCommands: [],
  toolIds: [],
  datasetIds: [],
  model: { modelId: 0, temperature: null, maxTokens: null },
});

const form = reactive({ appId: null, name: "", description: "", status: "0" });
const cfg = reactive(defaultCfg());
const rules = { name: [{ required: true, message: "应用名称不能为空", trigger: "blur" }] };

function resetForm() {
  Object.assign(form, { appId: null, name: "", description: "", status: "0" });
  Object.assign(cfg, defaultCfg());
  genReq.value = "";
}

async function loadOptions() {
  const [tools, models, datasets] = await Promise.all([
    listTool({ pageNum: 1, pageSize: 200 }),
    listModelAll(),
    listDataset({ pageNum: 1, pageSize: 200 }),
  ]);
  toolOptions.value = tools.rows || [];
  modelOptions.value = models.data || [];
  datasetOptions.value = datasets.rows || [];
}

async function onOpen() {
  resetForm();
  await loadOptions();
  if (props.appId) {
    const res = await getApp(props.appId);
    const d = res.data || {};
    Object.assign(form, { appId: d.appId, name: d.name, description: d.description, status: d.status || "0" });
    Object.assign(cfg, { ...defaultCfg(), ...(d.config || {}) });
    if (!cfg.model) cfg.model = { modelId: 0 };
    loadTokens();
  } else {
    tokens.value = [];
  }
}

function doGenerate() {
  if (!genReq.value.trim()) return ElMessage.warning("先填一句话应用定位");
  generating.value = true;
  generatePrompt({ requirement: genReq.value, modelId: cfg.model.modelId || 0 })
    .then((res) => {
      cfg.prompt = res.data?.prompt || cfg.prompt;
      ElMessage.success("已生成,可继续编辑");
    })
    .finally(() => (generating.value = false));
}

function submit() {
  formRef.value.validate((valid) => {
    if (!valid) return;
    saving.value = true;
    const payload = {
      appId: form.appId || undefined,
      name: form.name,
      description: form.description,
      status: form.status,
      config: {
        ...cfg,
        presetQuestions: cfg.presetQuestions.filter((q) => q && q.trim()),
        quickCommands: cfg.quickCommands.filter((c) => c.name && c.content),
      },
    };
    const action = form.appId ? updateApp : addApp;
    action(payload)
      .then(() => {
        ElMessage.success(form.appId ? "修改成功" : "新增成功");
        visible.value = false;
        emit("success");
      })
      .finally(() => (saving.value = false));
  });
}
</script>
