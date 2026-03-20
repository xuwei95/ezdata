<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose :title="title" :width="680" @ok="handleSubmit">
    <template #footer>
      <a-space>
        <a-button @click="closeModal">取消</a-button>
        <a-button v-if="showFooter" type="primary" @click="handleSubmit" :loading="loading">确定</a-button>
      </a-space>
    </template>
    <a-spin :spinning="loading">
      <a-form ref="formRef" :model="formState" :label-col="{ span: 5 }" :wrapper-col="{ span: 17 }">
        <a-form-item label="提供商" name="provider" :rules="[{ required: true, message: '请选择提供商' }]">
          <a-select v-model:value="formState.provider" placeholder="请选择提供商" :disabled="!showFooter">
            <a-select-option v-for="p in providerOptions" :key="p.code" :value="p.code">
              {{ p.name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="模型名称" name="name" :rules="[{ required: true, message: '请输入模型名称' }]">
          <a-input v-model:value="formState.name" placeholder="如 GPT-4o" :disabled="!showFooter" />
        </a-form-item>

        <a-form-item label="模型代码" name="model_code" :rules="[{ required: true, message: '请输入模型代码' }]">
          <a-input v-model:value="formState.model_code" placeholder="实际调用代码，如 gpt-4o" :disabled="!showFooter" />
        </a-form-item>

        <a-form-item label="模型类型" name="model_type" :rules="[{ required: true, message: '请选择模型类型' }]">
          <a-select v-model:value="formState.model_type" placeholder="请选择模型类型" :disabled="!showFooter">
            <a-select-option value="chat">对话(chat)</a-select-option>
            <a-select-option value="embedding">向量(embedding)</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="API Key" name="api_key">
          <a-input-password
            v-model:value="formState.api_key"
            placeholder="请输入 API Key"
            :disabled="!showFooter"
            autocomplete="off"
          />
        </a-form-item>

        <a-form-item label="Base URL" name="base_url">
          <a-input
            v-model:value="formState.base_url"
            placeholder="如 https://api.openai.com/v1"
            :disabled="!showFooter"
          />
        </a-form-item>

        <a-form-item label="状态" name="status">
          <a-radio-group v-model:value="formState.status" :disabled="!showFooter">
            <a-radio :value="1">启用</a-radio>
            <a-radio :value="0">禁用</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-spin>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, reactive, computed, unref, onMounted } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { saveOrUpdateModel, providerList } from '../models.api';
  import { useMessage } from '/@/hooks/web/useMessage';

  const emit = defineEmits(['register', 'success']);
  const formRef = ref();
  const loading = ref(false);
  const isUpdate = ref(false);
  const showFooter = ref(true);
  const providerOptions = ref<any[]>([]);

  onMounted(async () => {
    try {
      const data = await providerList();
      providerOptions.value = Array.isArray(data) ? data : [];
    } catch (e) {}
  });

  const { createMessage } = useMessage();

  const formState = reactive({
    id: '',
    provider: '',
    name: '',
    model_code: '',
    model_type: 'chat',
    api_key: '',
    base_url: '',
    status: 1,
  });

  const title = computed(() => (!unref(isUpdate) ? '新增模型' : '编辑模型'));

  const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
    setModalProps({ confirmLoading: false });
    isUpdate.value = data.isUpdate;
    showFooter.value = data.showFooter !== false;

    if (data.record) {
      Object.assign(formState, {
        id: '', provider: '', name: '', model_code: '', model_type: 'chat',
        api_key: '', base_url: '', status: 1,
        ...data.record,
      });
    } else {
      Object.assign(formState, {
        id: '', provider: data.provider || '', name: '', model_code: '',
        model_type: 'chat', api_key: '', base_url: '', status: 1,
      });
    }
  });

  async function handleSubmit() {
    try {
      await formRef.value?.validate();
      setModalProps({ confirmLoading: true });
      loading.value = true;
      await saveOrUpdateModel({ ...formState }, unref(isUpdate));
      closeModal();
      emit('success');
    } catch (error: any) {
      if (error?.errorFields) return;
      createMessage.error(error?.message || '保存失败');
    } finally {
      loading.value = false;
      setModalProps({ confirmLoading: false });
    }
  }
</script>
