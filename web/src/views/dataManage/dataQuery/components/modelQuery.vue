<template>
  <div v-if="hasPermission(['llm:data:chat'])" >
    ai取数 <a-switch v-model:checked="ai_query" /> <br />
    <div v-show="ai_query" style="margin: 5px">
      <span>
        <a-textarea v-model:value="query_prompt" :autoSize="{ minRows: 1, maxRows: 8 }" placeholder="请输入取数提示" style="width: 100%" />
      </span>
    </div>
  </div>
  <div v-show="extract_rules.length > 0 && !ai_query" class="extract-panel">
    筛选条件 <br />
    <div v-for="(item, index) in extract_rule_list">
      <a-select
        v-model:value="extract_rule_list[index].field"
        style="width: 180px"
        show-search
        @change="handleFieldChange(index)"
      >
        <a-select-option v-for="(field, index) in fields" :key="index" :value="field">{{ field }}</a-select-option>
      </a-select>
      <a-select
        v-model:value="extract_rule_list[index].rule"
        style="width: 180px"
        show-search
        @change="handleRuleChange(index)"
      >
        <a-select-option v-for="(rule, index) in extract_rules" :key="index" :value="rule.value">{{ rule.name }}</a-select-option>
      </a-select>
      <a-input
        v-model:value="extract_rule_list[index].value"
        style="width: 180px"
        placeholder="请输入值" />
      <Icon icon="ant-design:minus-circle-outlined" @click="delRule(index)" />
      <Icon icon="ant-design:plus-circle-outlined" @click="addRule" v-if="index == extract_rule_list.length - 1" />
    </div>
    <Icon icon="ant-design:plus-circle-outlined" @click="addRule" v-if="extract_rule_list.length === 0" />
  </div>
  <div v-show="search_type_list.length > 0 && !ai_query" class="search-panel">
    高级查询
    <a-select
      v-model:value="search_type"
      label-in-value
      style="width: 200px; float: right"
      :options="search_type_options"
      @change="handleSearchTypeChange"
    ></a-select>
    <MonacoEditor
      v-model:value="search_text"
      language="sql"
    />
  </div>
</template>

<script lang="ts" setup>
  import { watch, onMounted, ref, unref, reactive } from 'vue';
  import type { SelectProps } from 'ant-design-vue';
  import { MonacoEditor } from '/@/components/Form';
  import { usePermission } from '@/hooks/web/usePermission';
  const { hasPermission } = usePermission();
  // Emits声明
  const emit = defineEmits(['genQuery']);
  const props = defineProps({
    data: { type: Object, default: () => ({}) },
  });
  const extract_rules = ref([]); // 可用筛选配置
  const fields = ref([]); // 字段列表
  const search_type_list = ref([]); // 可用高级查询配置
  let search_type_map = reactive({}); // 高级查询默认语句map
  const search_type_options = ref<SelectProps['options']>([]); // 高级查询下拉配置
  // 查询配置
  const extract_rule_list = ref([]); // 筛选条件
  const search_type = ref(''); // 高级查询类型
  const search_text = ref(''); // 高级查询语句
  const ai_query = ref(false); // ai取数
  const query_prompt = ref(''); // ai取数prompt
  // 添加筛选规则
  function addRule() {
    extract_rule_list.value.push({
      field: '',
      rule: '',
      value: '',
    });
  }
  // 删除筛选规则
  function delRule(index) {
    extract_rule_list.value.splice(index, 1);
  }
  // 筛选规则字段变化
  function handleFieldChange(index) {
    console.log(index, extract_rule_list);
  }
  // 筛选规则变化
  function handleRuleChange(index) {
    console.log(index, extract_rule_list);
  }
  // 设置查询配置
  function setData(data) {
    console.log(8, data);
    extract_rules.value = data.extract_rules || [];
    search_type_list.value = data.search_type_list || [];
    fields.value = data.fields || [];

    // 重置所有查询表单状态
    extract_rule_list.value = [];
    search_type_map = {};
    search_type_options.value = [];
    search_type.value = '';
    search_text.value = '';
    ai_query.value = false;
    query_prompt.value = '';

    for (let i = 0; i < unref(search_type_list).length; i++) {
      // 高级查询默认设为第一个
      if (i == 0) {
        search_type.value = unref(search_type_list)[i]['value'];
        search_text.value = unref(search_type_list)[i]['default'];
      }
      search_type_map[unref(search_type_list)[i]['value']] = unref(search_type_list)[i]['default'];
      console.log(search_type_map, unref(search_type_list)[i]['value'], unref(search_type_list)[i]['default']);
      search_type_options.value.push({
        value: unref(search_type_list)[i]['value'],
        label: unref(search_type_list)[i]['name'],
      });
    }
  }
  // 高级查询类型更新事件
  function handleSearchTypeChange() {
    search_text.value = unref(search_type_map)[unref(search_type).value] || '';
  }
  function genQuery() {
    console.log(unref(extract_rule_list));
    console.log(search_text.value, search_type.value);
    return {
      extract_rules: extract_rule_list.value,
      search_type: search_type.value,
      search_text: search_text.value,
      ai_query: ai_query.value,
      query_prompt: query_prompt.value,
    };
  }
  onMounted(() => {
    watch(
      () => props.data,
      () => setData(props.data),
      { deep: true, immediate: true }
    );
  });
  defineExpose({
    genQuery,
  });
</script>
