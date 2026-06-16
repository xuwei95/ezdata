<template>
  <div class="notice-user-select">
    <el-input
      v-model="text"
      :placeholder="placeholder"
      size="small"
      readonly
      class="nus-input"
      @click="open"
    >
      <template #append>
        <el-button icon="User" @click="open">选择</el-button>
      </template>
    </el-input>

    <el-dialog v-model="visible" title="选择通知用户" width="860px" append-to-body destroy-on-close>
      <div class="nus-body">
        <!-- 左：分组(部门/角色/岗位) -->
        <div class="nus-groups">
          <el-tabs v-model="activeTab" @tab-change="onTabChange">
            <el-tab-pane label="部门" name="dept">
              <el-scrollbar height="380px">
                <el-tree
                  :data="deptOptions"
                  :props="{ label: 'label', children: 'children' }"
                  node-key="id"
                  highlight-current
                  :expand-on-click-node="false"
                  default-expand-all
                  @node-click="onDeptClick"
                />
              </el-scrollbar>
            </el-tab-pane>
            <el-tab-pane label="角色" name="role">
              <el-scrollbar height="380px">
                <div
                  v-for="r in roleOptions"
                  :key="r.roleId"
                  class="nus-group-item"
                  :class="{ active: filter.roleId === r.roleId }"
                  @click="onRoleClick(r)"
                >{{ r.roleName }}</div>
              </el-scrollbar>
            </el-tab-pane>
            <el-tab-pane label="岗位" name="post">
              <el-scrollbar height="380px">
                <div
                  v-for="p in postOptions"
                  :key="p.postId"
                  class="nus-group-item"
                  :class="{ active: filter.postId === p.postId }"
                  @click="onPostClick(p)"
                >{{ p.postName }}</div>
              </el-scrollbar>
            </el-tab-pane>
          </el-tabs>
        </div>

        <!-- 右：用户列表 -->
        <div class="nus-users">
          <div class="nus-toolbar">
            <el-input
              v-model="queryParams.userName"
              placeholder="用户名/昵称"
              size="small"
              clearable
              style="width: 180px"
              @keyup.enter="handleQuery"
            />
            <el-button size="small" type="primary" icon="Search" @click="handleQuery">查询</el-button>
            <el-button size="small" icon="Refresh" @click="resetFilter">全部用户</el-button>
            <el-button size="small" type="success" plain icon="Plus" @click="selectAllCurrent">选择当前条件全部</el-button>
          </div>

          <el-table v-loading="loading" :data="userList" height="300" size="small">
            <el-table-column width="50">
              <template #default="scope">
                <el-checkbox
                  :model-value="isSelected(scope.row.userName)"
                  @change="toggle(scope.row.userName)"
                />
              </template>
            </el-table-column>
            <el-table-column label="用户名" prop="userName" show-overflow-tooltip />
            <el-table-column label="昵称" prop="nickName" show-overflow-tooltip />
            <el-table-column label="部门" prop="dept.deptName" show-overflow-tooltip />
          </el-table>
          <pagination
            v-show="total > 0"
            :total="total"
            v-model:page="queryParams.pageNum"
            v-model:limit="queryParams.pageSize"
            :page-sizes="[10, 20, 50]"
            @pagination="getList"
          />

          <div class="nus-selected">
            <span class="nus-selected__title">已选 ({{ selected.length }})：</span>
            <el-tag
              v-for="n in selected"
              :key="n"
              closable
              size="small"
              class="nus-tag"
              @close="remove(n)"
            >{{ n }}</el-tag>
            <el-button v-if="selected.length" link type="danger" size="small" @click="selected = []">清空</el-button>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="visible = false">取 消</el-button>
        <el-button type="primary" @click="confirm">确 定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="NoticeUserSelect">
import { listUser, deptTreeSelect } from '@/api/system/user'
import { listRole } from '@/api/system/role'
import { listPost } from '@/api/system/post'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '点击右侧按钮选择通知用户' }
})
const emit = defineEmits(['update:modelValue'])

const text = ref(props.modelValue || '')
watch(() => props.modelValue, v => { if ((v || '') !== text.value) text.value = v || '' })

const visible = ref(false)
const activeTab = ref('dept')
const deptOptions = ref([])
const roleOptions = ref([])
const postOptions = ref([])
const filter = reactive({ deptId: undefined, roleId: undefined, postId: undefined })
const queryParams = reactive({ pageNum: 1, pageSize: 10, userName: undefined })
const userList = ref([])
const total = ref(0)
const loading = ref(false)
const selected = ref([])

function parseNames(str) {
  return (str || '').split(',').map(s => s.trim()).filter(Boolean)
}
function isSelected(name) {
  return selected.value.includes(name)
}
function toggle(name) {
  if (!name) return
  const i = selected.value.indexOf(name)
  if (i >= 0) selected.value.splice(i, 1)
  else selected.value.push(name)
}
function remove(name) {
  const i = selected.value.indexOf(name)
  if (i >= 0) selected.value.splice(i, 1)
}

async function open() {
  selected.value = parseNames(text.value)
  visible.value = true
  resetFilter(false)
  // 懒加载分组数据
  if (!deptOptions.value.length) {
    deptTreeSelect().then(res => { deptOptions.value = res.data || [] })
  }
  if (!roleOptions.value.length) {
    listRole({ pageNum: 1, pageSize: 999 }).then(res => { roleOptions.value = res.rows || [] })
  }
  if (!postOptions.value.length) {
    listPost({ pageNum: 1, pageSize: 999 }).then(res => { postOptions.value = res.rows || [] })
  }
}

function currentFilter() {
  const f = {}
  if (filter.deptId) f.deptId = filter.deptId
  if (filter.roleId) f.roleId = filter.roleId
  if (filter.postId) f.postId = filter.postId
  return f
}

function getList() {
  loading.value = true
  listUser({ ...currentFilter(), userName: queryParams.userName, pageNum: queryParams.pageNum, pageSize: queryParams.pageSize })
    .then(res => {
      userList.value = res.rows || []
      total.value = res.total || 0
    })
    .finally(() => { loading.value = false })
}

function handleQuery() {
  queryParams.pageNum = 1
  getList()
}

function resetFilter(reload = true) {
  filter.deptId = undefined
  filter.roleId = undefined
  filter.postId = undefined
  queryParams.userName = undefined
  queryParams.pageNum = 1
  if (reload) getList()
  else getList()
}

function onTabChange() {
  // 切换分组类型时清空其它筛选
}
function onDeptClick(data) {
  filter.deptId = data.id
  filter.roleId = undefined
  filter.postId = undefined
  queryParams.pageNum = 1
  getList()
}
function onRoleClick(r) {
  filter.roleId = r.roleId
  filter.deptId = undefined
  filter.postId = undefined
  queryParams.pageNum = 1
  getList()
}
function onPostClick(p) {
  filter.postId = p.postId
  filter.deptId = undefined
  filter.roleId = undefined
  queryParams.pageNum = 1
  getList()
}

// 选择当前筛选条件下的全部用户(快照展开为用户名)
function selectAllCurrent() {
  listUser({ ...currentFilter(), userName: queryParams.userName, pageNum: 1, pageSize: 9999 }).then(res => {
    for (const u of res.rows || []) {
      if (u.userName && !selected.value.includes(u.userName)) selected.value.push(u.userName)
    }
  })
}

function confirm() {
  const val = Array.from(new Set(selected.value)).join(',')
  text.value = val
  emit('update:modelValue', val)
  visible.value = false
}
</script>

<style scoped>
.nus-input :deep(.el-input__inner) {
  cursor: pointer;
}
.nus-body {
  display: flex;
  gap: 12px;
}
.nus-groups {
  width: 240px;
  border: 1px solid var(--el-border-color-lighter, #ebeef5);
  border-radius: 4px;
  padding: 0 8px;
}
.nus-users {
  flex: 1;
  min-width: 0;
}
.nus-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.nus-group-item {
  padding: 6px 8px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 13px;
}
.nus-group-item:hover {
  background: var(--el-fill-color-light, #f5f7fa);
}
.nus-group-item.active {
  background: var(--el-color-primary-light-9, #ecf5ff);
  color: var(--el-color-primary, #409eff);
}
.nus-selected {
  margin-top: 8px;
  max-height: 90px;
  overflow-y: auto;
}
.nus-selected__title {
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
}
.nus-tag {
  margin: 2px 4px 2px 0;
}
</style>
