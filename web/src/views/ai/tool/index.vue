<template>
  <div class="app-container">
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch">
      <el-form-item label="名称/代码" prop="keyword">
        <el-input
          v-model="queryParams.keyword"
          placeholder="工具名称或代码"
          clearable
          style="width: 200px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="类型" prop="toolType">
        <el-select v-model="queryParams.toolType" placeholder="工具类型" clearable style="width: 160px">
          <el-option label="MCP工具" value="mcp" />
          <el-option label="内置工具" value="builtin" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button type="primary" plain icon="Plus" @click="handleAdd" v-hasPermi="['ai:tool:add']"
          >新增工具</el-button
        >
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="toolList">
      <el-table-column label="名称" align="center" prop="name" min-width="140" />
      <el-table-column label="代码" align="center" prop="code" min-width="160" show-overflow-tooltip />
      <el-table-column label="类型" align="center" prop="toolType" width="100">
        <template #default="scope">
          <el-tag :type="scope.row.toolType === 'builtin' ? 'info' : 'success'">
            {{ scope.row.toolType === "builtin" ? "内置" : "MCP" }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="描述" align="center" prop="description" min-width="200" show-overflow-tooltip />
      <el-table-column label="创建时间" align="center" prop="createTime" width="160">
        <template #default="scope">
          <span>{{ parseTime(scope.row.createTime) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160" align="center" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['ai:tool:edit']"
            >{{ scope.row.builtIn === "1" ? "查看" : "修改" }}</el-button
          >
          <el-button
            v-if="scope.row.builtIn !== '1'"
            link
            type="danger"
            icon="Delete"
            @click="handleDelete(scope.row)"
            v-hasPermi="['ai:tool:remove']"
            >删除</el-button
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

    <!-- 添加或修改对话框 -->
    <el-dialog :title="title" v-model="open" width="720px" append-to-body>
      <el-form ref="toolRef" :model="form" :rules="rules" label-width="100px">
        <el-row :gutter="10">
          <el-col :span="12">
            <el-form-item label="工具名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入工具名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工具代码" prop="code">
              <el-input v-model="form.code" placeholder="英文唯一标识" :disabled="isBuiltin || isUpdate" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="类型" prop="toolType">
              <el-select v-model="form.toolType" style="width: 100%" disabled>
                <el-option label="MCP工具" value="mcp" />
                <el-option label="内置工具" value="builtin" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="描述" prop="description">
              <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入工具描述" />
            </el-form-item>
          </el-col>

          <!-- MCP 配置 -->
          <template v-if="form.toolType === 'mcp'">
            <el-col :span="24"><el-divider content-position="left">MCP 连接配置</el-divider></el-col>
            <el-col :span="12">
              <el-form-item label="服务器类型">
                <el-select v-model="form.args.server_type" style="width: 100%">
                  <el-option label="STDIO(本地进程)" value="stdio" />
                  <el-option label="SSE" value="sse" />
                  <el-option label="Streamable HTTP" value="http" />
                </el-select>
              </el-form-item>
            </el-col>

            <template v-if="form.args.server_type === 'stdio'">
              <el-col :span="24">
                <el-form-item label="执行命令">
                  <el-input v-model="form.args.command" placeholder="如: npx / python / uvx" />
                </el-form-item>
              </el-col>
              <el-col :span="24">
                <el-form-item label="命令参数">
                  <el-input
                    v-model="argsJson"
                    type="textarea"
                    :rows="2"
                    placeholder='JSON 数组,如 ["-y","@modelcontextprotocol/server-filesystem","/data"]'
                  />
                </el-form-item>
              </el-col>
              <el-col :span="24">
                <el-form-item label="环境变量">
                  <el-input v-model="envJson" type="textarea" :rows="2" placeholder='JSON 对象,如 {"TOKEN":"xxx"}' />
                </el-form-item>
              </el-col>
            </template>

            <template v-else>
              <el-col :span="24">
                <el-form-item label="服务器URL">
                  <el-input v-model="form.args.url" placeholder="http(s)://host:port/sse 或 /mcp" />
                </el-form-item>
              </el-col>
              <el-col :span="24">
                <el-form-item label="请求头">
                  <el-input
                    v-model="headersJson"
                    type="textarea"
                    :rows="2"
                    placeholder='JSON 对象,如 {"Authorization":"Bearer xxx"}'
                  />
                </el-form-item>
              </el-col>
            </template>

            <el-col :span="24" v-if="testResult">
              <el-alert
                :title="`连接成功,发现 ${testResult.count} 个工具: ${testResult.tools.join(', ')}`"
                type="success"
                :closable="false"
              />
            </el-col>
          </template>
        </el-row>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button v-if="form.toolType === 'mcp'" :loading="testing" @click="handleTest">测试连接</el-button>
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup name="AiTool">
import { listTool, addTool, delTool, getTool, updateTool, testTool } from "@/api/ai/tool";

const { proxy } = getCurrentInstance();

const toolList = ref([]);
const open = ref(false);
const loading = ref(true);
const showSearch = ref(true);
const total = ref(0);
const title = ref("");
const isUpdate = ref(false);
const testing = ref(false);
const testResult = ref(null);

const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    keyword: undefined,
    toolType: undefined,
  },
  rules: {
    name: [{ required: true, message: "工具名称不能为空", trigger: "blur" }],
    code: [{ required: true, message: "工具代码不能为空", trigger: "blur" }],
  },
});

const { queryParams, form, rules } = toRefs(data);

// MCP 的 命令参数/环境变量/请求头 用 JSON 文本编辑,提交/测试时解析
const argsJson = ref("[]");
const envJson = ref("{}");
const headersJson = ref("{}");

const isBuiltin = computed(() => form.value.builtIn === "1");

function parseJson(str, fallback) {
  const s = (str || "").trim();
  if (!s) return fallback;
  try {
    return JSON.parse(s);
  } catch (e) {
    return undefined; // 标记解析失败
  }
}

/** 把 JSON 文本收敛进 form.args,返回组装好的 args(失败返回 null 并提示) */
function buildArgs() {
  const a = form.value.args || {};
  if (a.server_type === "stdio") {
    const argsArr = parseJson(argsJson.value, []);
    const env = parseJson(envJson.value, {});
    if (argsArr === undefined) return proxy.$modal.msgError("命令参数不是合法 JSON 数组"), null;
    if (env === undefined) return proxy.$modal.msgError("环境变量不是合法 JSON 对象"), null;
    return { server_type: "stdio", command: a.command || "", args: argsArr, env };
  }
  const headers = parseJson(headersJson.value, {});
  if (headers === undefined) return proxy.$modal.msgError("请求头不是合法 JSON 对象"), null;
  return { server_type: a.server_type, url: a.url || "", headers };
}

/** 查询列表 */
function getList() {
  loading.value = true;
  listTool(queryParams.value).then((response) => {
    toolList.value = response.rows;
    total.value = response.total;
    loading.value = false;
  });
}

function cancel() {
  open.value = false;
  reset();
}

function reset() {
  form.value = {
    toolId: undefined,
    name: undefined,
    code: undefined,
    toolType: "mcp",
    description: undefined,
    args: { server_type: "stdio", command: "", url: "" },
    status: "0",
    builtIn: "0",
  };
  argsJson.value = "[]";
  envJson.value = "{}";
  headersJson.value = "{}";
  testResult.value = null;
  isUpdate.value = false;
  proxy.resetForm("toolRef");
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
  reset();
  open.value = true;
  title.value = "新增工具";
}

function handleUpdate(row) {
  reset();
  getTool(row.toolId).then((response) => {
    const d = response.data || {};
    const a = d.args && typeof d.args === "object" ? d.args : {};
    form.value = {
      ...d,
      args: { server_type: a.server_type || "stdio", command: a.command || "", url: a.url || "" },
    };
    argsJson.value = JSON.stringify(a.args || [], null, 0);
    envJson.value = JSON.stringify(a.env || {}, null, 0);
    headersJson.value = JSON.stringify(a.headers || {}, null, 0);
    isUpdate.value = true;
    open.value = true;
    title.value = d.builtIn === "1" ? "查看内置工具" : "修改工具";
  });
}

/** 测试 MCP 连接 */
function handleTest() {
  const args = buildArgs();
  if (!args) return;
  testing.value = true;
  testResult.value = null;
  testTool({ toolType: "mcp", args })
    .then((res) => {
      testResult.value = res.data;
      proxy.$modal.msgSuccess(`连接成功,发现 ${res.data.count} 个工具`);
    })
    .finally(() => {
      testing.value = false;
    });
}

/** 提交 */
function submitForm() {
  proxy.$refs["toolRef"].validate((valid) => {
    if (!valid) return;
    const payload = { ...form.value };
    if (form.value.toolType === "mcp") {
      const args = buildArgs();
      if (!args) return;
      payload.args = args;
    } else {
      payload.args = form.value.args || {};
    }
    const action = form.value.toolId != undefined ? updateTool : addTool;
    action(payload).then(() => {
      proxy.$modal.msgSuccess(form.value.toolId != undefined ? "修改成功" : "新增成功");
      open.value = false;
      getList();
    });
  });
}

/** 删除 */
function handleDelete(row) {
  proxy.$modal
    .confirm('是否确认删除工具"' + row.name + '"？')
    .then(() => delTool(row.toolId))
    .then(() => {
      getList();
      proxy.$modal.msgSuccess("删除成功");
    })
    .catch(() => {});
}

getList();
</script>
