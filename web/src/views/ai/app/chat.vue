<template>
  <div class="app-chat">
    <div class="ac-header">
      <el-button link icon="ArrowLeft" @click="goBack">应用广场</el-button>
      <div class="ac-title">
        <el-icon><Cpu /></el-icon>
        <span>{{ app.name || "应用对话" }}</span>
      </div>
      <el-button link icon="Plus" @click="newChat">新对话</el-button>
    </div>

    <div ref="historyRef" class="ac-history">
      <!-- 欢迎屏 -->
      <div v-if="messageList.length === 0" class="ac-welcome">
        <div class="ac-avatar"><el-icon><Cpu /></el-icon></div>
        <div class="ac-hello">{{ app.config?.prologue || "你好,有什么可以帮你?" }}</div>
        <div v-if="presetQuestions.length" class="ac-presets">
          <el-tag
            v-for="(q, i) in presetQuestions"
            :key="i"
            class="ac-preset"
            effect="plain"
            @click="sendMessage(q)"
            >{{ q }}</el-tag
          >
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
        <el-button v-for="(c, i) in quickCommands" :key="i" size="small" round @click="sendMessage(c.content)">
          {{ c.name }}
        </el-button>
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
  </div>
</template>

<script setup name="AiAppChat">
import { ref, reactive, computed, nextTick, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import AiMessage from "../chat/components/AiMessage.vue";
import { getApp } from "@/api/ai/app";
import { getToken } from "@/utils/auth";
import { v4 as uuidv4 } from "uuid";

const route = useRoute();
const router = useRouter();
const appId = route.params.appId;

const app = reactive({ name: "", config: {} });
const messageList = ref([]);
const input = ref("");
const loading = ref(false);
const sessionId = ref(uuidv4());
const historyRef = ref(null);
const abort = ref(null);

const presetQuestions = computed(() => app.config?.presetQuestions || []);
const quickCommands = computed(() => app.config?.quickCommands || []);

onMounted(() => {
  getApp(appId).then((res) => {
    app.name = res.data?.name || "应用对话";
    app.config = res.data?.config || {};
  });
});

function goBack() {
  router.push("/ai/app");
}
function newChat() {
  if (loading.value) return;
  messageList.value = [];
  sessionId.value = uuidv4();
}

function scrollBottom() {
  nextTick(() => {
    if (historyRef.value) historyRef.value.scrollTop = historyRef.value.scrollHeight;
  });
}

async function sendMessage(preset) {
  const text = (preset !== undefined ? preset : input.value).trim();
  if (!text || loading.value) return;
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
          if (last && last.type === "text") last.text += d.content;
          else m.blocks.push({ type: "text", text: d.content });
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
            m.blocks.push({ type: "tool", id: d.id, name: d.name, args: d.args, status: "running" });
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
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}
.ac-header {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
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
  background: radial-gradient(1200px 400px at 50% -10%, var(--el-color-primary-light-9), transparent 60%),
    var(--el-bg-color-page);
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
