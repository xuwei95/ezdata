<template>
  <div class="app-edit">
    <!-- 左:配置/调试 -->
    <div class="ae-left">
      <div class="ae-left-head">
        <el-button link icon="ArrowLeft" @click="goBack">应用广场</el-button>
        <span class="ae-title">{{ form.appId ? "编辑应用" : "新建应用" }}</span>
        <el-button type="primary" size="small" :loading="saving" @click="save">保存</el-button>
      </div>
      <el-scrollbar class="ae-left-body">
        <el-form :model="form" label-width="86px">
          <el-row :gutter="12">
            <el-col :span="14">
              <el-form-item label="应用名称" required>
                <el-input v-model="form.name" placeholder="如:数据分析助手" />
              </el-form-item>
            </el-col>
            <el-col :span="10">
              <el-form-item label="状态">
                <el-radio-group v-model="form.status">
                  <el-radio value="0">发布</el-radio>
                  <el-radio value="1">草稿</el-radio>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :span="24">
              <el-form-item label="应用描述"><el-input v-model="form.description" placeholder="一句话介绍" /></el-form-item>
            </el-col>
          </el-row>

          <el-divider content-position="left">人设与开场</el-divider>
          <el-form-item label="系统提示词">
            <div style="width: 100%">
              <el-input v-model="cfg.prompt" type="textarea" :rows="6" placeholder="设定角色/技能/限制(可点 AI 生成)" />
              <div style="margin-top: 6px; display: flex; gap: 8px">
                <el-input v-model="genReq" placeholder="一句话应用定位,AI 帮你写提示词" size="small" />
                <el-button size="small" type="primary" :loading="generating" @click="doGenerate">AI 生成</el-button>
              </div>
            </div>
          </el-form-item>
          <el-form-item label="开场白"><el-input v-model="cfg.prologue" type="textarea" :rows="2" placeholder="进入对话的欢迎语" /></el-form-item>
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
                <el-input v-model="c.name" placeholder="按钮名" style="width: 130px" />
                <el-input v-model="c.content" placeholder="点击后发送的指令" />
                <el-button icon="Delete" @click="cfg.quickCommands.splice(i, 1)" />
              </div>
              <el-button size="small" icon="Plus" @click="cfg.quickCommands.push({ name: '', content: '' })">添加指令</el-button>
            </div>
          </el-form-item>

          <el-divider content-position="left">能力绑定</el-divider>
          <el-form-item label="工具">
            <el-select v-model="cfg.toolIds" multiple filterable clearable placeholder="选择可用工具" style="width: 100%">
              <el-option
                v-for="t in toolOptions"
                :key="t.toolId"
                :label="`${t.name} (${t.toolType === 'builtin' ? '内置' : 'MCP'})`"
                :value="t.toolId"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="知识库">
            <el-select v-model="cfg.datasetIds" multiple filterable clearable placeholder="选择检索的知识库" style="width: 100%">
              <el-option v-for="d in datasetOptions" :key="d.id" :label="d.name" :value="d.id" />
            </el-select>
          </el-form-item>

          <el-divider content-position="left">模型参数</el-divider>
          <el-row :gutter="12">
            <el-col :span="10">
              <el-form-item label="模型">
                <el-select v-model="cfg.model.modelId" style="width: 100%">
                  <el-option v-for="m in modelOptions" :key="m.modelId" :label="m.modelName || m.modelCode" :value="m.modelId" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="7">
              <el-form-item label="温度"><el-input-number v-model="cfg.model.temperature" :min="0" :max="2" :step="0.1" :precision="1" style="width: 100%" /></el-form-item>
            </el-col>
            <el-col :span="7">
              <el-form-item label="最大输出"><el-input-number v-model="cfg.model.maxTokens" :min="0" :step="1000" style="width: 100%" placeholder="默认" /></el-form-item>
            </el-col>
          </el-row>

          <template v-if="form.appId">
            <el-divider content-position="left">对外 API Key</el-divider>
            <el-button size="small" type="primary" icon="Plus" :loading="tokenLoading" @click="genToken">生成 API Key</el-button>
            <el-table :data="tokens" size="small" style="margin-top: 8px" empty-text="暂无 API Key">
              <el-table-column label="名称" prop="name" width="110" show-overflow-tooltip />
              <el-table-column label="API Key" prop="token" show-overflow-tooltip>
                <template #default="{ row }">
                  <span style="font-family: monospace; font-size: 12px">{{ row.token }}</span>
                  <el-button link type="primary" size="small" @click="copy(row.token)">复制</el-button>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="60">
                <template #default="{ row }"><el-button link type="danger" size="small" @click="removeToken(row.id)">删除</el-button></template>
              </el-table-column>
            </el-table>
            <div class="ae-api-hint">POST {{ apiBase }}/ai/app/api/chat,Header「X-API-Key: 上面的 key」,body {"message":"你好"}</div>
          </template>
        </el-form>
      </el-scrollbar>
    </div>

    <!-- 右:实时调试对话 -->
    <div class="ae-right">
      <div class="ae-right-head">
        <span><el-icon><ChatLineRound /></el-icon> 调试对话(用当前配置,免保存)</span>
        <el-button link icon="Refresh" @click="newChat">清空</el-button>
      </div>
      <div ref="historyRef" class="ae-history">
        <div v-if="messages.length === 0" class="ae-empty">
          {{ cfg.prologue || "在右侧输入消息,实时测试当前配置的效果" }}
          <div v-if="cfg.presetQuestions.filter(Boolean).length" class="ae-presets">
            <el-tag v-for="(q, i) in cfg.presetQuestions.filter(Boolean)" :key="i" effect="plain" class="ae-preset" @click="sendDebug(q)">{{ q }}</el-tag>
          </div>
        </div>
        <div v-for="(m, idx) in messages" :key="idx" class="ae-msg" :class="m.role">
          <div v-if="m.role === 'user'" class="ae-user">{{ m.content }}</div>
          <AiMessage v-else :content="m.content" :reasoning-content="m.reasoningContent" :blocks="m.blocks" :loading="loading && idx === messages.length - 1" />
        </div>
      </div>
      <div class="ae-input">
        <div v-if="cfg.quickCommands.filter((c) => c.name && c.content).length" class="ae-quick">
          <el-button v-for="(c, i) in cfg.quickCommands.filter((c) => c.name && c.content)" :key="i" size="small" round @click="sendDebug(c.content)">{{ c.name }}</el-button>
        </div>
        <div class="ae-input-row">
          <el-input v-model="input" type="textarea" :autosize="{ minRows: 1, maxRows: 4 }" placeholder="Enter 发送" @keydown.enter.exact.prevent="sendDebug()" />
          <el-button type="primary" :loading="loading" icon="Promotion" @click="sendDebug()">发送</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup name="AiAppEdit">
import { reactive, ref, nextTick, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import AiMessage from "../chat/components/AiMessage.vue";
import { getApp, addApp, updateApp, generatePrompt } from "@/api/ai/app";
import { listTool } from "@/api/ai/tool";
import { listModelAll } from "@/api/ai/model";
import { listDataset } from "@/api/rag";
import { listToken, addToken, delToken } from "@/api/apitoken/token";
import { getToken } from "@/utils/auth";
import { v4 as uuidv4 } from "uuid";

const route = useRoute();
const router = useRouter();
const apiBase = import.meta.env.VITE_APP_BASE_API || "";

const form = reactive({ appId: route.params.appId ? Number(route.params.appId) : null, name: "", description: "", status: "0" });
const cfg = reactive({ prompt: "", prologue: "", presetQuestions: [], quickCommands: [], toolIds: [], datasetIds: [], model: { modelId: 0, temperature: null, maxTokens: null } });
const genReq = ref("");
const saving = ref(false);
const generating = ref(false);
const toolOptions = ref([]);
const modelOptions = ref([]);
const datasetOptions = ref([]);
const tokens = ref([]);
const tokenLoading = ref(false);

// 右侧调试对话
const messages = ref([]);
const input = ref("");
const loading = ref(false);
const sessionId = ref(uuidv4());
const historyRef = ref(null);

onMounted(async () => {
  const [tools, models, datasets] = await Promise.all([
    listTool({ pageNum: 1, pageSize: 200 }),
    listModelAll(),
    listDataset({ pageNum: 1, pageSize: 200 }),
  ]);
  toolOptions.value = tools.rows || [];
  modelOptions.value = models.data || [];
  datasetOptions.value = datasets.rows || [];
  if (form.appId) {
    const res = await getApp(form.appId);
    const d = res.data || {};
    Object.assign(form, { name: d.name, description: d.description, status: d.status || "0" });
    Object.assign(cfg, { ...cfg, ...(d.config || {}) });
    if (!cfg.model) cfg.model = { modelId: 0 };
    loadTokens();
  }
});

function goBack() {
  router.push("/ai/app");
}
function buildConfig() {
  return {
    ...cfg,
    presetQuestions: cfg.presetQuestions.filter((q) => q && q.trim()),
    quickCommands: cfg.quickCommands.filter((c) => c.name && c.content),
  };
}
function save() {
  if (!form.name.trim()) return ElMessage.error("请填写应用名称");
  saving.value = true;
  const payload = { appId: form.appId || undefined, name: form.name, description: form.description, status: form.status, config: buildConfig() };
  const action = form.appId ? updateApp : addApp;
  action(payload)
    .then((res) => {
      ElMessage.success("保存成功");
      if (!form.appId && res.data?.appId) {
        form.appId = res.data.appId;
        router.replace("/ai/app/edit/" + res.data.appId);
        loadTokens();
      }
    })
    .finally(() => (saving.value = false));
}
function doGenerate() {
  if (!genReq.value.trim()) return ElMessage.warning("先填一句话应用定位");
  generating.value = true;
  generatePrompt({ requirement: genReq.value, modelId: cfg.model.modelId || 0 })
    .then((res) => {
      cfg.prompt = res.data?.prompt || cfg.prompt;
      ElMessage.success("已生成");
    })
    .finally(() => (generating.value = false));
}

// APIKey(复用通用 api_token:token_type=ai_app, ref_id=appId)
function loadTokens() {
  if (!form.appId) return;
  listToken({ tokenType: "ai_app", refId: String(form.appId), pageNum: 1, pageSize: 50 }).then((res) => (tokens.value = res.rows || []));
}
function genToken() {
  tokenLoading.value = true;
  addToken({ tokenType: "ai_app", refId: String(form.appId), name: "key" + (tokens.value.length + 1) })
    .then(() => loadTokens())
    .finally(() => (tokenLoading.value = false));
}
function removeToken(id) {
  delToken(id).then(() => loadTokens());
}
function copy(t) {
  navigator.clipboard?.writeText(t);
  ElMessage.success("已复制");
}

function newChat() {
  if (loading.value) return;
  messages.value = [];
  sessionId.value = uuidv4();
}
function scrollBottom() {
  nextTick(() => historyRef.value && (historyRef.value.scrollTop = historyRef.value.scrollHeight));
}
async function sendDebug(preset) {
  const text = (preset !== undefined ? preset : input.value).trim();
  if (!text || loading.value) return;
  input.value = "";
  messages.value.push({ role: "user", content: text });
  const ai = messages.value.push({ role: "assistant", content: "", reasoningContent: "", blocks: [] }) - 1;
  loading.value = true;
  scrollBottom();
  try {
    const resp = await fetch(apiBase + "/ai/app/debug", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + getToken() },
      body: JSON.stringify({ config: buildConfig(), message: text, sessionId: sessionId.value }),
    });
    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    let c = "";
    let r = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        let d;
        try {
          d = JSON.parse(line);
        } catch (e) {
          continue;
        }
        const m = messages.value[ai];
        if (d.type === "content") {
          c += d.content;
          m.content = c;
          const last = m.blocks[m.blocks.length - 1];
          if (last && last.type === "text") last.text += d.content;
          else m.blocks.push({ type: "text", text: d.content });
        } else if (d.type === "reasoning") {
          r += d.content;
          m.reasoningContent = r;
        } else if (d.type === "meta") {
          sessionId.value = d.session_id;
        } else if (d.type === "artifact") {
          m.blocks.push({ type: "artifact", artifact: d.artifact });
        } else if (d.type === "ui_action") {
          m.blocks.push({ type: "ui_action", action: d.action });
        } else if (d.type === "tool") {
          if (d.phase === "start") m.blocks.push({ type: "tool", id: d.id, name: d.name, args: d.args, status: "running" });
          else {
            const s = m.blocks.find((b) => b.type === "tool" && b.id === d.id);
            if (s) {
              s.status = d.phase === "error" ? "error" : "done";
              s.result = d.result;
              s.error = d.error;
            }
          }
        } else if (d.type === "error") {
          ElMessage.error(d.error);
        }
        scrollBottom();
      }
    }
  } catch (e) {
    ElMessage.error("调试失败: " + (e?.message || e));
  } finally {
    loading.value = false;
    scrollBottom();
  }
}
</script>

<style scoped lang="scss">
.app-edit {
  height: calc(100vh - 84px);
  display: flex;
  background: var(--el-bg-color-page);
}
.ae-left {
  width: 46%;
  min-width: 420px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
}
.ae-left-head,
.ae-right-head {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  border-bottom: 1px solid var(--el-border-color);
  .ae-title {
    font-weight: 600;
  }
}
.ae-left-body {
  flex: 1;
  padding: 16px;
}
.ae-api-hint {
  margin-top: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.ae-right {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.ae-right-head {
  background: var(--el-bg-color);
}
.ae-history {
  flex: 1;
  overflow-y: auto;
  padding: 18px;
  background: radial-gradient(900px 300px at 50% -10%, var(--el-color-primary-light-9), transparent 60%), var(--el-bg-color-page);
}
.ae-empty {
  max-width: 600px;
  margin: 40px auto;
  text-align: center;
  color: var(--el-text-color-secondary);
  .ae-presets {
    margin-top: 14px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
  }
  .ae-preset {
    cursor: pointer;
  }
}
.ae-msg {
  margin-bottom: 14px;
  &.user {
    display: flex;
    justify-content: flex-end;
  }
}
.ae-user {
  background: var(--el-color-primary);
  color: #fff;
  padding: 9px 13px;
  border-radius: 12px 12px 2px 12px;
  max-width: 80%;
  white-space: pre-wrap;
  word-break: break-word;
}
.ae-input {
  border-top: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  padding: 10px 16px;
  .ae-quick {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 8px;
  }
  .ae-input-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
  }
}
</style>
