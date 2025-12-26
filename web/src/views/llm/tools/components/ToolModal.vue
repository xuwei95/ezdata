<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose :title="title" :width="900" @ok="handleSubmit">
    <template #footer>
      <a-space>
        <a-button v-if="showFooter && formState.type === 'mcp'" @click="handleTest" :loading="testing">
          <template #icon><Icon icon="ant-design:thunderbolt-outlined" /></template>
          测试连接
        </a-button>
        <a-button @click="closeModal">取消</a-button>
        <a-button v-if="showFooter" type="primary" @click="handleSubmit" :loading="loading">确定</a-button>
      </a-space>
    </template>
    <a-spin :spinning="loading">
      <a-form ref="formRef" :model="formState" :label-col="{ span: 5 }" :wrapper-col="{ span: 18 }">
        <a-form-item label="工具名称" name="name" :rules="[{ required: true, message: '请输入工具名称' }]">
          <a-input v-model:value="formState.name" placeholder="请输入工具名称" :disabled="!showFooter" />
        </a-form-item>

        <a-form-item label="工具代码" name="code" :rules="[{ required: true, message: '请输入工具代码' }]">
          <a-input v-model:value="formState.code" placeholder="请输入工具代码，英文唯一标识" :disabled="isUpdate || !showFooter" />
        </a-form-item>

        <a-form-item label="工具类型" name="type" :rules="[{ required: true, message: '请选择工具类型' }]">
          <a-select v-model:value="formState.type" placeholder="请选择工具类型" :disabled="isUpdate || !showFooter" @change="handleTypeChange">
            <a-select-option value="mcp">MCP工具</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="工具描述" name="description">
          <a-textarea v-model:value="formState.description" :rows="2" placeholder="请输入工具描述" :disabled="!showFooter" />
        </a-form-item>
        <a-form-item label="状态" name="status">
          <a-radio-group v-model:value="formState.status" :disabled="!showFooter">
            <a-radio :value="1">启用</a-radio>
            <a-radio :value="0">禁用</a-radio>
          </a-radio-group>
        </a-form-item>
        <!-- MCP工具配置 -->
        <template v-if="formState.type === 'mcp'">
          <a-divider>MCP工具配置</a-divider>

          <a-form-item label="服务器类型" name="args.server_type">
            <a-select v-model:value="formState.args.server_type" placeholder="请选择服务器类型" :disabled="!showFooter">
              <a-select-option value="stdio">STDIO</a-select-option>
              <a-select-option value="sse">SSE</a-select-option>
            </a-select>
          </a-form-item>

          <template v-if="formState.args.server_type === 'stdio'">
            <a-form-item label="执行命令" name="args.command">
              <a-input v-model:value="formState.args.command" placeholder="如: npx, python, /path/to/tool" :disabled="!showFooter" />
            </a-form-item>

            <a-form-item label="命令参数" name="args.args">
              <MonacoEditor
                v-model:value="argsJsonString"
                language="json"
                :height="150"
                :options="{ readOnly: !showFooter }"
                @change="handleArgsChange"
              />
            </a-form-item>

            <a-form-item label="环境变量" name="args.env">
              <MonacoEditor
                v-model:value="envJsonString"
                language="json"
                :height="150"
                :options="{ readOnly: !showFooter }"
                @change="handleEnvChange"
              />
            </a-form-item>
          </template>

          <template v-if="formState.args.server_type === 'sse'">
            <a-form-item label="服务器URL" name="args.url">
              <a-input v-model:value="formState.args.url" placeholder="请输入SSE服务器URL" :disabled="!showFooter" />
            </a-form-item>

            <a-form-item label="请求头" name="args.headers">
              <MonacoEditor
                v-model:value="headersJsonString"
                language="json"
                :height="150"
                :options="{ readOnly: !showFooter }"
                @change="handleHeadersChange"
              />
            </a-form-item>
          </template>
        </template>
      </a-form>
    </a-spin>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, reactive, computed, unref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { getInfoById, saveOrUpdate, testTool } from '../tools.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { MonacoEditor } from '/@/components/Form';
  import { Icon } from '/@/components/Icon';

  const emit = defineEmits(['register', 'success']);
  const formRef = ref();
  const loading = ref(false);
  const testing = ref(false);
  const isUpdate = ref(true);
  const showFooter = ref(true);

  const { createMessage } = useMessage();

  const formState = reactive({
    id: '',
    name: '',
    code: '',
    type: 'mcp',
    description: '',
    args: {
      server_type: 'stdio',
      command: '',
      args: [],
      env: {},
      url: '',
      headers: {},
    },
    status: 1,
  });

  // JSON字符串的computed属性用于双向绑定
  const argsJsonString = ref(JSON.stringify([], null, 2));
  const envJsonString = ref(JSON.stringify({}, null, 2));
  const headersJsonString = ref(JSON.stringify({}, null, 2));

  // 更新JSON值的方法
  const updateJsonValues = () => {
    argsJsonString.value = JSON.stringify(formState.args.args || [], null, 2);
    envJsonString.value = JSON.stringify(formState.args.env || {}, null, 2);
    headersJsonString.value = JSON.stringify(formState.args.headers || {}, null, 2);
  };

  // 从MonacoEditor更新值的方法
  const handleArgsChange = (val) => {
    try {
      formState.args.args = JSON.parse(val);
    } catch (e) {}
  };

  const handleEnvChange = (val) => {
    try {
      formState.args.env = JSON.parse(val);
    } catch (e) {}
  };

  const handleHeadersChange = (val) => {
    try {
      formState.args.headers = JSON.parse(val);
    } catch (e) {}
  };

  const title = computed(() => (!unref(isUpdate) ? '新增工具' : '编辑工具'));

  //弹窗回调
  const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
    setModalProps({ confirmLoading: false });
    isUpdate.value = data.isUpdate;
    showFooter.value = data.showFooter;

    if (data.record) {
      loading.value = true;
      try {
        const res = await getInfoById({ id: data.record.id });
        Object.assign(formState, res);
        if (typeof formState.args === 'string') {
          formState.args = JSON.parse(formState.args);
        }
        updateJsonValues();
      } catch (error) {
        createMessage.error('获取工具详情失败');
      } finally {
        loading.value = false;
      }
    } else {
      resetForm();
    }
  });

  function resetForm() {
    Object.assign(formState, {
      id: '',
      name: '',
      code: '',
      type: 'mcp',
      description: '',
      args: {
        server_type: 'stdio',
        command: '',
        args: [],
        env: {},
        url: '',
        headers: {},
      },
      status: 1,
    });
    updateJsonValues();
  }

  // 类型变化时重置args
  function handleTypeChange(value) {
    formState.args = {
      server_type: 'stdio',
      command: '',
      args: [],
      env: {},
      url: '',
      headers: {},
    };
    updateJsonValues();
  }

  // 测试连接
  async function handleTest() {
    try {
      // 验证必填字段
      await formRef.value?.validate();

      testing.value = true;

      // 传递表单配置而不是 id
      const testParams = {
        type: formState.type,
        code: formState.code,
        args: formState.args,
      };

      const result = await testTool(testParams);

      if (result.tools && result.tools.length > 0) {
        const toolNames = result.tools.map((t) => t.name).join(', ');
        createMessage.success(`测试成功！获取到 ${result.tools_count} 个工具: ${toolNames}`);
      } else {
        createMessage.success(result.msg || '测试成功');
      }
    } catch (error) {
      createMessage.error(error.message || '测试失败');
    } finally {
      testing.value = false;
    }
  }

  //提交
  async function handleSubmit() {
    try {
      setModalProps({ confirmLoading: true });

      const params = {
        ...formState,
        args: formState.args,
      };

      await saveOrUpdate(params, unref(isUpdate));
      closeModal();
      emit('success');
    } catch (error) {
      createMessage.error('保存失败');
    } finally {
      setModalProps({ confirmLoading: false });
    }
  }
</script>

<style scoped>
  :deep(.ant-divider) {
    margin: 16px 0;
    font-weight: bold;
  }
  :deep(.monaco-editor-container) {
    border: 1px solid #d9d9d9;
    border-radius: 4px;
  }
</style>
