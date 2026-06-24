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
      <div v-for="app in appList" :key="app.appId" class="app-card" @click="goChat(app)">
        <div class="app-card-head">
          <div class="app-avatar"><el-icon><Cpu /></el-icon></div>
          <div class="app-meta">
            <div class="app-name">{{ app.name }}</div>
            <el-tag size="small" :type="app.status === '0' ? 'success' : 'info'">
              {{ app.status === "0" ? "已发布" : "草稿" }}
            </el-tag>
          </div>
        </div>
        <div class="app-desc">{{ app.description || "暂无描述" }}</div>
        <div class="app-card-foot" @click.stop>
          <el-button type="primary" link icon="ChatDotRound" @click="goChat(app)">进入对话</el-button>
          <span style="flex: 1"></span>
          <el-button type="primary" link icon="Edit" @click="handleEdit(app)" v-hasPermi="['ai:app:edit']">编辑</el-button>
          <el-button type="danger" link icon="Delete" @click="handleDelete(app)" v-hasPermi="['ai:app:remove']">删除</el-button>
        </div>
      </div>
      <el-empty v-if="!loading && appList.length === 0" description="暂无应用,点「新建应用」创建" style="width: 100%" />
    </div>

    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <AppEditDialog v-model:visible="editOpen" :app-id="editAppId" @success="getList" />
  </div>
</template>

<script setup name="AiApp">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { listApp, delApp } from "@/api/ai/app";
import AppEditDialog from "./components/AppEditDialog.vue";

const { proxy } = getCurrentInstance();
const router = useRouter();

const appList = ref([]);
const total = ref(0);
const loading = ref(true);
const editOpen = ref(false);
const editAppId = ref(null);
const queryParams = reactive({ pageNum: 1, pageSize: 12, keyword: undefined });

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
  editAppId.value = null;
  editOpen.value = true;
}
function handleEdit(app) {
  editAppId.value = app.appId;
  editOpen.value = true;
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
