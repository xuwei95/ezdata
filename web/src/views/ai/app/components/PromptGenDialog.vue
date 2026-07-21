<template>
  <el-dialog
    :model-value="modelValue"
    :title="$t('AI 生成提示词')"
    width="660px"
    :close-on-click-modal="false"
    append-to-body
    @update:model-value="$emit('update:modelValue', $event)"
    @open="onOpen"
  >
    <div class="pg-body">
      <div class="pg-req">
        <el-input
          v-model="requirement"
          type="textarea"
          :rows="2"
          :placeholder="$t('一句话描述应用定位/角色,例如:小咖啡店的智能客服,负责答疑、推荐饮品')"
        />
        <el-button type="primary" :loading="generating" :disabled="!requirement.trim()" @click="doGenerate">
          {{ output ? "重新生成" : "生成" }}
        </el-button>
      </div>
      <div class="pg-out-label">
        <span>{{ $t('生成结果(确认前可直接编辑)') }}</span>
        <span v-if="generating" class="pg-typing">{{ $t('AI 正在书写…') }}</span>
      </div>
      <el-input
        v-model="output"
        type="textarea"
        :autosize="{ minRows: 9, maxRows: 18 }"
        :placeholder="$t('点击「生成」后,AI 将实时逐字写出系统提示词…')"
        class="pg-out"
      />
    </div>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">{{ $t('取消') }}</el-button>
      <el-button type="primary" :disabled="!output.trim() || generating" @click="apply">{{ $t('应用到提示词') }}</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { getToken } from "@/utils/auth";

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  modelId: { type: [Number, String], default: 0 },
  initialRequirement: { type: String, default: "" },
});
const emit = defineEmits(["update:modelValue", "apply"]);
const apiBase = import.meta.env.VITE_APP_BASE_API || "";

const requirement = ref("");
const output = ref("");
const generating = ref(false);

function onOpen() {
  if (!requirement.value) requirement.value = props.initialRequirement || "";
}

// 流式拉取生成结果:逐块追加,实现"吐字"效果(不直接改外部提示词,确认后才回填)
async function doGenerate() {
  if (!requirement.value.trim() || generating.value) return;
  generating.value = true;
  output.value = "";
  try {
    const resp = await fetch(apiBase + "/ai/app/prompt/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + getToken() },
      body: JSON.stringify({ requirement: requirement.value, modelId: props.modelId || 0 }),
    });
    if (!resp.ok || !resp.body) {
      ElMessage.error("生成失败: HTTP " + resp.status);
      return;
    }
    const reader = resp.body.getReader();
    const dec = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      output.value += dec.decode(value, { stream: true });
    }
  } catch (e) {
    ElMessage.error("生成失败: " + (e?.message || e));
  } finally {
    generating.value = false;
  }
}

function apply() {
  if (!output.value.trim()) return;
  emit("apply", output.value);
  emit("update:modelValue", false);
}
</script>

<style scoped lang="scss">
.pg-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.pg-req {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  :deep(.el-textarea) {
    flex: 1;
  }
}
.pg-out-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.pg-typing {
  color: var(--el-color-primary);
  animation: pg-blink 1.2s infinite;
}
@keyframes pg-blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.4;
  }
}
</style>
