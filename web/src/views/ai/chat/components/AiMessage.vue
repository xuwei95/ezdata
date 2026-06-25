<template>
  <div class="ai-message-container">
    <div v-if="reasoningContent" class="reasoning-section">
      <div class="reasoning-header" @click="toggleReasoning">
        <el-icon :class="{ 'is-expanded': isReasoningExpanded }"
          ><ArrowRight
        /></el-icon>
        <span>深度思考过程</span>
        <span class="reasoning-status" v-if="!isThinkingComplete"
          >思考中...</span
        >
      </div>
      <div v-show="isReasoningExpanded" class="reasoning-content">
        <MarkdownRender :content="reasoningContent" :is-dark="isDark" />
      </div>
    </div>
    <!-- 主体:按到达顺序的 blocks(文字 — 工具调用 — 文字 — 产物 交替) -->
    <template v-if="blocks && blocks.length">
      <template v-for="(b, i) in blocks" :key="i">
        <!-- 文字段 -->
        <div v-if="b.type === 'text'" class="ai-message-content">
          <MarkdownRender :content="b.text" :is-dark="isDark" />
        </div>
        <!-- 工具调用(内联,夹在文字之间) -->
        <div v-else-if="b.type === 'tool'" class="inline-tool">
          <div class="step-head" @click="toggleBlk(i)">
            <el-icon v-if="b.status === 'running'" class="step-icon running"><Loading /></el-icon>
            <el-icon v-else-if="b.status === 'error'" class="step-icon error"><CircleCloseFilled /></el-icon>
            <el-icon v-else class="step-icon done"><CircleCheckFilled /></el-icon>
            <span class="step-name">{{ toolLabel(b.name) }}</span>
            <span v-if="b.status === 'running'" class="step-status">运行中…</span>
            <el-button
              v-if="canSaveRecipe(b) && sessionId"
              class="step-recipe"
              link
              size="small"
              :type="b.saved ? 'success' : 'warning'"
              :icon="b.saved ? StarFilled : Star"
              :loading="!!savingBlk[b.id]"
              :disabled="b.saved"
              @click.stop="saveRecipeOf(b)"
              >{{ b.saved ? "已收藏" : "收藏到知识库" }}</el-button
            >
            <el-icon class="step-toggle" :class="{ 'is-open': expandedBlks[i] }"><ArrowRight /></el-icon>
          </div>
          <div v-show="expandedBlks[i]" class="step-detail">
            <pre v-if="b.args" class="step-pre">参数: {{ fmt(b.args) }}</pre>
            <pre v-if="b.result" class="step-pre">结果: {{ b.result }}</pre>
            <pre v-if="b.error" class="step-pre step-err">错误: {{ b.error }}</pre>
          </div>
        </div>
        <!-- 产物:图表(iframe echarts) / 表格(vxe-table) -->
        <div v-else-if="b.type === 'artifact'" class="ai-artifact">
          <div class="artifact-bar">
            <span class="artifact-kind">{{ b.artifact.kind === "chart" ? "图表" : "表格" }}</span>
            <el-button
              v-if="b.artifact.kind === 'chart'"
              link
              size="small"
              icon="Download"
              @click="exportChart(b.artifact)"
              >导出 HTML</el-button
            >
            <el-button v-else link size="small" icon="Download" @click="exportTable(b.artifact)">导出 Excel</el-button>
          </div>
          <iframe
            v-if="b.artifact.kind === 'chart'"
            class="artifact-chart"
            :srcdoc="fitChart(b.artifact.html)"
            sandbox="allow-scripts"
            frameborder="0"
          />
          <template v-else-if="b.artifact.kind === 'table'">
            <vxe-table
              :data="b.artifact.rows"
              border
              stripe
              size="mini"
              max-height="360"
              show-overflow
              :column-config="{ resizable: true }"
              :scroll-y="{ enabled: true, gt: 50 }"
              :scroll-x="{ enabled: true, gt: 20 }"
            >
              <vxe-column type="seq" width="50" fixed="left" />
              <vxe-column
                v-for="c in colsOf(b.artifact.rows)"
                :key="c"
                :field="c"
                :title="c"
                min-width="120"
              />
            </vxe-table>
            <div
              v-if="b.artifact.total > (b.artifact.rows ? b.artifact.rows.length : 0)"
              class="artifact-hint"
            >
              共 {{ b.artifact.total }} 行,仅展示前 {{ b.artifact.rows.length }} 行
            </div>
          </template>
        </div>
        <!-- 任务提议:可编辑的确认表单卡片(创建并运行 / 仅创建) -->
        <TaskProposalCard
          v-else-if="b.type === 'ui_action' && b.action && b.action.kind === 'task_proposal'"
          :action="b.action"
        />
      </template>
    </template>
    <!-- 历史消息(无 blocks)回退:纯文本 -->
    <div v-else-if="content" class="ai-message-content">
      <MarkdownRender :content="content" :is-dark="isDark" />
    </div>
    <div
      v-if="loading && !content && !reasoningContent"
      class="typing-indicator"
    >
      <span></span>
      <span></span>
      <span></span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { Star, StarFilled } from "@element-plus/icons-vue";
import { saveAs } from "file-saver";
import * as XLSX from "xlsx";
import TaskProposalCard from "./TaskProposalCard.vue";
import { saveRecipe } from "@/api/ai/chat";
import { MarkdownRender } from "markstream-vue";
import { useDark } from "@vueuse/core";
import { enableKatex, enableMermaid } from "markstream-vue";
import "markstream-vue/index.css";
import "katex/dist/katex.min.css";

enableMermaid();
enableKatex();

const isDark = useDark();

const props = defineProps({
  content: {
    type: String,
    default: "",
  },
  reasoningContent: {
    type: String,
    default: "",
  },
  loading: {
    type: Boolean,
    default: false,
  },
  blocks: {
    type: Array,
    default: () => [],
  },
  sessionId: {
    type: String,
    default: "",
  },
});

// 「收藏为解法」:把成功的取数调用(全量代码+本轮问题)存进该数据源知识库
const savingBlk = ref({});
function canSaveRecipe(b) {
  return b.type === "tool" && b.name === "run_datasource_query" && b.status === "done";
}
async function saveRecipeOf(b) {
  if (!props.sessionId || !b.id || b.saved || savingBlk.value[b.id]) return;
  savingBlk.value[b.id] = true;
  try {
    const res = await saveRecipe(props.sessionId, b.id);
    b.saved = true;
    ElMessage.success("已存入「" + (res.data?.datasetName || "数据源知识库") + "」");
  } catch (e) {
    ElMessage.error("收藏失败: " + (e?.message || e));
  } finally {
    savingBlk.value[b.id] = false;
  }
}

// 工具名 → 友好中文
const TOOL_LABELS = {
  list_datasources: "发现数据源",
  get_table_schema: "查表结构",
  search_datasource_knowledge: "检索知识库",
  run_python_code: "运行代码",
  run_datasource_query: "取数查询",
};
function toolLabel(name) {
  return TOOL_LABELS[name] || name;
}
function fmt(v) {
  try {
    return typeof v === "string" ? v : JSON.stringify(v, null, 2);
  } catch (e) {
    return String(v);
  }
}
const expandedBlks = ref({});
function toggleBlk(i) {
  expandedBlks.value[i] = !expandedBlks.value[i];
}

// pyecharts render_embed() 已是含 echarts 公网 CDN 的完整 html 页面(勿再包一层)。
// 仅向其中注入 CSS + resize 脚本:把固定 900×500 的图表容器改成 100%、随 iframe 宽度自适应。
function fitChart(html) {
  if (!html) return html;
  const css =
    "<style>html,body{height:100%;margin:0;overflow:hidden}" +
    ".chart-container{width:100%!important;height:100%!important}</style>";
  const js =
    '<script>window.addEventListener("resize",function(){' +
    'var e=document.querySelector(".chart-container");' +
    "if(window.echarts&&e){var c=echarts.getInstanceByDom(e);if(c)c.resize();}});<\/script>";
  let out = html.includes("</head>") ? html.replace("</head>", css + "</head>") : css + html;
  out = out.includes("</body>") ? out.replace("</body>", js + "</body>") : out + js;
  return out;
}

// 表格列名:取首行的 key
function colsOf(rows) {
  return rows && rows.length ? Object.keys(rows[0]) : [];
}

// 导出 echarts 图表为独立 html(render_embed 已是完整页面,直接下载即可离线打开)
function exportChart(art) {
  const html = art && art.html;
  if (!html) return ElMessage.warning("无图表内容可导出");
  saveAs(new Blob([html], { type: "text/html;charset=utf-8" }), `chart_${Date.now()}.html`);
}
// 导出当前表格为 Excel(导出已展示的行;大表仅含预览行)
function exportTable(art) {
  const rows = (art && art.rows) || [];
  if (!rows.length) return ElMessage.warning("无数据可导出");
  const ws = XLSX.utils.json_to_sheet(rows, { header: colsOf(rows) });
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, "Sheet1");
  XLSX.writeFile(wb, `table_${Date.now()}.xlsx`);
}

const isReasoningExpanded = ref(true);

const isThinkingComplete = computed(() => {
  return !!props.content;
});

function toggleReasoning() {
  isReasoningExpanded.value = !isReasoningExpanded.value;
}
</script>

<style lang="scss">
.ai-message-container {
  width: 100%;

  .ai-message-content {
    font-size: 14px;
    line-height: 1.6;
    color: var(--el-text-color-primary);
    overflow-wrap: break-word;
    word-break: break-word;
  }

  .ai-artifact {
    margin: 10px 0;

    .artifact-bar {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
      .artifact-kind {
        font-size: 12px;
        color: var(--el-text-color-secondary);
        margin-right: auto;
      }
    }

    .artifact-chart {
      width: 100%;
      height: 420px;
      border: 1px solid var(--el-border-color);
      border-radius: 4px;
      background: #fff;
    }

    .artifact-hint {
      margin-top: 4px;
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.reasoning-section {
  margin-bottom: 15px;
  border-left: 2px solid var(--el-border-color);
  padding-left: 10px;

  .reasoning-header {
    display: flex;
    align-items: center;
    cursor: pointer;
    color: var(--el-text-color-secondary);
    font-size: 13px;
    user-select: none;
    margin-bottom: 5px;

    .el-icon {
      margin-right: 4px;
      transition: transform 0.3s;
      &.is-expanded {
        transform: rotate(90deg);
      }
    }

    .reasoning-status {
      margin-left: 10px;
      font-size: 12px;
      color: #e6a23c;
      animation: blink 1.5s infinite;
    }
  }

  .reasoning-content {
    font-size: 13px;
    color: var(--el-text-color-regular);
    padding: 8px;
    background-color: var(--el-fill-color-light);
    border-radius: 4px;
    overflow-wrap: break-word;
    word-break: break-word;
  }
}

.inline-tool {
  margin: 8px 0;
  padding: 6px 10px;
  background: var(--el-fill-color-lighter);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  font-size: 13px;

  .step-head {
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
  }
  .step-icon {
    font-size: 14px;
    &.done {
      color: var(--el-color-success);
    }
    &.error {
      color: var(--el-color-danger);
    }
    &.running {
      color: var(--el-color-primary);
      animation: spin 1s linear infinite;
    }
  }
  .step-name {
    color: var(--el-text-color-regular);
    font-weight: 500;
  }
  .step-status {
    font-size: 12px;
    color: var(--el-color-primary);
  }
  .step-recipe {
    margin-left: auto;
    font-size: 12px;
  }
  .step-toggle {
    margin-left: auto;
    color: var(--el-text-color-placeholder);
    transition: transform 0.2s;
    &.is-open {
      transform: rotate(90deg);
    }
  }
  .step-detail {
    padding: 6px 0 2px 20px;
  }
  .step-pre {
    margin: 2px 0;
    padding: 6px 8px;
    background: var(--el-fill-color);
    border-radius: 4px;
    font-size: 12px;
    white-space: pre-wrap;
    word-break: break-all;
    color: var(--el-text-color-regular);
    &.step-err {
      color: var(--el-color-danger);
    }
  }
}

@keyframes spin {
  from {
    transform: rotate(0);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes blink {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
  100% {
    opacity: 1;
  }
}

.typing-indicator {
  display: flex;
  align-items: center;
  padding: 8px 0;

  span {
    display: inline-block;
    width: 6px;
    height: 6px;
    background-color: var(--el-text-color-secondary);
    border-radius: 50%;
    animation: typing 1.4s infinite ease-in-out both;
    margin-right: 4px;

    &:nth-child(1) {
      animation-delay: -0.32s;
    }

    &:nth-child(2) {
      animation-delay: -0.16s;
    }
  }
}

@keyframes typing {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>
