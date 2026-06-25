<template>
  <div class="app-container">
    <el-form :model="queryParams" :inline="true">
      <el-form-item label="关键字">
        <el-input v-model="queryParams.keyword" placeholder="名称/描述" clearable style="width: 220px" @keyup.enter="getList" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="getList">搜索</el-button>
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['ai:app:add']">新建应用</el-button>
      </el-form-item>
    </el-form>

    <div v-loading="loading" class="app-grid">
      <div v-for="app in appList" :key="app.appId" class="app-card" @click="openDetail(app)">
        <div class="app-card-head">
          <div class="app-avatar"><el-icon><Cpu /></el-icon></div>
          <div class="app-meta">
            <div class="app-name">{{ app.name }}</div>
            <el-switch
              v-model="app.status"
              active-value="0"
              inactive-value="1"
              inline-prompt
              active-text="发布"
              inactive-text="草稿"
              size="small"
              @click.stop
              @change="handlePublish(app)"
            />
          </div>
        </div>
        <div class="app-desc">{{ app.description || "暂无描述" }}</div>
        <div class="app-card-foot" @click.stop>
          <el-tooltip content="进入对话" placement="top">
            <el-button type="primary" link icon="ChatDotRound" @click="goChat(app)" />
          </el-tooltip>
          <span style="flex: 1"></span>
          <el-tooltip content="API Key" placement="top">
            <el-button type="primary" link icon="Key" @click="openTokens(app)" v-hasPermi="['ai:app:edit']" />
          </el-tooltip>
          <el-tooltip content="编辑" placement="top">
            <el-button type="primary" link icon="Edit" @click="handleEdit(app)" v-hasPermi="['ai:app:edit']" />
          </el-tooltip>
          <el-tooltip content="删除" placement="top">
            <el-button type="danger" link icon="Delete" @click="handleDelete(app)" v-hasPermi="['ai:app:remove']" />
          </el-tooltip>
        </div>
      </div>
      <el-empty v-if="!loading && appList.length === 0" description="暂无应用,点「新建应用」创建" style="width: 100%" />
    </div>

    <TokenDialog v-model:visible="tokenOpen" :app-id="tokenAppId" />
    <AppDetailDialog v-model:visible="detailOpen" :app-id="detailAppId" @edit="handleEditById" @chat="goChatById" />

    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

  </div>
</template>

<script setup name="AiApp">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { listApp, delApp, updateApp } from "@/api/ai/app";
import TokenDialog from "./components/TokenDialog.vue";
import AppDetailDialog from "./components/AppDetailDialog.vue";

const { proxy } = getCurrentInstance();
const router = useRouter();

const appList = ref([]);
const total = ref(0);
const loading = ref(true);
const tokenOpen = ref(false);
const tokenAppId = ref(null);
const detailOpen = ref(false);
const detailAppId = ref(null);
const queryParams = reactive({ pageNum: 1, pageSize: 12, keyword: undefined });

function openDetail(app) {
  detailAppId.value = app.appId;
  detailOpen.value = true;
}

function openTokens(app) {
  tokenAppId.value = app.appId;
  tokenOpen.value = true;
}
function handlePublish(app) {
  updateApp({ appId: app.appId, name: app.name, status: app.status })
    .then(() => proxy.$modal.msgSuccess(app.status === "0" ? "已发布" : "已转草稿"))
    .catch(() => {
      app.status = app.status === "0" ? "1" : "0";
    });
}

function getList() {
  loading.value = true;
  listApp(queryParams)
    .then((res) => {
      appList.value = res.rows || [];
      total.value = res.total || 0;
    })
    .finally(() => (loading.value = false));
}

function handleAdd() {
  router.push("/ai/app/edit");
}
function handleEdit(app) {
  router.push("/ai/app/edit/" + app.appId);
}
function handleEditById(appId) {
  router.push("/ai/app/edit/" + appId);
}
function goChatById(appId) {
  router.push("/ai/app/chat/" + appId);
}
function handleDelete(app) {
  proxy.$modal
    .confirm('是否确认删除应用"' + app.name + '"？')
    .then(() => delApp(app.appId))
    .then(() => {
      getList();
      proxy.$modal.msgSuccess("删除成功");
    })
    .catch(() => {});
}
function goChat(app) {
  router.push("/ai/app/chat/" + app.appId);
}

getList();
</script>

<style scoped lang="scss">
.app-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 8px;
}
.app-card {
  border: 1px solid var(--el-border-color-light);
  border-radius: 12px;
  padding: 16px;
  background: var(--el-bg-color);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 10px;
  &:hover {
    border-color: var(--el-color-primary-light-5);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    transform: translateY(-2px);
  }
}
.app-card-head {
  display: flex;
  align-items: center;
  gap: 12px;
}
.app-avatar {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #fff;
  background: linear-gradient(135deg, var(--el-color-primary), var(--el-color-primary-light-3));
}
.app-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.app-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.app-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  height: 38px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.app-card-foot {
  display: flex;
  align-items: center;
  border-top: 1px solid var(--el-border-color-lighter);
  padding-top: 8px;
}
</style>
