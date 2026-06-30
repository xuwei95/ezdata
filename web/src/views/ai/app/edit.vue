<template>
  <div class="app-edit">
    <!-- 左:配置/调试 -->
    <div class="ae-left">
      <div class="ae-left-head">
        <el-button link icon="ArrowLeft" @click="goBack">应用广场</el-button>
        <span class="ae-title">{{ readonly ? "查看应用" : form.appId ? "编辑应用" : "新建应用" }}</span>
        <el-button v-if="readonly" type="primary" size="small" icon="Edit" @click="readonly = false" v-hasPermi="['ai:app:edit']">编辑</el-button>
        <el-button v-else type="primary" size="small" :loading="saving" @click="save">保存</el-button>
      </div>
      <el-scrollbar class="ae-left-body">
        <el-form :model="form" label-width="86px" :disabled="readonly">
          <el-form-item label="应用名称" required>
            <el-input v-model="form.name" placeholder="如:数据分析助手" />
          </el-form-item>
          <el-form-item label="应用描述">
            <el-input v-model="form.description" placeholder="一句话介绍" />
          </el-form-item>
          <el-form-item label="模型">
            <div style="display: flex; gap: 8px; width: 100%">
              <el-select v-model="cfg.model.modelId" style="flex: 1" placeholder="选择模型">
                <el-option v-for="m in modelOptions" :key="m.modelId" :label="m.modelName || m.modelCode" :value="m.modelId" />
              </el-select>
              <el-popover trigger="click" :width="270" placement="bottom-end">
                <template #reference>
                  <el-button icon="Setting">设置</el-button>
                </template>
                <el-form label-width="72px" style="margin: 0" :disabled="readonly">
                  <el-form-item label="温度" style="margin-bottom: 10px">
                    <el-input-number v-model="cfg.model.temperature" :min="0" :max="2" :step="0.1" :precision="1" style="width: 100%" placeholder="默认" />
                  </el-form-item>
                  <el-form-item label="最大输出" style="margin-bottom: 0">
                    <el-input-number v-model="cfg.model.maxTokens" :min="0" :step="1000" style="width: 100%" placeholder="默认" />
                  </el-form-item>
                </el-form>
              </el-popover>
            </div>
          </el-form-item>

          <el-divider content-position="left">人设与开场</el-divider>
          <el-form-item label="系统提示词">
            <div style="width: 100%">
              <el-input v-model="cfg.prompt" type="textarea" :rows="6" placeholder="设定角色/技能/限制(可点 AI 生成)" />
              <div v-if="!readonly" style="margin-top: 6px">
                <el-button size="small" type="primary" icon="MagicStick" @click="pgVisible = true">AI 生成提示词</el-button>
              </div>
            </div>
          </el-form-item>
          <el-form-item label="开场白"><el-input v-model="cfg.prologue" type="textarea" :rows="2" placeholder="进入对话的欢迎语" /></el-form-item>
          <el-form-item label="预设问题">
            <div style="width: 100%">
              <div v-for="(q, i) in cfg.presetQuestions" :key="i" style="display: flex; gap: 8px; margin-bottom: 6px">
                <el-input v-model="cfg.presetQuestions[i]" placeholder="点击即发送的示例问题" />
                <el-button v-if="!readonly" icon="Delete" @click="cfg.presetQuestions.splice(i, 1)" />
              </div>
              <el-button v-if="!readonly" size="small" icon="Plus" @click="cfg.presetQuestions.push('')">添加问题</el-button>
            </div>
          </el-form-item>
          <el-form-item label="快捷指令">
            <div style="width: 100%">
              <div v-for="(c, i) in cfg.quickCommands" :key="i" style="display: flex; gap: 8px; margin-bottom: 6px">
                <el-input v-model="c.name" placeholder="按钮名" style="width: 130px" />
                <el-input v-model="c.content" placeholder="点击后发送的指令" />
                <el-button v-if="!readonly" icon="Delete" @click="cfg.quickCommands.splice(i, 1)" />
              </div>
              <el-button v-if="!readonly" size="small" icon="Plus" @click="cfg.quickCommands.push({ name: '', content: '' })">添加指令</el-button>
            </div>
          </el-form-item>

          <el-divider content-position="left">能力绑定</el-divider>
          <el-form-item label="数据分析">
            <el-select v-model="cfg.datasourceCodes" multiple filterable clearable placeholder="选择可分析的数据源(不选则不启用数据分析)" style="width: 100%">
              <el-option v-for="s in datasourceOptions" :key="s.code" :label="`${s.name} (${s.sourceType})`" :value="s.code" />
            </el-select>
            <div style="font-size: 12px; color: var(--el-text-color-secondary); line-height: 1.4">
              选定后开放数据探索/取数能力,且只能访问所选数据源;不选则不挂数据分析工具。
            </div>
          </el-form-item>
          <el-form-item label="工具">
            <el-select v-model="cfg.toolIds" multiple filterable clearable placeholder="选择可用工具(MCP/任务)" style="width: 100%">
              <el-option
                v-for="t in selectableTools"
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
          <el-form-item label="长期记忆">
            <el-switch v-model="cfg.enableMemory" />
            <span style="margin-left: 8px; font-size: 12px; color: var(--el-text-color-secondary)">跨会话记住用户偏好/事实(按用户隔离)</span>
          </el-form-item>
          <el-form-item label="上下文历史">
            <el-switch v-model="cfg.addHistory" />
            <el-input-number v-if="cfg.addHistory" v-model="cfg.numHistoryRuns" :min="1" :max="50" :step="1" controls-position="right" style="margin-left: 8px; width: 120px" />
            <span style="margin-left: 8px; font-size: 12px; color: var(--el-text-color-secondary)">本会话携带最近 N 轮历史(关闭则每次单轮无上下文)</span>
          </el-form-item>

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

    <!-- AI 生成提示词:弹窗流式吐字,确认后回填到系统提示词 -->
    <PromptGenDialog
      v-model="pgVisible"
      :model-id="cfg.model.modelId"
      :initial-requirement="form.description || form.name"
      @apply="(t) => (cfg.prompt = t)"
    />
  </div>
</template>

<script setup name="AiAppEdit">
import { reactive, ref, computed, nextTick, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import AiMessage from "../chat/components/AiMessage.vue";
import PromptGenDialog from "./components/PromptGenDialog.vue";
import { getApp, addApp, updateApp } from "@/api/ai/app";
import { listTool } from "@/api/ai/tool";
import { listModelAll } from "@/api/ai/model";
import { listDataset } from "@/api/rag";
import { listSource } from "@/api/dataManage/data";
import { getToken } from "@/utils/auth";
import { v4 as uuidv4 } from "uuid";

const route = useRoute();
const router = useRouter();
const apiBase = import.meta.env.VITE_APP_BASE_API || "";

const form = reactive({ appId: route.params.appId ? Number(route.params.appId) : null, name: "", description: "", status: "0" });
const cfg = reactive({ prompt: "", prologue: "", presetQuestions: [], quickCommands: [], toolIds: [], datasetIds: [], datasourceCodes: [], enableMemory: false, addHistory: true, numHistoryRuns: 10, model: { modelId: 0, temperature: null, maxTokens: null } });
// 只读态:点卡片进入(view=1)只看配置不可改,右侧仍可对话;点「编辑」切换为可编辑
const readonly = ref(route.query.view === "1");
const pgVisible = ref(false);
const saving = ref(false);
const toolOptions = ref([]);
const modelOptions = ref([]);
const datasetOptions = ref([]);
const datasourceOptions = ref([]);
// 工具多选只给 MCP + 任务提议;数据分析工具由「数据分析」数据源选择控制
const selectableTools = computed(() => toolOptions.value.filter((t) => !["data_explore", "sandbox_code"].includes(t.code)));

// 右侧调试对话
const messages = ref([]);
const input = ref("");
const loading = ref(false);
const sessionId = ref(uuidv4());
const historyRef = ref(null);

onMounted(async () => {
  const [tools, models, datasets, sources] = await Promise.all([
    listTool({ pageNum: 1, pageSize: 200 }),
    listModelAll(),
    listDataset({ pageNum: 1, pageSize: 200 }),
    listSource({ pageNum: 1, pageSize: 200 }),
  ]);
  toolOptions.value = tools.rows || [];
  modelOptions.value = models.data || [];
  datasetOptions.value = datasets.rows || [];
  datasourceOptions.value = sources.rows || [];
  if (form.appId) {
    const res = await getApp(form.appId);
    const d = res.data || {};
    Object.assign(form, { name: d.name, description: d.description, status: d.status || "0" });
    Object.assign(cfg, { ...cfg, ...(d.config || {}) });
    if (!cfg.model) cfg.model = { modelId: 0 };
  } else if (route.query.copyFrom) {
    // 复制:带入源应用配置作为新建表单初值(appId 仍为空,保存即新增),名称加 _copy
    const res = await getApp(route.query.copyFrom);
    const d = res.data || {};
    Object.assign(form, { name: (d.name || "") + "_copy", description: d.description, status: "1" });
    Object.assign(cfg, { ...cfg, ...(d.config || {}) });
    if (!cfg.model) cfg.model = { modelId: 0 };
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
      }
    })
    .finally(() => (saving.value = false));
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
    if (!resp.ok || !resp.body) {
      const t = await resp.text().catch(() => "");
      messages.value[ai].content = "调试失败: HTTP " + resp.status + " " + t.slice(0, 200);
      ElMessage.error("调试失败: HTTP " + resp.status);
      return;
    }
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
