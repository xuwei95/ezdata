<template>
  <el-dialog v-model="visible" :title="$t('API Key 管理')" width="640px" append-to-body @open="onOpen">
    <div style="margin-bottom: 10px; display: flex; align-items: center; gap: 8px">
      <el-button type="primary" icon="Plus" :loading="loading" @click="apply">{{ $t('申请 API Key') }}</el-button>
      <span style="color: var(--el-text-color-secondary); font-size: 12px">{{ $t('用于外部系统调用本应用') }}</span>
    </div>
    <el-table :data="tokens" size="small" v-loading="loading" :empty-text="$t('暂无 API Key')">
      <el-table-column :label="$t('名称')" prop="name" width="110" show-overflow-tooltip />
      <el-table-column label="API Key" prop="token" show-overflow-tooltip>
        <template #default="{ row }">
          <span style="font-family: monospace; font-size: 12px">{{ row.token }}</span>
          <el-button link type="primary" size="small" @click="copy(row.token)">{{ $t('复制') }}</el-button>
        </template>
      </el-table-column>
      <el-table-column :label="$t('创建时间')" prop="createTime" width="160" />
      <el-table-column :label="$t('操作')" width="60">
        <template #default="{ row }">
          <el-button link type="danger" size="small" @click="remove(row.id)">{{ $t('删除') }}</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="token-hint">
      调用:POST {{ apiBase }}/ai/app/api/chat,Header「X-API-Key: 上面的 key」,body
      {"message":"你好"}(流式返回)
    </div>
  </el-dialog>
</template>

<script setup name="TokenDialog">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { listToken, addToken, delToken } from "@/api/apitoken/token";

const visible = defineModel("visible", { type: Boolean, default: false });
const props = defineProps({ appId: { type: [Number, String], default: null } });

const tokens = ref([]);
const loading = ref(false);
const apiBase = import.meta.env.VITE_APP_BASE_API || "";

function onOpen() {
  load();
}
function load() {
  if (!props.appId) return;
  loading.value = true;
  listToken({ tokenType: "ai_app", refId: String(props.appId), pageNum: 1, pageSize: 50 })
    .then((res) => (tokens.value = res.rows || []))
    .finally(() => (loading.value = false));
}
function apply() {
  loading.value = true;
  addToken({ tokenType: "ai_app", refId: String(props.appId), name: "key" + (tokens.value.length + 1) })
    .then(() => {
      ElMessage.success("已生成");
      load();
    })
    .finally(() => (loading.value = false));
}
function remove(id) {
  delToken(id).then(() => load());
}
function copy(t) {
  navigator.clipboard?.writeText(t);
  ElMessage.success("已复制");
}
</script>

<style scoped>
.token-hint {
  margin-top: 10px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  word-break: break-all;
}
</style>
