<template>
  <BasicModal
    v-bind="$attrs"
    @register="registerModal"
    destroyOnClose
    title="从 API 获取模型列表"
    :width="700"
    :footer="null"
  >
    <div v-if="!fetched">
      <a-empty description="点击下方按钮从提供商 API 拉取可用模型" :image="Empty.PRESENTED_IMAGE_SIMPLE" style="margin: 24px 0" />
      <div style="text-align: center">
        <a-button type="primary" :loading="fetching" @click="handleFetch">
          <template #icon><Icon icon="ant-design:cloud-download-outlined" /></template>
          获取模型列表
        </a-button>
      </div>
    </div>

    <template v-else>
      <div style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center">
        <span>共获取到 <b>{{ allModels.length }}</b> 个模型，已选 <b>{{ selectedKeys.length }}</b> 个</span>
        <a-space>
          <a-select v-model:value="filterType" style="width: 130px" size="small" @change="onFilterChange">
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="chat">对话(chat)</a-select-option>
            <a-select-option value="embedding">向量(embedding)</a-select-option>
          </a-select>
          <a-button size="small" @click="handleFetch" :loading="fetching">重新获取</a-button>
        </a-space>
      </div>

      <a-table
        :data-source="displayModels"
        :columns="columns"
        :row-selection="rowSelection"
        :pagination="{ pageSize: 10, showSizeChanger: false }"
        size="small"
        row-key="model_code"
        :scroll="{ y: 360 }"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.dataIndex === 'model_type'">
            <a-select
              v-model:value="record.model_type"
              size="small"
              style="width: 110px"
              @change="(val) => onTypeChange(record, val)"
            >
              <a-select-option value="chat">对话(chat)</a-select-option>
              <a-select-option value="embedding">向量(embedding)</a-select-option>
            </a-select>
          </template>
          <template v-else-if="column.dataIndex === 'exists'">
            <a-tag v-if="record.exists" color="orange">已存在</a-tag>
          </template>
        </template>
      </a-table>

      <div style="margin-top: 12px; text-align: right">
        <a-space>
          <a-button @click="closeModal">取消</a-button>
          <a-button
            type="primary"
            :loading="syncing"
            :disabled="selectedKeys.length === 0"
            @click="handleSync"
          >
            同步选中模型（{{ selectedKeys.length }}）
          </a-button>
        </a-space>
      </div>
    </template>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, computed, reactive } from 'vue';
  import { Empty } from 'ant-design-vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { Icon } from '/@/components/Icon';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { providerFetchModels, providerSyncModels } from '../models.api';

  const emit = defineEmits(['register', 'success']);
  const { createMessage } = useMessage();

  const fetching = ref(false);
  const syncing = ref(false);
  const fetched = ref(false);
  const filterType = ref('');

  const providerCode = ref('');
  const existingCodes = ref<Set<string>>(new Set());

  // 全量模型（带 model_type 字段，可编辑）
  const allModels = ref<any[]>([]);
  const selectedKeys = ref<string[]>([]);

  const displayModels = computed(() => {
    if (!filterType.value) return allModels.value;
    return allModels.value.filter((m) => m.model_type === filterType.value);
  });

  const columns = [
    { title: '模型代码', dataIndex: 'model_code', ellipsis: true },
    { title: '类型', dataIndex: 'model_type', width: 130 },
    { title: '', dataIndex: 'exists', width: 70 },
  ];

  const rowSelection = computed(() => ({
    selectedRowKeys: selectedKeys.value,
    onChange: (keys: string[]) => { selectedKeys.value = keys; },
    getCheckboxProps: (record: any) => ({ disabled: record.exists }),
  }));

  const [registerModal, { closeModal }] = useModalInner(async (data) => {
    providerCode.value = data.provider || '';
    existingCodes.value = new Set(data.existingCodes || []);
    // 重置状态
    fetched.value = false;
    allModels.value = [];
    selectedKeys.value = [];
    filterType.value = '';
  });

  async function handleFetch() {
    try {
      fetching.value = true;
      const data: any[] = await providerFetchModels({ provider: providerCode.value });
      allModels.value = (data || []).map((m) => ({
        ...m,
        model_type: guessType(m.model_code),
        exists: existingCodes.value.has(m.model_code),
      }));
      // 默认选中全部未存在的
      selectedKeys.value = allModels.value.filter((m) => !m.exists).map((m) => m.model_code);
      fetched.value = true;
    } catch (e: any) {
      createMessage.error(e?.message || '获取模型列表失败');
    } finally {
      fetching.value = false;
    }
  }

  function guessType(code: string) {
    const lower = (code || '').toLowerCase();
    if (lower.includes('embed') || lower.includes('text-embedding')) return 'embedding';
    return 'chat';
  }

  function onTypeChange(record: any, val: string) {
    record.model_type = val;
  }

  function onFilterChange() {
    // 切换过滤时保持已选项不变
  }

  async function handleSync() {
    try {
      syncing.value = true;
      const selected = allModels.value.filter((m) => selectedKeys.value.includes(m.model_code));
      await providerSyncModels({ provider: providerCode.value, models: selected });
      createMessage.success(`同步成功，已新增 ${selected.length} 个模型`);
      closeModal();
      emit('success');
    } catch (e: any) {
      createMessage.error(e?.message || '同步失败');
    } finally {
      syncing.value = false;
    }
  }
</script>
