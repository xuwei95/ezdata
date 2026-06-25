<template>
  <div class="app-chat">
    <el-container style="height: 100%">
      <!-- 左侧:会话列表(可伸缩) -->
      <el-aside :width="sidebarCollapsed ? '0px' : '240px'" class="ac-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <div class="ac-side-head">
          <el-button type="primary" class="ac-new" icon="Plus" @click="newChat">新建会话</el-button>
        </div>
        <div class="ac-sessions" v-loading="sessionLoading">
          <div
            v-for="s in sessionList"
            :key="s.sessionId"
            :class="['ac-session', sessionId === s.sessionId ? 'active' : '']"
            @click="loadSession(s.sessionId)"
          >
            <el-icon class="ac-s-icon"><ChatDotRound /></el-icon>
            <div class="ac-s-info">
              <div class="ac-s-title">{{ s.sessionTitle || "新会话" }}</div>
              <div class="ac-s-time">{{ formatTime(s.createdAt) }}</div>
            </div>
            <el-button class="ac-s-del" type="danger" link icon="Delete" @click.stop="handleDeleteSession(s.sessionId)" />
          </div>
          <div v-if="!sessionList.length && !sessionLoading" class="ac-s-empty">暂无历史会话</div>
        </div>
      </el-aside>

      <!-- 右侧:对话区 -->
      <el-main class="ac-main">
        <div class="ac-header">
          <div class="ac-h-left">
            <el-tooltip :content="sidebarCollapsed ? '展开会话列表' : '收起会话列表'" placement="bottom">
              <el-button class="ac-toggle" :icon="sidebarCollapsed ? 'Expand' : 'Fold'" text @click="sidebarCollapsed = !sidebarCollapsed" />
            </el-tooltip>
            <el-button link icon="ArrowLeft" @click="goBack">应用广场</el-button>
            <div class="ac-title">
              <el-icon><Cpu /></el-icon>
              <span>{{ app.name || "应用对话" }}</span>
            </div>
          </div>
          <el-button link icon="Plus" @click="newChat">新对话</el-button>
        </div>

        <div ref="historyRef" class="ac-history">
          <!-- 欢迎屏 -->
          <div v-if="messageList.length === 0" class="ac-welcome">
            <div class="ac-avatar"><el-icon><Cpu /></el-icon></div>
            <div class="ac-hello">{{ app.config?.prologue || "你好,有什么可以帮你?" }}</div>
            <div v-if="presetQuestions.length" class="ac-presets">
              <el-tag v-for="(q, i) in presetQuestions" :key="i" class="ac-preset" effect="plain" @click="sendMessage(q)">{{ q }}</el-tag>
            </div>
          </div>

          <!-- 消息 -->
          <div v-for="(msg, idx) in messageList" :key="idx" class="ac-msg" :class="msg.role">
            <div v-if="msg.role === 'user'" class="ac-user-bubble">{{ msg.content }}</div>
            <AiMessage
              v-else
              :content="msg.content"
              :reasoning-content="msg.reasoningContent"
              :blocks="msg.blocks"
              :session-id="sessionId"
              :loading="loading && idx === messageList.length - 1"
            />
          </div>
        </div>

        <div class="ac-input">
          <div v-if="quickCommands.length" class="ac-quick">
            <el-button v-for="(c, i) in quickCommands" :key="i" size="small" round @click="sendMessage(c.content)">{{ c.name }}</el-button>
          </div>
          <div class="ac-input-row">
            <el-input
              v-model="input"
              type="textarea"
              :autosize="{ minRows: 1, maxRows: 5 }"
              placeholder="输入消息,Enter 发送 / Shift+Enter 换行"
              @keydown.enter.exact.prevent="sendMessage()"
            />
            <el-button type="primary" :loading="loading" icon="Promotion" @click="sendMessage()">发送</el-button>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup name="AiAppChat">
import { ref, reactive, computed, nextTick, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import AiMessage from "../chat/components/AiMessage.vue";
import { getApp } from "@/api/ai/app";
import { listChatSession, getChatSession, delChatSession } from "@/api/ai/chat";
import { getToken } from "@/utils/auth";
import { v4 as uuidv4 } from "uuid";

const { proxy } = getCurrentInstance();
const route = useRoute();
const router = useRouter();
const appId = route.params.appId;

const app = reactive({ name: "", config: {} });
const messageList = ref([]);
const input = ref("");
const loading = ref(false);
const sessionId = ref(newSessionId());
const historyRef = ref(null);
const abort = ref(null);
// 会话列表 / 侧栏
const sessionList = ref([]);
const sessionLoading = ref(false);
const sidebarCollapsed = ref(false);

const presetQuestions = computed(() => app.config?.presetQuestions || []);
const quickCommands = computed(() => app.config?.quickCommands || []);

// 应用会话以 app-{appId}- 前缀,后端据此把本应用会话与普通对话/其它应用隔离
function newSessionId() {
  return `app-${appId}-${uuidv4()}`;
}

onMounted(() => {
  getApp(appId).then((res) => {
    app.name = res.data?.name || "应用对话";
    app.config = res.data?.config || {};
  });
  getSessions();
});

function getSessions() {
  sessionLoading.value = true;
  listChatSession(appId)
    .then((res) => {
      const list = res.data || [];
      list.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
      sessionList.value = list;
    })
    .finally(() => (sessionLoading.value = false));
}

function formatTime(t) {
  if (!t) return "";
  try {
    return new Date(t).toLocaleString();
  } catch (e) {
    return t;
  }
}

// 历史消息归一:合并被工具拆开的连续 assistant,丢弃 tool/空消息(与主对话一致)
function normalizeHistory(msgs) {
  const out = [];
  for (const m of msgs || []) {
    if (m.role === "user") {
      out.push(m);
      continue;
    }
    if (m.role !== "assistant") continue;
    const hasBlocks = m.blocks && m.blocks.length;
    if (!m.content && !m.reasoningContent && !hasBlocks) continue;
    const prev = out[out.length - 1];
    if (prev && prev.role === "assistant") {
      prev.content = [prev.content, m.content].filter(Boolean).join("\n\n");
      if (m.reasoningContent) prev.reasoningContent = [prev.reasoningContent, m.reasoningContent].filter(Boolean).join("\n");
      if (hasBlocks) prev.blocks = [...(prev.blocks || []), ...m.blocks];
    } else {
      out.push({ ...m, blocks: hasBlocks ? [...m.blocks] : undefined });
    }
  }
  return out;
}

function loadSession(sid) {
  if (loading.value || sessionId.value === sid) return;
  sessionId.value = sid;
  messageList.value = [];
  loading.value = true;
  getChatSession(sid)
    .then((res) => {
      messageList.value = normalizeHistory(res.data.messages);
      scrollBottom();
    })
    .finally(() => (loading.value = false));
}

function handleDeleteSession(sid) {
  proxy.$modal
    .confirm("是否确认删除该会话？")
    .then(() => delChatSession(sid))
    .then(() => {
      if (sessionId.value === sid) newChat();
      getSessions();
      proxy.$modal.msgSuccess("删除成功");
    })
    .catch(() => {});
}

function goBack() {
  router.push("/ai/app");
}
function newChat() {
  if (loading.value) return;
  messageList.value = [];
  sessionId.value = newSessionId();
}

function scrollBottom() {
  nextTick(() => {
    if (historyRef.value) historyRef.value.scrollTop = historyRef.value.scrollHeight;
  });
}

async function sendMessage(preset) {
  const text = (preset !== undefined ? preset : input.value).trim();
  if (!text || loading.value) return;
  const isNew = messageList.value.length === 0;
  input.value = "";
  messageList.value.push({ role: "user", content: text });
  const aiIdx = messageList.value.push({ role: "assistant", content: "", reasoningContent: "", blocks: [] }) - 1;
  loading.value = true;
  scrollBottom();

  abort.value = new AbortController();
  try {
    const resp = await fetch(import.meta.env.VITE_APP_BASE_API + "/ai/chat/send", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + getToken() },
      signal: abort.value.signal,
      body: JSON.stringify({ modelId: 0, message: text, sessionId: sessionId.value, appId: String(appId) }),
    });
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let aiContent = "";
    let aiReasoning = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        let d;
        try {
          d = JSON.parse(line);
        } catch (e) {
          continue;
        }
        const m = messageList.value[aiIdx];
        if (d.type === "content") {
          aiContent += d.content;
          m.content = aiContent;
          const last = m.blocks[m.blocks.length - 1];
          if (last && last.type === "text" && last.agentName === d.agentName) last.text += d.content;
          else m.blocks.push({ type: "text", text: d.content, agentName: d.agentName });
        } else if (d.type === "reasoning") {
          aiReasoning += d.content;
          m.reasoningContent = aiReasoning;
        } else if (d.type === "meta") {
          sessionId.value = d.session_id;
        } else if (d.type === "artifact") {
          m.blocks.push({ type: "artifact", artifact: d.artifact });
        } else if (d.type === "ui_action") {
          m.blocks.push({ type: "ui_action", action: d.action });
        } else if (d.type === "tool") {
          if (d.phase === "start") {
            m.blocks.push({ type: "tool", id: d.id, name: d.name, args: d.args, status: "running", agentName: d.agentName });
          } else {
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
    if (isNew) getSessions(); // 首条消息落库后刷新会话列表
  } catch (e) {
    if (e.name !== "AbortError") ElMessage.error("对话失败: " + (e?.message || e));
  } finally {
    loading.value = false;
    abort.value = null;
    scrollBottom();
  }
}
</script>

<style scoped lang="scss">
.app-chat {
  height: calc(100vh - 84px);
  background: var(--el-bg-color-page);
}
.ac-sidebar {
  background: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color);
  transition: width 0.2s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  &.collapsed {
    border-right: none;
  }
}
.ac-side-head {
  padding: 12px;
  .ac-new {
    width: 100%;
  }
}
.ac-sessions {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 8px;
}
.ac-session {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 4px;
  &:hover {
    background: var(--el-fill-color-light);
    .ac-s-del {
      opacity: 1;
    }
  }
  &.active {
    background: var(--el-color-primary-light-9);
  }
  .ac-s-icon {
    color: var(--el-text-color-secondary);
  }
  .ac-s-info {
    flex: 1;
    min-width: 0;
  }
  .ac-s-title {
    font-size: 13px;
    color: var(--el-text-color-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .ac-s-time {
    font-size: 11px;
    color: var(--el-text-color-placeholder);
  }
  .ac-s-del {
    opacity: 0;
    transition: opacity 0.2s;
  }
}
.ac-s-empty {
  text-align: center;
  color: var(--el-text-color-placeholder);
  font-size: 13px;
  padding: 20px 0;
}
.ac-main {
  padding: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.ac-header {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  .ac-h-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .ac-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}
.ac-history {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background: radial-gradient(1200px 400px at 50% -10%, var(--el-color-primary-light-9), transparent 60%), var(--el-bg-color-page);
}
.ac-welcome {
  max-width: 760px;
  margin: 40px auto;
  text-align: center;
  .ac-avatar {
    width: 56px;
    height: 56px;
    margin: 0 auto 12px;
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: #fff;
    background: linear-gradient(135deg, var(--el-color-primary), var(--el-color-primary-light-3));
  }
  .ac-hello {
    font-size: 16px;
    color: var(--el-text-color-primary);
    margin-bottom: 16px;
  }
  .ac-presets {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
  }
  .ac-preset {
    cursor: pointer;
  }
}
.ac-msg {
  max-width: 860px;
  margin: 0 auto 16px;
  &.user {
    display: flex;
    justify-content: flex-end;
  }
}
.ac-user-bubble {
  background: var(--el-color-primary);
  color: #fff;
  padding: 10px 14px;
  border-radius: 12px 12px 2px 12px;
  max-width: 80%;
  white-space: pre-wrap;
  word-break: break-word;
}
.ac-input {
  border-top: 1px solid var(--el-border-color);
  background: var(--el-bg-color);
  padding: 12px 16px;
  .ac-quick {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 8px;
  }
  .ac-input-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
    max-width: 900px;
    margin: 0 auto;
  }
}
</style>
