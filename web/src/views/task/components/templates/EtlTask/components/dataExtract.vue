<template>
  <a-row>
    <a-col :span="12" style="padding-left: 5px; padding-right: 5px; border-right: 1px dashed rgb(217, 217, 217);">
      <div style="font-weight: 700;">数据抽取</div>
      数据模型 <br />
      <a-select
          v-model:value="model_id"
          style="width: 300px"
          show-search
          @change="handleModelChange"
      >
        <a-select-option v-for="(item, index) in dataModelList" :key="index" :value="item.id">{{ item.name }}</a-select-option>
      </a-select>
      <br />
      抽取方式 <br />
      <a-select
          v-model:value="extract_type"
          style="width: 300px"
          show-search
          @change="handleExtractTypeChange"
      >
        <a-select-option v-for="(item, index) in extract_type_options" :key="index" :value="item.value">{{ item.name }}</a-select-option>
      </a-select>
      <br />
      单批数据量 <br />
      <a-input-number v-model:value="batch_size" style="width: 300px" /> <br />
      <div v-show="extract_rules.length > 0" class="extract-panel">
        筛选条件 <br />
        <div v-for="(item, index) in extract_rule_list">
          <a-select
              v-model:value="extract_rule_list[index].field"
              style="width: 180px"
              show-search
              @change="handleFieldChange(index)"
          >
            <a-select-option v-for="(field, index) in fields" :key="index" :value="field.key">{{ field.title }}</a-select-option>
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
      <div v-show="search_type_list.length > 0" class="search-panel">
        高级查询
        <a-select
          v-model:value="search_type"
          label-in-value
          style="width: 200px; float: right"
          :options="search_type_options"
          @change="handleSearchTypeChange"
        ></a-select>
        <monaco-editor
          v-model:value="search_text"
          language="sql"
        />
      </div>
    </a-col>
    <a-col :span="12" style="padding-left: 5px; padding-right: 5px;">
      <JVxeTable
        ref="tableRef"
        toolbar
        resizable
        maxHeight="400"
        :toolbarConfig="{ btn: [] }"
        :loading="loading"
        :columns="fields"
        :dataSource="dataSource"
      >
        <template #toolbarSuffix>
          <a-button @click="fetchData(false)" style="float: right">预览</a-button>
        </template>
      </JVxeTable>
    </a-col>
  </a-row>
</template>

<script lang="ts" setup>
  import { onMounted, ref, unref, reactive } from 'vue';
  import type { SelectProps } from 'ant-design-vue';
  import { allList } from '/@/views/dataManage/dataModel/datamodel.api';
  import { previewEtlData } from '/@/views/dataManage/dataQuery/dataquery.api';
  import { JVxeTypes } from '/@/components/jeecg/JVxeTable/src/types';
  import { MonacoEditor } from '/@/components/Form';
  import { parseTableRecords } from '/@/utils/common_utils';
  const loading = ref(false); // loading
  const dataModelList = ref([]); // 数据模型列表
  const model_id = ref(''); // 数据模型id
  const batch_size = ref(1000); // 单批处理量
  const dataSource = ref<any[]>([]); // 数据列表
  const extract_rules = ref([]); // 可用筛选配置
  const extract_type = ref('once'); // 抽取方式
  const fields = ref([]); // 字段列表
  const search_type_list = ref([]); // 可用高级查询配置
  let search_type_map = reactive({}); // 高级查询默认语句map
  const search_type_options = ref<SelectProps['options']>([]); // 高级查询下拉配置
  const extract_type_options = ref<SelectProps['options']>([
    {
      name: '单次抽取',
      value: 'once',
    },
    {
      name: '分批抽取',
      value: 'batch',
    },
    {
      name: '流式抽取',
      value: 'flow',
    },
  ]); // 抽取方式下拉配置
  // 查询配置
  const extract_rule_list = ref([]); // 筛选条件
  const search_type = ref(''); // 高级查询类型
  const search_text = ref(''); // 高级查询语句
  // 监听模型发生变化
  async function handleModelChange(id) {
    model_id.value = id;
    await fetchData(true);
    console.log(model_id.value);
  }
  // 监听抽取方式变化
  async function handleExtractTypeChange(t) {
    extract_type.value = t;
    console.log(extract_type.value);
  }
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
  // 查询模型数据
  async function fetchData(is_init = false) {
    // queryRef
    loading.value = true;
    try {
      const res_data = await previewEtlData({
        task_params: {
          extract: genExtract(),
          process_rules: [],
        },
        run_load: false,
      });
      if (res_data) {
        dataSource.value = parseTableRecords(res_data.data.records);
        if (is_init) {
          // 重置字段列表, 筛选规则列表, 高级查询列表
          const modelInfo = {
            model_id: model_id.value,
            extract_rules: res_data.extract_rules || [],
            search_type_list: res_data.search_type_list || [],
            fields: res_data.fields || [],
          };
          // 初始化查询配置
          setData(modelInfo, [], '', '');
        }
      }
    } catch (e) {
      console.log(e);
    } finally {
      loading.value = false;
    }
  }
  // 设置查询配置
  function setData(modelInfo, _extract_rule_list = [], _search_type = '', _search_text = '') {
    model_id.value = modelInfo.model_id;
    extract_rules.value = modelInfo.extract_rules || [];
    search_type_list.value = modelInfo.search_type_list || [];
    search_type_map = {};
    search_type_options.value = [];
    // 设置字段
    let _fields = modelInfo.fields;
    fields.value = [];
    for (let i in _fields) {
      let field = _fields[i];
      fields.value.push({
        title: field,
        key: field,
        type: JVxeTypes.normal,
        width: 150,
      });
    }
    // 初始化高级筛选项
    for (let i = 0; i < unref(search_type_list).length; i++) {
      // 高级查询默认设为第一个
      if (i == 0) {
        if (_search_type != '' && _search_text != '') {
          // 设置高级筛选项
          search_type.value = _search_type;
          search_text.value = _search_text;
        } else {
          search_type.value = unref(search_type_list)[i]['value'];
          search_text.value = unref(search_type_list)[i]['default'];
        }
      }
      search_type_map[unref(search_type_list)[i]['value']] = unref(search_type_list)[i]['default'];
      console.log(search_type_map, unref(search_type_list)[i]['value'], unref(search_type_list)[i]['default']);
      search_type_options.value.push({
        value: unref(search_type_list)[i]['value'],
        label: unref(search_type_list)[i]['name'],
      });
    }
    // 初始化抽取配置
    if (_extract_rule_list.length != 0) {
      extract_rule_list.value = _extract_rule_list;
    } else {
      extract_rule_list.value = [];
    }
  }
  // 高级查询类型更新事件
  function handleSearchTypeChange() {
    search_text.value = unref(search_type_map)[unref(search_type).value] || '';
  }
  // 生成数据抽取配置
  function genExtract() {
    return {
      model_id: model_id.value,
      extract_type: extract_type.value,
      extract_rules: extract_rule_list.value,
      search_type: search_type.value,
      search_text: search_text.value,
      batch_size: batch_size.value,
    };
  }
  // 初始化数据抽取配置
  async function initData(taskParams) {
    console.log('init Extract', taskParams);
    const extract_info = taskParams.extract;
    if (!extract_info) {
      model_id.value = '';
      extract_type.value = 'once';
      extract_rules.value = [];
      search_type_list.value = [];
      search_type_map = {};
      search_type_options.value = [];
      fields.value = [];
      batch_size.value = 1000;
      return;
    }
    model_id.value = extract_info.model_id;
    batch_size.value = extract_info.batch_size;
    extract_type.value = extract_info.extract_type || 'once';
    console.log('init extract', extract_info);
    loading.value = true;
    try {
      const res_data = await previewEtlData({
        task_params: {
          extract: genExtract(),
          process_rules: [],
        },
        run_load: false,
      });
      if (res_data) {
        dataSource.value = parseTableRecords(res_data.data.records);
        // 重置字段列表, 筛选规则列表, 高级查询列表
        const modelInfo = {
          model_id: model_id.value,
          extract_rules: res_data.extract_rules || [],
          search_type_list: res_data.search_type_list || [],
          fields: res_data.fields || [],
        };
        // 初始化查询配置
        setData(modelInfo, extract_info.extract_rules, extract_info.search_type, extract_info.search_text);
      } else {
        console.log('error', res_data);
      }
    } catch (e) {
      console.log(e);
    } finally {
      loading.value = false;
    }
  }
  onMounted(async () => {
    // 加载数据模型列表
    dataModelList.value = await allList({ auth_type: 'extract' });
    console.log(dataModelList.value);
  });
  defineExpose({
    genExtract,
    initData,
  });
</script>
