<template>
  <div class="ai-message-container">
    <div v-if="reasoningContent" class="reasoning-section">
      <div class="reasoning-header" @click="toggleReasoning">
        <el-icon :class="{ 'is-expanded': isReasoningExpanded }"
          ><ArrowRight
        /></el-icon>
        <span>{{ $t('深度思考过程') }}</span>
        <span class="reasoning-status" v-if="!isThinkingComplete"
          >{{ $t('思考中...') }}</span
        >
      </div>
      <div v-show="isReasoningExpanded" class="reasoning-content">
        <MarkdownRender :content="reasoningContent" :is-dark="isDark" />
      </div>
    </div>
    <!-- 主体:按到达顺序的 blocks(文字 — 工具调用 — 文字 — 产物 交替) -->
    <template v-if="blocks && blocks.length">
      <template v-for="(b, i) in blocks" :key="i">
        <!-- 文字段(多 agent 时带成员归属标签) -->
        <div v-if="b.type === 'text'" class="ai-message-content">
          <div v-if="b.agentName" class="agent-tag">🤖 {{ b.agentName }}</div>
          <MarkdownRender :content="b.text" :is-dark="isDark" />
        </div>
        <!-- 工具调用(内联,夹在文字之间) -->
        <div v-else-if="b.type === 'tool'" class="inline-tool">
          <div class="step-head" @click="toggleBlk(i)">
            <el-icon v-if="b.status === 'running'" class="step-icon running"><Loading /></el-icon>
            <el-icon v-else-if="b.status === 'error'" class="step-icon error"><CircleCloseFilled /></el-icon>
            <el-icon v-else class="step-icon done"><CircleCheckFilled /></el-icon>
            <span class="step-name">{{ toolLabel(b.name) }}</span>
            <span v-if="b.agentName" class="step-agent">· {{ b.agentName }}</span>
            <span v-if="b.status === 'running'" class="step-status">{{ $t('运行中…') }}</span>
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
            <span class="artifact-kind">{{ b.artifact.kind === "table" ? "表格" : "图表" }}</span>
            <el-button
              v-if="b.artifact.saveable && (b.artifact.kind === 'echart' || b.artifact.kind === 'chart')"
              link
              size="small"
              :type="b.artifact.saved ? 'success' : 'primary'"
              :icon="b.artifact.saved ? 'Select' : 'DocumentAdd'"
              :loading="!!savingChart[i]"
              :disabled="b.artifact.saved"
              @click="saveDashboard(b.artifact, i)"
              >{{ b.artifact.saved ? "已存看板" : "存为看板" }}</el-button
            >
            <el-button
              v-if="b.artifact.kind === 'chart'"
              link
              size="small"
              icon="Download"
              @click="exportChart(b.artifact)"
              >{{ $t('导出 HTML') }}</el-button
            >
            <el-button v-else-if="b.artifact.kind === 'table'" link size="small" icon="Download" @click="exportTable(b.artifact)">{{ $t('导出 Excel') }}</el-button>
          </div>
          <EchartsBuilder
            v-if="b.artifact.kind === 'echart'"
            :rows="b.artifact.rows"
            :config="b.artifact.cfg"
            :show-controls="false"
            :height="360"
          />
          <iframe
            v-else-if="b.artifact.kind === 'chart'"
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
        <!-- 任务提议/修改:可编辑的确认表单卡片(新建并运行/仅创建;或修改已有任务保存) -->
        <TaskProposalCard
          v-else-if="b.type === 'ui_action' && b.action && (b.action.kind === 'task_proposal' || b.action.kind === 'task_update_proposal')"
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

    <!-- 代码取数的图「存为看板」:流式生成 native+配置 → 预览取数画图 → 确认落库(避免一次性阻塞超时) -->
    <el-dialog
      v-model="conv.visible"
      :title="$t('AI 转看板')"
      width="920px"
      top="5vh"
      append-to-body
      :close-on-click-modal="false"
      class="conv-dialog"
    >
      <div class="conv-body">
        <div class="conv-gen">
          <div class="conv-head">
            <span>{{ $t('生成配置') }}<span v-if="conv.streaming" class="conv-ing"> {{ $t('· 生成中…') }}</span></span>
          </div>
          <pre class="conv-out">{{ conv.text || (conv.streaming ? '' : '(空)') }}<span v-if="conv.streaming" class="cursor">▋</span></pre>
          <div v-if="conv.err" class="conv-err">{{ conv.err }}</div>
          <!-- 手输补充提示纠偏后重新生成(失败/结果不理想时用,如:指定聚合列、纠正字段名、换图表类型) -->
          <div class="conv-hint">
            <el-input
              v-model="conv.hint"
              type="textarea"
              :rows="2"
              :disabled="conv.streaming"
              :placeholder="$t('可选:给转换补充提示,如「按行业分组求和放到 cfg」「字段名用 change_pct」「改成折线图」,再点重新生成')"
              @keyup.enter.exact.prevent="regenerate"
            />
            <el-button
              size="small"
              type="primary"
              icon="Refresh"
              :loading="conv.streaming"
              @click="regenerate"
              >{{ conv.text ? '重新生成' : '生成' }}</el-button
            >
          </div>
        </div>
        <div class="conv-preview" v-loading="conv.previewing" element-loading-text="取数预览中…">
          <EchartsBuilder
            v-if="conv.rows.length && conv.cfg"
            :rows="conv.rows"
            :config="conv.cfg"
            :show-controls="false"
            :height="360"
          />
          <el-empty
            v-else
            :description="conv.streaming ? '等待生成完成…' : (conv.err ? '生成/预览失败,可重新生成' : '暂无预览')"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="conv.visible = false">{{ $t('取消') }}</el-button>
        <el-button
          type="primary"
          :disabled="!conv.rows.length || !conv.cfg || conv.streaming || conv.previewing"
          :loading="conv.saving"
          @click="confirmSave"
          >{{ $t('确认存为看板') }}</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Star, StarFilled } from "@element-plus/icons-vue";
import { saveAs } from "file-saver";
import * as XLSX from "xlsx";
import TaskProposalCard from "./TaskProposalCard.vue";
import EchartsBuilder from "@/views/dataManage/visualization/EchartsBuilder.vue";
import { saveRecipe } from "@/api/ai/chat";
import { saveChartAsBoard, previewNative } from "@/api/dataManage/data";
import { getToken } from "@/utils/auth";

const AI_BASE = import.meta.env.VITE_APP_BASE_API || "";
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

// 统一「存为看板」:
// - plot_chart 声明式图(带 native+chartSpec)→ 命名后直存(瞬时);
// - 代码取数的图(带 code)→ 打开对话框,流式把代码转成 native+配置、预览画图,再确认落库
//   (旧版一次性阻塞转换很慢、会超时,故拆成 流式生成 → 预览 → 确认)。
const savingChart = ref({});
async function saveDashboard(art, i) {
  if (!art || !art.saveable || art.saved) return;
  if (art.saveable.mode === "code") {
    openConvert(art, i);
    return;
  }
  // 声明式:已有 native + chartSpec,命名后直存
  let name;
  try {
    const r = await ElMessageBox.prompt("给看板起个名字", "存为看板", {
      confirmButtonText: "保存",
      cancelButtonText: "取消",
      inputValue: art.saveable.title || "",
      inputPlaceholder: "看板名称",
      inputValidator: (v) => (v && v.trim() ? true : "请输入名称"),
    });
    name = r.value;
  } catch (e) {
    return; // 取消
  }
  const sv = art.saveable;
  savingChart.value[i] = true;
  try {
    await saveChartAsBoard({ name: name.trim(), datasourceCode: sv.datasourceCode, native: sv.native, chartSpec: sv.chartSpec });
    art.saved = true;
    ElMessage.success("已存为看板,可在「数据管理 → 数据看板」查看");
  } catch (e) {
    ElMessage.error("保存失败: " + (e?.msg || e?.message || e));
  } finally {
    savingChart.value[i] = false;
  }
}

// ---- 代码取数图 → 转看板对话框(流式生成 + 预览 + 确认)----
const conv = reactive({
  visible: false, art: null, i: -1,
  streaming: false, previewing: false, saving: false,
  text: "", native: null, cfg: null, rows: [], err: "", hint: "",
});
function stripFence(t) {
  let s = (t || "").trim();
  if (s.startsWith("```")) s = s.replace(/^```[^\n]*\n/, "").replace(/```\s*$/, "").trim();
  return s;
}
function openConvert(art, i) {
  Object.assign(conv, {
    visible: true, art, i, streaming: false, previewing: false, saving: false,
    text: "", native: null, cfg: null, rows: [], err: "", hint: "",
  });
  regenerate();
}
// 流式请求后端把「取数代码」转成 {native, cfg},实时打印;结束后自动预览取数画图
async function regenerate() {
  const sv = conv.art && conv.art.saveable;
  if (!sv) return;
  Object.assign(conv, { streaming: true, err: "", text: "", native: null, cfg: null, rows: [] });
  try {
    const resp = await fetch(AI_BASE + "/data/analysis-template/code-to-board/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + getToken() },
      body: JSON.stringify({ datasourceCode: sv.datasourceCode, code: sv.code, question: sv.title || "", hint: conv.hint || "" }),
    });
    if (!resp.ok || !resp.body) throw new Error("HTTP " + resp.status);
    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      conv.text += dec.decode(value, { stream: true });
    }
  } catch (e) {
    conv.streaming = false;
    conv.err = "生成失败: " + (e?.message || e);
    return;
  }
  conv.streaming = false;
  await parseAndPreview();
}
// 解析流式产出的 {native, cfg} → 实跑 native 取数 → 画预览图(取数即校验)
async function parseAndPreview() {
  let obj;
  try {
    obj = JSON.parse(stripFence(conv.text));
  } catch (e) {
    conv.err = "生成结果不是合法 JSON,请点「重新生成」";
    return;
  }
  if (!obj || obj.native == null) {
    conv.err = "生成结果缺少 native 查询,请点「重新生成」";
    return;
  }
  conv.native = obj.native;
  conv.cfg = obj.cfg || null;
  const sv = conv.art.saveable;
  conv.previewing = true;
  conv.err = "";
  try {
    const res = await previewNative({ datasourceCode: sv.datasourceCode, native: conv.native });
    conv.rows = res.data.records || [];
    if (!conv.rows.length) conv.err = "预览取数为空(0 行),可点「重新生成」";
  } catch (e) {
    conv.err = "预览取数失败: " + (e?.msg || e?.message || e);
  } finally {
    conv.previewing = false;
  }
}
async function confirmSave() {
  const sv = conv.art && conv.art.saveable;
  if (!sv || conv.native == null) return;
  let name;
  try {
    const r = await ElMessageBox.prompt("给看板起个名字", "存为看板", {
      confirmButtonText: "保存",
      cancelButtonText: "取消",
      inputValue: sv.title || "",
      inputPlaceholder: "看板名称",
      inputValidator: (v) => (v && v.trim() ? true : "请输入名称"),
    });
    name = r.value;
  } catch (e) {
    return;
  }
  conv.saving = true;
  try {
    await saveChartAsBoard({ name: name.trim(), datasourceCode: sv.datasourceCode, native: conv.native, chartSpec: conv.cfg });
    conv.art.saved = true;
    conv.visible = false;
    ElMessage.success("已存为看板,可在「数据管理 → 数据看板」查看");
  } catch (e) {
    ElMessage.error("保存失败: " + (e?.msg || e?.message || e));
  } finally {
    conv.saving = false;
  }
}

// 工具名 → 友好中文
const TOOL_LABELS = {
  list_datasources: "发现数据源",
  get_table_schema: "查表结构",
  search_datasource_knowledge: "检索知识库",
  run_python_code: "运行代码",
  run_datasource_query: "取数查询",
  plot_chart: "生成图表",
  delegate_task_to_member: "委派成员",
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
// 1) 把 echarts CDN(assets.pyecharts.org,受限网络常不可达,图表画不出)改为同源本地副本
//    /echarts.min.js(public/),并保留 CDN 作 onerror 兜底,离线/在线都能渲染;
// 2) 注入 CSS + resize 脚本:把固定 900×500 容器改成 100%、随 iframe 宽度自适应。
function fitChart(html) {
  if (!html) return html;
  const localEcharts = window.location.origin + "/echarts.min.js";
  // 把 echarts 的 <script src=CDN> 换成本地源 + CDN 兜底(其余 pyecharts 扩展脚本保持原样)
  html = html.replace(
    /<script\s+type="text\/javascript"\s+src="(https?:\/\/[^"]*\/echarts\.min\.js)"><\/script>/i,
    `<script type="text/javascript" src="${localEcharts}" onerror="this.onerror=null;var s=document.createElement('script');s.src='$1';document.head.appendChild(s);"><\/script>`,
  );
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

// 同源 echarts 源码缓存(用于把图表导出成自包含 html)
let _echartsSrc = null;
async function loadEchartsSrc() {
  if (_echartsSrc !== null) return _echartsSrc;
  try {
    const resp = await fetch(window.location.origin + "/echarts.min.js");
    _echartsSrc = resp.ok ? await resp.text() : "";
  } catch (e) {
    _echartsSrc = "";
  }
  return _echartsSrc;
}
// 导出 echarts 图表为独立 html:把 CDN <script src> 内联成本地 echarts 源码,
// 这样导出的文件离线/任意网络都能打开看到图(否则原始 html 仍指向 CDN,受限网络空白)。
async function exportChart(art) {
  const raw = art && art.html;
  if (!raw) return ElMessage.warning("无图表内容可导出");
  let html = raw;
  const js = await loadEchartsSrc();
  if (js) {
    // 用替换函数(而非字符串),避免 echarts 源码里的 $ 被当成 replace 特殊变量
    html = html.replace(
      /<script\s+type="text\/javascript"\s+src="https?:\/\/[^"]*\/echarts\.min\.js"><\/script>/i,
      () => `<script type="text/javascript">${js}<\/script>`,
    );
  }
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

    .agent-tag {
      display: inline-block;
      margin-bottom: 4px;
      padding: 1px 8px;
      font-size: 12px;
      color: var(--el-color-primary);
      background: var(--el-color-primary-light-9);
      border-radius: 10px;
    }
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
  .step-agent {
    font-size: 12px;
    color: var(--el-color-primary);
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

.conv-dialog {
  .conv-body {
    display: flex;
    gap: 12px;
  }
  .conv-gen {
    width: 46%;
    display: flex;
    flex-direction: column;
  }
  .conv-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 13px;
    color: var(--el-text-color-regular);
    margin-bottom: 6px;
  }
  .conv-ing {
    color: var(--el-color-primary);
  }
  .conv-out {
    flex: 1;
    min-height: 320px;
    max-height: 60vh;
    overflow: auto;
    margin: 0;
    padding: 10px 12px;
    background: #1e1e1e;
    color: #d4d4d4;
    border-radius: 6px;
    font-family: Consolas, Monaco, monospace;
    font-size: 12px;
    white-space: pre-wrap;
    word-break: break-all;
  }
  .conv-err {
    margin-top: 6px;
    font-size: 12px;
    color: var(--el-color-danger);
  }
  .conv-hint {
    margin-top: 8px;
    display: flex;
    gap: 8px;
    align-items: flex-end;
    .el-textarea {
      flex: 1;
    }
  }
  .conv-preview {
    flex: 1;
    min-width: 0;
    min-height: 360px;
    border: 1px solid var(--el-border-color);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 6px;
  }
  .cursor {
    color: #67c23a;
    animation: blink 1s steps(1) infinite;
  }
}
</style>
