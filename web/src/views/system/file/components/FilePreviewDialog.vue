<template>
  <el-dialog
    v-model="visible"
    :title="`预览 - ${file?.originalName || ''}`"
    width="70%"
    top="6vh"
    append-to-body
    @closed="cleanup"
  >
    <div v-loading="loading" class="file-preview-body">
      <template v-if="objectUrl">
        <img v-if="kind === 'image'" :src="objectUrl" class="preview-media" alt="preview" />
        <video v-else-if="kind === 'video'" :src="objectUrl" class="preview-media" controls />
        <audio v-else-if="kind === 'audio'" :src="objectUrl" controls style="width: 100%" />
        <iframe v-else-if="kind === 'pdf'" :src="objectUrl" class="preview-frame" />
        <pre v-else-if="kind === 'text'" class="preview-text">{{ textContent }}</pre>
        <el-empty v-else description="该文件类型暂不支持预览，请下载查看" />
      </template>
      <el-empty v-else-if="!loading" :description="errorMsg || '无法预览'" />
    </div>
    <template #footer>
      <el-button @click="visible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup name="FilePreviewDialog">
import { previewFile } from "@/api/system/file";

const visible = ref(false);
const loading = ref(false);
const objectUrl = ref("");
const textContent = ref("");
const errorMsg = ref("");
const file = ref(null);
const { proxy } = getCurrentInstance();

// 由 contentType(优先)或扩展名推断预览类型
const kind = computed(() => {
  const ct = (file.value?.contentType || "").toLowerCase();
  const ext = (file.value?.extension || "").toLowerCase();
  if (ct.startsWith("image/") || ["png", "jpg", "jpeg", "gif", "bmp", "webp", "svg"].includes(ext)) return "image";
  if (ct.startsWith("video/") || ["mp4", "webm", "ogg", "mov"].includes(ext)) return "video";
  if (ct.startsWith("audio/") || ["mp3", "wav", "flac", "aac"].includes(ext)) return "audio";
  if (ct === "application/pdf" || ext === "pdf") return "pdf";
  if (ct.startsWith("text/") || ["txt", "json", "csv", "log", "md"].includes(ext)) return "text";
  return "other";
});

function cleanup() {
  if (objectUrl.value) {
    URL.revokeObjectURL(objectUrl.value);
    objectUrl.value = "";
  }
  textContent.value = "";
  errorMsg.value = "";
}

async function open(row) {
  cleanup();
  file.value = row;
  visible.value = true;
  loading.value = true;
  try {
    const res = await previewFile(row.fileId, row.storedName);
    const blob = res instanceof Blob ? res : res?.data instanceof Blob ? res.data : new Blob([res]);
    if (kind.value === "text") {
      textContent.value = await blob.text();
    } else if (kind.value !== "other") {
      objectUrl.value = URL.createObjectURL(blob);
    }
  } catch (e) {
    errorMsg.value = "预览加载失败";
    proxy?.$modal?.msgError?.("预览加载失败");
  } finally {
    loading.value = false;
  }
}

defineExpose({ open });
</script>

<style scoped>
.file-preview-body {
  min-height: 240px;
  max-height: 68vh;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: center;
}
.preview-media {
  max-width: 100%;
  max-height: 66vh;
}
.preview-frame {
  width: 100%;
  height: 66vh;
  border: none;
}
.preview-text {
  width: 100%;
  white-space: pre-wrap;
  word-break: break-all;
  text-align: left;
}
</style>
