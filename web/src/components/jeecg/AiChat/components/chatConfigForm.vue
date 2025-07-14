<template>
  <div class="center-container">
    <!-- 知识库配置 -->
    <a-card class="mb-3" :title="knowledgeTitle">
      <template #extra>
        <a-switch v-model:checked="formState.rag.enable" />
      </template>
      <a-form v-if="formState.rag.enable" :model="formState.rag" :label-col="{ span: 7 }" :wrapper-col="{ span: 14 }" layout="horizontal">
        <a-form-item label="数据集">
          <ApiSelect v-model:value="formState.rag.dataset_id" :api="allDataSetList" mode="multiple" :params="{}" labelField="name" valueField="id" />
        </a-form-item>
        <a-form-item label="召回数量">
          <a-input-number v-model:value="formState.rag.k" :min="1" />
        </a-form-item>
        <a-form-item label="检索模式">
          <JSelectInput v-model:value="formState.rag.retrieval_type" :options="retrievalTypeOptions" />
        </a-form-item>
        <a-form-item label="分数过滤">
          <a-input-number v-model:value="formState.rag.score_threshold" :min="0" :precision="2" :step="0.1" />
        </a-form-item>
        <a-form-item label="结果重排">
          <JSwitch v-model:value="formState.rag.rerank" :options="['1', '0']" />
        </a-form-item>
        <a-form-item label="结果重排分数过滤" v-if="formState.rag.rerank == '1'">
          <a-input-number v-model:value="formState.rag.rerank_score_threshold" :min="0" :precision="2" :step="0.1" />
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 工具调用配置 -->
    <a-card class="mb-3" :title="toolTitle">
      <template #extra>
        <a-switch v-model:checked="formState.agent.enable" />
      </template>
      <a-form v-if="formState.agent.enable" :model="formState.agent" :label-col="{ span: 7 }" :wrapper-col="{ span: 14 }" layout="horizontal">
        <a-form-item label="使用工具">
          <ApiSelect v-model:value="formState.agent.tools" :api="toolList" mode="multiple" :params="{}" labelField="name" valueField="value" />
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 数据分析配置 -->
    <a-card class="mb-3" :title="dataTitle">
      <template #extra>
        <a-switch v-model:checked="formState.data_chat.enable" />
      </template>
      <a-form v-if="formState.data_chat.enable" :model="formState.data_chat" :label-col="{ span: 7 }" :wrapper-col="{ span: 14 }" layout="horizontal">
        <a-form-item label="数据模型列表">
          <ApiSelect v-model:value="formState.data_chat.datamodel_id" :api="allDataModelList" mode="multiple" :params="{}" labelField="name" valueField="id" />
        </a-form-item>
      </a-form>
    </a-card>

    <!-- 长期记忆配置 -->
    <a-card class="mb-3" :title="memoryTitle">
      <template #extra>
        <a-switch v-model:checked="formState.memory.enable" />
      </template>
      <a-form v-if="formState.memory.enable" :model="formState.memory" :label-col="{ span: 7 }" :wrapper-col="{ span: 14 }" layout="horizontal">
        <a-form-item label="记忆窗口">
          <a-input-number v-model:value="formState.memory.history_size" :min="1" />
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
  import { ref, watch } from 'vue';
  import ApiSelect from '@/components/Form/src/components/ApiSelect.vue';
  import JSelectInput from '@/components/Form/src/jeecg/components/JSelectInput.vue';
  import JSwitch from '@/components/Form/src/jeecg/components/JSwitch.vue';
  import { allList as allDataSetList } from '@/views/rag/dataset/dataset.api';
  import { toolList } from '@/components/jeecg/AiChat/llm.api';
  import { allList as allDataModelList } from '@/views/dataManage/dataModel/datamodel.api';
  import { defaultChatConfig } from '@/components/jeecg/AiChat/data';

  const props = defineProps<{
    modelValue: {
      rag: {
        enable: boolean;
        dataset_id: string[];
        k: number;
        retrieval_type: string;
        score_threshold: number;
        rerank: string;
        rerank_score_threshold: number;
      };
      agent: {
        enable: boolean;
        tools: string[];
      };
      data_chat: {
        enable: boolean;
        datamodel_id: string[];
      };
      memory: {
        enable: false;
        history_size: number;
      };
    };
  }>();

  const emit = defineEmits(['update:modelValue']);

  const formState = ref({
    rag: {
      ...defaultChatConfig.rag,
      ...props.modelValue.rag,
    },
    agent: {
      ...defaultChatConfig.agent,
      ...props.modelValue.agent,
    },
    data_chat: {
      ...defaultChatConfig.data_chat,
      ...props.modelValue.data_chat,
    },
    memory: {
      ...defaultChatConfig.memory,
      ...props.modelValue.memory,
    },
  });

  const retrievalTypeOptions = [
    { label: '语义', value: 'vector' },
    { label: '全文', value: 'keyword' },
    { label: '混合', value: 'all' },
  ];

  const knowledgeTitle = '启用知识库';
  const toolTitle = '工具调用';
  const dataTitle = '数据分析';
  const memoryTitle = '长期记忆';

  watch(
    formState,
    (newVal) => {
      emit('update:modelValue', newVal);
    },
    { deep: true }
  );
</script>

<style scoped>
.mb-3 { margin-bottom: 16px; }
.center-container {
  /* max-width: 600px; */
  margin: 0 auto;
}
</style>
