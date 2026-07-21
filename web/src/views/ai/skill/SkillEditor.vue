<template>
  <el-dialog
    v-model="visible"
    :title="form.skillId ? $t('编辑技能') : $t('新建技能')"
    fullscreen
    append-to-body
    :close-on-click-modal="false"
    class="skill-editor-dialog"
  >
    <div class="skill-editor">
      <!-- 顶部工具条 -->
      <div class="se-head">
        <el-input v-model="form.name" :placeholder="$t('技能名称')" :disabled="isBuiltin" style="width: 220px" />
        <el-input v-model="form.code" :placeholder="$t('技能代码(唯一)')" :disabled="isBuiltin || isUpdate" style="width: 200px" />
        <el-switch v-model="form.status" active-value="0" inactive-value="1" :disabled="isBuiltin" :active-text="$t('启用')" :inactive-text="$t('停用')" inline-prompt />
        <div class="se-head-right">
          <el-dropdown v-if="!isBuiltin" trigger="click" @command="onImportCmd">
            <el-button icon="Upload">{{ $t('导入') }}<el-icon class="el-icon--right"><arrow-down /></el-icon></el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="dir">{{ $t('导入文件夹(Skill 目录)') }}</el-dropdown-item>
                <el-dropdown-item command="zip">{{ $t('导入 .zip 包') }}</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button icon="Download" @click="exportZip">{{ $t('导出') }}</el-button>
          <el-button v-if="!isBuiltin" type="primary" icon="Check" :loading="saving" @click="save">{{ $t('保存') }}</el-button>
          <el-button @click="visible = false">{{ $t('关闭') }}</el-button>
        </div>
      </div>

      <div class="se-body">
        <!-- 左:文件树 -->
        <div class="se-left">
          <div class="se-left-head">
            <span>{{ $t('技能文件') }}</span>
            <el-button v-if="!isBuiltin" link type="primary" icon="DocumentAdd" :title="$t('新建文件')" @click="addFile('')">{{ $t('新建') }}</el-button>
          </div>
          <el-tree
            ref="treeRef"
            :data="treeData"
            node-key="id"
            :expand-on-click-node="false"
            :current-node-key="selectedKey"
            highlight-current
            default-expand-all
            @node-click="onNodeClick"
          >
            <template #default="{ node, data }">
              <span class="se-node">
                <el-icon class="se-node-icon"><component :is="nodeIcon(data)" /></el-icon>
                <span class="se-node-label">{{ node.label }}</span>
                <span v-if="!isBuiltin && (data.kind === 'file' || data.kind === 'dir')" class="se-node-actions">
                  <el-icon v-if="data.kind === 'dir'" :title="$t('在此新建文件')" @click.stop="addFile(data.path)"><plus /></el-icon>
                  <el-icon :title="$t('重命名')" @click.stop="renameNode(data)"><edit-pen /></el-icon>
                  <el-icon :title="$t('删除')" @click.stop="deleteNode(data)"><delete /></el-icon>
                </span>
              </span>
            </template>
          </el-tree>
        </div>

        <!-- 右:编辑区 -->
        <div class="se-right">
          <!-- 基础信息 -->
          <div v-if="selectedKey === '__info__'" class="se-info">
            <el-form label-width="140px" style="max-width: 720px">
              <el-form-item :label="$t('技能名称')" required>
                <el-input v-model="form.name" :disabled="isBuiltin" :placeholder="$t('请输入技能名称')" />
              </el-form-item>
              <el-form-item :label="$t('技能代码')" required>
                <el-input v-model="form.code" :disabled="isBuiltin || isUpdate" :placeholder="$t('英文唯一标识,供 load_skill 引用')" />
              </el-form-item>
              <el-form-item :label="$t('描述')" required>
                <el-input
                  v-model="form.description"
                  type="textarea"
                  :rows="3"
                  :disabled="isBuiltin"
                  :placeholder="$t('常驻上下文,决定何时被选用。写清「这个技能用来做什么、什么场景该用」')"
                />
              </el-form-item>
              <el-form-item :label="$t('类型')">
                <el-radio-group v-model="form.skillType" :disabled="isBuiltin">
                  <el-radio label="process">{{ $t('流程型(全局)') }}</el-radio>
                  <el-radio label="knowledge">{{ $t('知识型(按源浮现)') }}</el-radio>
                </el-radio-group>
                <div class="se-hint" style="width: 100%; margin-left: 0"> {{ $t('流程型:常驻「可用技能」清单,模型按需 load。知识型:不占常驻清单,认到所绑数据源时(search_datasource_knowledge)才提示可加载。') }} </div>
              </el-form-item>
              <el-form-item v-if="form.skillType === 'knowledge'" :label="$t('关联数据源')">
                <el-select v-model="dsCodes" multiple filterable clearable :disabled="isBuiltin" :placeholder="$t('绑定数据源:认到这些源时本技能才浮现')" style="width: 100%">
                  <el-option v-for="s in dsOptions" :key="s.code" :label="`${s.name} (${s.code})`" :value="s.code" />
                </el-select>
              </el-form-item>
              <el-form-item :label="$t('引用技能')">
                <el-select v-model="refSkills" multiple filterable clearable :disabled="isBuiltin" :placeholder="$t('可引用其它技能(软引用:load_skill 本技能时会提示可再 load 它们)')" style="width: 100%">
                  <el-option v-for="s in refSkillOptions" :key="s.code" :label="`${s.name} (${s.code})`" :value="s.code" />
                </el-select>
              </el-form-item>
              <el-form-item :label="$t('状态')">
                <el-switch v-model="form.status" active-value="0" inactive-value="1" :disabled="isBuiltin" />
                <span class="se-hint">{{ $t('启用后普通对话默认可用') }}</span>
              </el-form-item>
            </el-form>
          </div>

          <!-- 文件/正文 编辑 -->
          <div v-else class="se-edit">
            <div class="se-edit-bar">
              <el-icon><document /></el-icon>
              <span class="se-edit-path">{{ selectedLabel }}</span>
              <el-tag v-if="selectedKey === '__entry__'" size="small" type="warning">{{ $t('入口') }}</el-tag>
            </div>
            <CodeEditor
              :key="selectedKey"
              v-model="editorValue"
              :language="editorLang"
              :read-only="isBuiltin"
              height="calc(100vh - 200px)"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 隐藏的导入 input -->
    <input ref="dirInput" type="file" webkitdirectory directory multiple style="display: none" @change="onPickDir" />
    <input ref="zipInput" type="file" accept=".zip" style="display: none" @change="onPickZip" />
  </el-dialog>
</template>

<script setup name="SkillEditor">
import { ref, reactive, computed, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { t as $t } from "@/lang";
import { getSkill, addSkill, updateSkill, listSkill } from "@/api/ai/skill";
import { listSource } from "@/api/dataManage/data";
import CodeEditor from "@/components/CodeEditor";

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  skillId: { type: [Number, String], default: null },
});
const emit = defineEmits(["update:modelValue", "saved"]);
const visible = computed({ get: () => props.modelValue, set: (v) => emit("update:modelValue", v) });

const form = reactive({ skillId: null, name: "", code: "", description: "", status: "0", builtIn: "0", skillType: "process" });
const content = ref(""); // SKILL.md 正文
const files = ref([]); // [{name, content}]  name 可含 /
const refSkills = ref([]); // 引用的技能 code
const dsCodes = ref([]); // 知识型绑定的数据源 code
const skillOptions = ref([]); // 全部技能(供引用选择)
const dsOptions = ref([]); // 数据源(供知识型绑定)
const selectedKey = ref("__info__");
const saving = ref(false);
const treeRef = ref(null);
const dirInput = ref(null);
const zipInput = ref(null);

const isBuiltin = computed(() => form.builtIn === "1");
const isUpdate = computed(() => form.skillId != null);
const refSkillOptions = computed(() => skillOptions.value.filter((s) => s.code && s.code !== form.code));

// 文本文件扩展名白名单(导入时用)
const TEXT_EXT = new Set([
  "md", "markdown", "txt", "py", "js", "ts", "json", "sql", "sh", "bash",
  "yaml", "yml", "csv", "html", "htm", "css", "xml", "ini", "toml", "cfg", "conf", "env", "r",
]);
const LANG_MAP = {
  md: "markdown", markdown: "markdown", py: "python", js: "javascript", ts: "typescript",
  json: "json", sql: "sql", sh: "shell", bash: "shell", yaml: "yaml", yml: "yaml",
  html: "html", htm: "html", css: "css", xml: "xml",
};

function extOf(name) {
  const i = (name || "").lastIndexOf(".");
  return i >= 0 ? name.slice(i + 1).toLowerCase() : "";
}

// ---- 文件树构建 ----
const treeData = computed(() => {
  const roots = [
    { id: "__info__", label: $t("基础信息"), kind: "info" },
    { id: "__entry__", label: "SKILL.md", kind: "entry" },
  ];
  // 由 files 的 name(可含 /)构建目录树
  const dirMap = {}; // path -> node
  const fileNodes = [];
  const ensureDir = (path) => {
    if (dirMap[path]) return dirMap[path];
    const parts = path.split("/");
    const label = parts[parts.length - 1];
    const node = { id: "dir:" + path, label, kind: "dir", path, children: [] };
    dirMap[path] = node;
    if (parts.length > 1) {
      const parent = ensureDir(parts.slice(0, -1).join("/"));
      parent.children.push(node);
    } else {
      fileNodes.push(node);
    }
    return node;
  };
  for (const f of files.value) {
    const name = f.name || "";
    const parts = name.split("/");
    const fileNode = { id: "file:" + name, label: parts[parts.length - 1], kind: "file", path: name };
    if (parts.length > 1) {
      ensureDir(parts.slice(0, -1).join("/")).children.push(fileNode);
    } else {
      fileNodes.push(fileNode);
    }
  }
  return [...roots, ...fileNodes];
});

function nodeIcon(data) {
  if (data.kind === "info") return "Setting";
  if (data.kind === "entry") return "Document";
  if (data.kind === "dir") return "Folder";
  return "Document";
}

const selectedLabel = computed(() => {
  if (selectedKey.value === "__entry__") return "SKILL.md";
  if (selectedKey.value.startsWith("file:")) return selectedKey.value.slice(5);
  return "";
});

function onNodeClick(data) {
  if (data.kind === "dir") return; // 目录不进编辑区
  selectedKey.value = data.id;
}

// 当前选中文件对象
const currentFile = computed(() => {
  if (!selectedKey.value.startsWith("file:")) return null;
  const path = selectedKey.value.slice(5);
  return files.value.find((f) => f.name === path) || null;
});

// 右侧编辑器双向绑定:entry→content,file→该文件 content
const editorValue = computed({
  get() {
    if (selectedKey.value === "__entry__") return content.value;
    return currentFile.value ? currentFile.value.content : "";
  },
  set(v) {
    if (selectedKey.value === "__entry__") content.value = v;
    else if (currentFile.value) currentFile.value.content = v;
  },
});
const editorLang = computed(() => {
  if (selectedKey.value === "__entry__") return "markdown";
  const ext = extOf(selectedLabel.value);
  return LANG_MAP[ext] || "plaintext";
});

// ---- 文件增删改 ----
async function addFile(dirPath) {
  try {
    const { value } = await ElMessageBox.prompt(
      dirPath ? `在「${dirPath}/」下新建文件` : "新建文件(可用 / 建子目录,如 references/api.md)",
      "新建文件",
      { inputPlaceholder: "文件名,如 reference.md / scripts/run.py" }
    );
    let name = (value || "").trim().replace(/^\/+|\/+$/g, "");
    if (!name) return;
    if (dirPath) name = dirPath + "/" + name;
    if (name.toLowerCase() === "skill.md") return ElMessage.error("SKILL.md 是入口,请直接编辑左侧「SKILL.md」");
    if (files.value.some((f) => f.name === name)) return ElMessage.error("文件已存在:" + name);
    files.value.push({ name, content: "" });
    selectedKey.value = "file:" + name;
  } catch (e) {
    /* 取消 */
  }
}

async function renameNode(data) {
  const old = data.path;
  try {
    const { value } = await ElMessageBox.prompt("重命名(可含 / 移动目录)", "重命名", { inputValue: old });
    const nn = (value || "").trim().replace(/^\/+|\/+$/g, "");
    if (!nn || nn === old) return;
    if (data.kind === "file") {
      if (nn.toLowerCase() === "skill.md") return ElMessage.error("不能命名为 SKILL.md");
      if (files.value.some((f) => f.name === nn)) return ElMessage.error("文件已存在:" + nn);
      const f = files.value.find((x) => x.name === old);
      if (f) f.name = nn;
      if (selectedKey.value === "file:" + old) selectedKey.value = "file:" + nn;
    } else {
      // 目录:前缀替换所有子文件
      const prefix = old + "/";
      files.value.forEach((f) => {
        if (f.name.startsWith(prefix)) f.name = nn + "/" + f.name.slice(prefix.length);
      });
    }
  } catch (e) {
    /* 取消 */
  }
}

async function deleteNode(data) {
  try {
    await ElMessageBox.confirm(`确认删除「${data.path}」${data.kind === "dir" ? "(含其下全部文件)" : ""}?`, "删除", { type: "warning" });
    if (data.kind === "file") {
      files.value = files.value.filter((f) => f.name !== data.path);
    } else {
      const prefix = data.path + "/";
      files.value = files.value.filter((f) => !f.name.startsWith(prefix));
    }
    if (selectedKey.value === data.id || selectedKey.value.startsWith("file:" + data.path)) selectedKey.value = "__entry__";
  } catch (e) {
    /* 取消 */
  }
}

// ---- 导入 ----
function onImportCmd(cmd) {
  if (cmd === "dir") dirInput.value?.click();
  else if (cmd === "zip") zipInput.value?.click();
}

/** 统一应用导入结果:{content, files:[{name,content}], skipped:[]} */
async function applyImport(parsed) {
  if (parsed.content == null && !parsed.files.length) {
    return ElMessage.warning("未在导入内容里找到 SKILL.md 或可识别的文本文件");
  }
  let mode = "replace";
  try {
    await ElMessageBox.confirm(
      `解析到 ${parsed.content != null ? "SKILL.md + " : ""}${parsed.files.length} 个文件。选择导入方式:`,
      "导入技能内容",
      { confirmButtonText: "替换全部", cancelButtonText: "合并(保留已有)", distinguishCancelAndClose: true, type: "info" }
    );
  } catch (act) {
    if (act === "cancel") mode = "merge";
    else return; // 关闭/ESC
  }
  if (mode === "replace") {
    if (parsed.content != null) content.value = parsed.content;
    files.value = parsed.files.map((f) => ({ ...f }));
  } else {
    if (parsed.content != null && !content.value.trim()) content.value = parsed.content;
    const byName = Object.fromEntries(files.value.map((f) => [f.name, f]));
    for (const f of parsed.files) {
      if (byName[f.name]) byName[f.name].content = f.content;
      else files.value.push({ ...f });
    }
  }
  if (parsed.skipped?.length) ElMessage.warning(`已跳过 ${parsed.skipped.length} 个非文本文件:${parsed.skipped.slice(0, 5).join(", ")}${parsed.skipped.length > 5 ? "…" : ""}`);
  else ElMessage.success("导入完成");
  selectedKey.value = "__entry__";
}

/** 去掉一组相对路径的公共顶层目录(zip/文件夹常带一层根目录) */
function stripTopDir(paths) {
  const tops = new Set(paths.map((p) => p.split("/")[0]));
  if (tops.size === 1 && paths.every((p) => p.includes("/"))) {
    const top = [...tops][0] + "/";
    return (p) => p.slice(top.length);
  }
  return (p) => p;
}

async function onPickDir(e) {
  const list = [...(e.target.files || [])];
  e.target.value = "";
  if (!list.length) return;
  const rels = list.map((f) => f.webkitRelativePath || f.name);
  const strip = stripTopDir(rels);
  const parsed = { content: null, files: [], skipped: [] };
  for (const f of list) {
    const rel = strip(f.webkitRelativePath || f.name);
    if (!rel || rel.endsWith("/")) continue;
    if (rel.toLowerCase() === "skill.md") {
      parsed.content = await f.text();
    } else if (TEXT_EXT.has(extOf(rel))) {
      parsed.files.push({ name: rel, content: await f.text() });
    } else {
      parsed.skipped.push(rel);
    }
  }
  await applyImport(parsed);
}

async function onPickZip(e) {
  const file = (e.target.files || [])[0];
  e.target.value = "";
  if (!file) return;
  let JSZip;
  try {
    JSZip = (await import("jszip")).default;
  } catch (err) {
    return ElMessage.error("未安装 jszip,无法解析 .zip(请联系管理员安装依赖)");
  }
  const zip = await JSZip.loadAsync(file);
  const entries = Object.values(zip.files).filter((f) => !f.dir);
  const strip = stripTopDir(entries.map((f) => f.name));
  const parsed = { content: null, files: [], skipped: [] };
  for (const f of entries) {
    const rel = strip(f.name);
    if (!rel) continue;
    if (rel.toLowerCase() === "skill.md") parsed.content = await f.async("string");
    else if (TEXT_EXT.has(extOf(rel))) parsed.files.push({ name: rel, content: await f.async("string") });
    else parsed.skipped.push(rel);
  }
  await applyImport(parsed);
}

// ---- 导出 ----
async function exportZip() {
  let JSZip;
  try {
    JSZip = (await import("jszip")).default;
  } catch (err) {
    return ElMessage.error("未安装 jszip,无法导出 .zip");
  }
  const zip = new JSZip();
  zip.file("SKILL.md", content.value || "");
  for (const f of files.value) zip.file(f.name, f.content || "");
  const blob = await zip.generateAsync({ type: "blob" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = (form.code || "skill") + ".zip";
  a.click();
  URL.revokeObjectURL(a.href);
}

// ---- 保存 ----
function save() {
  if (!form.name.trim()) return ElMessage.error($t("请填写技能名称"));
  if (!form.code.trim()) return ElMessage.error($t("请填写技能代码"));
  if (!content.value.trim()) return ElMessage.error($t("请填写 SKILL.md 正文"));
  const named = files.value.filter((f) => f.name && f.name.trim()).map((f) => ({ name: f.name.trim(), content: f.content || "" }));
  const names = named.map((f) => f.name);
  if (new Set(names).size !== names.length) return ElMessage.error($t("附加文件名不能重复"));
  saving.value = true;
  const payload = {
    skillId: form.skillId ?? undefined,
    name: form.name,
    code: form.code,
    description: form.description,
    content: content.value,
    resources: named.length ? JSON.stringify(named) : "",
    refSkills: refSkills.value.join(","),
    skillType: form.skillType || "process",
    datasourceCodes: form.skillType === "knowledge" ? dsCodes.value.join(",") : "",
    status: form.status,
    builtIn: form.builtIn,
  };
  const action = form.skillId != null ? updateSkill : addSkill;
  action(payload)
    .then(() => {
      ElMessage.success(form.skillId != null ? $t("修改成功") : $t("新增成功"));
      visible.value = false;
      emit("saved");
    })
    .finally(() => (saving.value = false));
}

// ---- 加载 ----
function parseFiles(resources) {
  if (!resources) return [];
  try {
    const arr = JSON.parse(resources);
    if (!Array.isArray(arr)) return [];
    return arr.filter((f) => f && f.name).map((f) => ({ name: String(f.name), content: String(f.content || "") }));
  } catch (e) {
    return [];
  }
}

async function load() {
  // 技能选项(供引用)+ 数据源(供知识型绑定)
  listSkill({ pageNum: 1, pageSize: 200 }).then((res) => (skillOptions.value = res.rows || []));
  listSource({ pageNum: 1, pageSize: 200 }).then((res) => (dsOptions.value = res.rows || [])).catch(() => {});
  selectedKey.value = "__info__";
  if (props.skillId != null) {
    const res = await getSkill(props.skillId);
    const d = res.data || {};
    Object.assign(form, {
      skillId: d.skillId ?? null,
      name: d.name || "",
      code: d.code || "",
      description: d.description || "",
      status: d.status || "0",
      builtIn: d.builtIn || "0",
      skillType: d.skillType || "process",
    });
    content.value = d.content || "";
    files.value = parseFiles(d.resources);
    refSkills.value = (d.refSkills || "").split(",").map((s) => s.trim()).filter(Boolean);
    dsCodes.value = (d.datasourceCodes || "").split(",").map((s) => s.trim()).filter(Boolean);
    if (d.builtIn !== "1") selectedKey.value = "__entry__";
  } else {
    Object.assign(form, { skillId: null, name: "", code: "", description: "", status: "0", builtIn: "0", skillType: "process" });
    content.value = "";
    files.value = [];
    refSkills.value = [];
    dsCodes.value = [];
  }
}

watch(() => props.modelValue, (v) => { if (v) load(); });
</script>

<style scoped>
.skill-editor { display: flex; flex-direction: column; height: calc(100vh - 40px); }
.se-head { display: flex; align-items: center; gap: 10px; padding-bottom: 10px; border-bottom: 1px solid var(--el-border-color-lighter); }
.se-head-right { margin-left: auto; display: flex; gap: 8px; }
.se-body { flex: 1; display: flex; min-height: 0; margin-top: 10px; gap: 10px; }
.se-left { width: 300px; flex-shrink: 0; border: 1px solid var(--el-border-color-lighter); border-radius: 6px; display: flex; flex-direction: column; overflow: hidden; }
.se-left-head { display: flex; align-items: center; justify-content: space-between; padding: 6px 10px; background: var(--el-fill-color-light); border-bottom: 1px solid var(--el-border-color-lighter); font-size: 13px; color: var(--el-text-color-secondary); }
.se-left :deep(.el-tree) { flex: 1; overflow: auto; padding: 6px; }
.se-node { display: flex; align-items: center; gap: 4px; width: 100%; padding-right: 6px; }
.se-node-icon { font-size: 14px; color: var(--el-text-color-secondary); }
.se-node-label { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.se-node-actions { display: none; gap: 6px; }
.se-node-actions .el-icon { color: var(--el-text-color-secondary); }
.se-node-actions .el-icon:hover { color: var(--el-color-primary); }
.se-node:hover .se-node-actions { display: inline-flex; }
.se-right { flex: 1; min-width: 0; border: 1px solid var(--el-border-color-lighter); border-radius: 6px; overflow: hidden; }
.se-info { padding: 20px; overflow: auto; height: 100%; }
.se-edit { display: flex; flex-direction: column; height: 100%; }
.se-edit-bar { display: flex; align-items: center; gap: 6px; padding: 8px 12px; background: var(--el-fill-color-light); border-bottom: 1px solid var(--el-border-color-lighter); font-size: 13px; }
.se-edit-path { font-family: monospace; }
.se-hint { margin-left: 8px; font-size: 12px; color: var(--el-text-color-secondary); }
</style>
