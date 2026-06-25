<template>
  <el-dialog
    :model-value="visible"
    :title="form.name || '应用配置'"
    width="680px"
    append-to-body
    @update:model-value="$emit('update:visible', $event)"
    @open="onOpen"
  >
    <div v-loading="loading" class="ad-body">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="应用名称">{{ form.name || "-" }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="form.status === '0' ? 'success' : 'info'" size="small">{{ form.status === "0" ? "已发布" : "草稿" }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">{{ form.description || "-" }}</el-descriptions-item>
        <el-descriptions-item label="模型">{{ modelName }}</el-descriptions-item>
        <el-descriptions-item label="参数">温度 {{ cfg.model?.temperature ?? "默认" }} / 最大输出 {{ cfg.model?.maxTokens || "默认" }}</el-descriptions-item>
        <el-descriptions-item label="长期记忆">
          <el-tag :type="cfg.enableMemory ? 'success' : 'info'" size="small">{{ cfg.enableMemory ? "开启" : "关闭" }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="数据分析">{{ datasourceNames || "未启用" }}</el-descriptions-item>
        <el-descriptions-item label="工具" :span="2">{{ toolNames || "无" }}</el-descriptions-item>
        <el-descriptions-item label="知识库" :span="2">{{ datasetNames || "无" }}</el-descriptions-item>
      </el-descriptions>

      <div class="ad-block">
        <div class="ad-label">系统提示词</div>
        <pre class="ad-prompt">{{ cfg.prompt || "(未设置)" }}</pre>
      </div>
      <div v-if="cfg.prologue" class="ad-block">
        <div class="ad-label">开场白</div>
        <div class="ad-text">{{ cfg.prologue }}</div>
      </div>
      <div v-if="presetList.length" class="ad-block">
        <div class="ad-label">预设问题</div>
        <el-tag v-for="(q, i) in presetList" :key="i" effect="plain" class="ad-tag">{{ q }}</el-tag>
      </div>
      <div v-if="cmdList.length" class="ad-block">
        <div class="ad-label">快捷指令</div>
        <el-tag v-for="(c, i) in cmdList" :key="i" type="warning" effect="plain" class="ad-tag">{{ c.name }}</el-tag>
      </div>
    </div>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">关闭</el-button>
      <el-button icon="ChatDotRound" @click="$emit('chat', appId)">进入对话</el-button>
      <el-button type="primary" icon="Edit" @click="$emit('edit', appId)" v-hasPermi="['ai:app:edit']">编辑</el-button>
    </template>
  </el-dialog>
</template>

<script setup name="AppDetailDialog">
import { ref, reactive, computed } from "vue";
import { getApp } from "@/api/ai/app";
import { listModelAll } from "@/api/ai/model";
import { listTool } from "@/api/ai/tool";
import { listDataset } from "@/api/rag";
import { listSource } from "@/api/dataManage/data";

const props = defineProps({
  visible: { type: Boolean, default: false },
  appId: { type: [Number, String], default: null },
});
defineEmits(["update:visible", "edit", "chat"]);

const loading = ref(false);
const form = reactive({ name: "", description: "", status: "0" });
const cfg = ref({});
const modelOptions = ref([]);
const toolOptions = ref([]);
const datasetOptions = ref([]);
const sourceOptions = ref([]);

const presetList = computed(() => (cfg.value.presetQuestions || []).filter(Boolean));
const cmdList = computed(() => (cfg.value.quickCommands || []).filter((c) => c && c.name));
const modelName = computed(() => {
  const id = cfg.value.model?.modelId;
  if (!id) return "默认模型";
  const m = modelOptions.value.find((x) => x.modelId === id);
  return m ? m.modelName || m.modelCode : "模型#" + id;
});
const toolNames = computed(() =>
  (cfg.value.toolIds || []).map((id) => toolOptions.value.find((t) => t.toolId === id)?.name || "#" + id).join("、"),
);
const datasetNames = computed(() =>
  (cfg.value.datasetIds || []).map((id) => datasetOptions.value.find((d) => d.id === id)?.name || "#" + id).join("、"),
);
const datasourceNames = computed(() =>
  (cfg.value.datasourceCodes || []).map((c) => sourceOptions.value.find((s) => s.code === c)?.name || c).join("、"),
);

async function onOpen() {
  if (!props.appId) return;
  loading.value = true;
  try {
    const [res, models, tools, datasets, sources] = await Promise.all([
      getApp(props.appId),
      listModelAll(),
      listTool({ pageNum: 1, pageSize: 200 }),
      listDataset({ pageNum: 1, pageSize: 200 }),
      listSource({ pageNum: 1, pageSize: 200 }),
    ]);
    const d = res.data || {};
    Object.assign(form, { name: d.name, description: d.description, status: d.status || "0" });
    cfg.value = d.config || {};
    modelOptions.value = models.data || [];
    toolOptions.value = tools.rows || [];
    datasetOptions.value = datasets.rows || [];
    sourceOptions.value = sources.rows || [];
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped lang="scss">
.ad-body {
  max-height: 62vh;
  overflow-y: auto;
}
.ad-block {
  margin-top: 14px;
}
.ad-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 6px;
}
.ad-prompt {
  margin: 0;
  padding: 10px 12px;
  background: var(--el-fill-color-light);
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 220px;
  overflow-y: auto;
}
.ad-text {
  font-size: 13px;
  color: var(--el-text-color-regular);
}
.ad-tag {
  margin: 0 6px 6px 0;
}
</style>
