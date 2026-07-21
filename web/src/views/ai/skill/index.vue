<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item :label="$t('名称/代码')" prop="keyword">
        <el-input
          v-model="queryParams.keyword"
          :placeholder="$t('技能名称或代码')"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item :label="$t('状态')" prop="status">
        <el-select v-model="queryParams.status" :placeholder="$t('状态')" clearable style="width: 120px">
          <el-option :label="$t('启用')" value="0" />
          <el-option :label="$t('停用')" value="1" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">{{ $t('搜索') }}</el-button>
        <el-button icon="Refresh" @click="resetQuery">{{ $t('重置') }}</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['ai:skill:add']"
          >{{ $t('新增技能') }}</el-button
        >
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="skillList">
      <el-table-column :label="$t('名称')" align="center" prop="name" min-width="140" />
      <el-table-column :label="$t('代码')" align="center" prop="code" min-width="150" show-overflow-tooltip />
      <el-table-column :label="$t('描述')" align="center" prop="description" min-width="220" show-overflow-tooltip />
      <el-table-column :label="$t('文件')" align="center" width="80">
        <template #default="scope">
          <el-tag v-if="fileCount(scope.row) > 0" type="primary" effect="plain">{{ fileCount(scope.row) }} 个</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('引用')" align="center" width="80">
        <template #default="scope">
          <el-tag v-if="refCount(scope.row) > 0" type="success" effect="plain">{{ refCount(scope.row) }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('状态')" align="center" width="90">
        <template #default="scope">
          <el-tag :type="scope.row.status === '0' ? 'success' : 'info'">
            {{ scope.row.status === "0" ? "启用" : "停用" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('内置')" align="center" width="80">
        <template #default="scope">
          <el-tag v-if="scope.row.builtIn === '1'" type="warning">{{ $t('内置') }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('创建时间')" align="center" prop="createTime" width="160">
        <template #default="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('操作')" width="160" align="center" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['ai:skill:edit']"
            >{{ scope.row.builtIn === "1" ? "查看" : "修改" }}</el-button
          >
          <el-button
            v-if="scope.row.builtIn !== '1'"
            link
            type="danger"
            icon="Delete"
            @click="handleDelete(scope.row)"
            v-hasPermi="['ai:skill:remove']"
            >{{ $t('删除') }}</el-button
          >
        </template>
      </el-table-column>
    </el-table>

    <pagination
      v-show="total > 0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 全屏 IDE 式技能编辑器 -->
    <SkillEditor v-model="ed.visible" :skill-id="ed.id" @saved="getList" />
  </div>
</template>

<script setup name="AiSkill">
import { listSkill, delSkill } from "@/api/ai/skill";
import SkillEditor from "./SkillEditor.vue";
import { t as $t } from "@/lang";

const { proxy } = getCurrentInstance();

const skillList = ref([]);
const loading = ref(true);
const showSearch = ref(true);
const total = ref(0);
const ed = reactive({ visible: false, id: null });

const data = reactive({
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    keyword: undefined,
    status: undefined,
  },
});
const { queryParams } = toRefs(data);

/** 附加文件数(从 resources JSON 数组长度) */
function fileCount(row) {
  if (!row.resources) return 0;
  try {
    const arr = JSON.parse(row.resources);
    return Array.isArray(arr) ? arr.length : 0;
  } catch (e) {
    return 0;
  }
}
/** 引用技能数(refSkills 逗号分隔) */
function refCount(row) {
  return (row.refSkills || "").split(",").map((s) => s.trim()).filter(Boolean).length;
}

/** 查询列表 */
function getList() {
  loading.value = true;
  listSkill(queryParams.value).then((response) => {
    skillList.value = response.rows;
    total.value = response.total;
    loading.value = false;
  });
}

function handleQuery() {
  queryParams.value.pageNum = 1;
  getList();
}

function resetQuery() {
  proxy.resetForm("queryRef");
  handleQuery();
}

function handleAdd() {
  ed.id = null;
  ed.visible = true;
}

function handleUpdate(row) {
  ed.id = row.skillId;
  ed.visible = true;
}

/** 删除 */
function handleDelete(row) {
  proxy.$modal
    .confirm($t('是否确认删除技能"{name}"？', { name: row.name }))
    .then(() => delSkill(row.skillId))
    .then(() => {
      getList();
      proxy.$modal.msgSuccess($t("删除成功"));
    })
    .catch(() => {});
}

getList();
</script>
