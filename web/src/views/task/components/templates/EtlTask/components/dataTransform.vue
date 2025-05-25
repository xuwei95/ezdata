<template>
  <div style="font-weight: 700">数据转换</div>
  <a-row>
    <a-col :span="6" style="padding-left: 5px; padding-right: 5px">
      <a-card title="算法列表">
        <draggable
          v-model="alg_list"
          :group="{ name: 'alg', pull: 'clone', put: false }"
          :clone="cloneAlg"
          @change="handelDragAlg"
          class="alg-list-panel"
        >
          <template #item="{ element }">
            <div class="alg-box">
              {{ element.name }}
            </div>
          </template>
        </draggable>
      </a-card>
    </a-col>
    <a-col :span="6" style="padding-left: 5px; padding-right: 5px;">
      <a-card title="处理流程">
        <draggable
          v-model="process_rules"
          group="alg"
          @change="handelDrag"
          @start="drag = true"
          @end="drag = false"
          class="alg-list-panel"
        >
          <template #item="{ element, index }">
            <div class="flow-box">
              <div>
                <span @click="setParams(element, index)" style="width: 90%; text-align: center; float: left">
                  {{ index + 1 }}.  {{ element.name }}
                </span>
                <Icon icon="ant-design:close-outlined" @click="delRule(index)" style="width: 10%; float: right; text-align: center;margin-top: 6px" />
              </div>
            </div>
          </template>
        </draggable>
      </a-card>
    </a-col>
    <a-col :span="12" style="padding-left: 5px; padding-right: 5px;">
      <a-card title="算法配置" class="alg-setting-panel">
        <div v-show="editIndex !== null">
          <div>流程序号：{{ editIndex + 1 }}</div>
          <div>算法名称：{{ alg_params.name }}</div>
          <div>算法编码：{{ alg_params.code }}</div>
          <BasicForm
            ref="formElRef"
            :showActionButtonGroup="false"
            :labelWidth="120"
            :schemas="schemas"
            :actionColOptions="{ span: 24 }"
          />
          <a-button @click="previewData(editIndex)">预览</a-button>
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
          </JVxeTable>
        </div>
      </a-card>
    </a-col>
  </a-row>
</template>

<script lang="ts" setup>
  import { onMounted, ref } from 'vue';
  import { previewEtlData } from '/@/views/dataManage/dataQuery/dataquery.api';
  import { JVxeTypes } from '/@/components/jeecg/JVxeTable/src/types';
  import { allList } from '/@/views/algorithm/algorithm.api';
  import draggable from 'vuedraggable';
  import { cloneObject } from '/@/utils';
  import { BasicForm, FormActionType } from '/@/components/Form';
  import { parseTableRecords } from '/@/utils/common_utils';
  const emit = defineEmits(['gen_params']);
  const loading = ref(false); // loading
  const extract = ref({}); // 数据抽取规则
  const alg_list = ref([]); // 算法列表
  const drag = ref(true);
  const process_rules = ref([]); // 处理规则
  const alg_params = ref({}); // 算法参数
  const editIndex = ref(null); // 编辑算法的索引
  const dataSource = ref<any[]>([]); // 数据列表
  const fields = ref([]); // 字段列表
  const formElRef = ref<Nullable<FormActionType>>(null); // 算法表单
  let schemas = ref([]);
  // 组合生成表单schemas
  function genSchemas(params) {
    console.log('gen alg params', params);
    let schema_list = [];
    for (let i = 0; i < params.length; i++) {
      let dic = params[i];
      let schema = {
        label: dic.name,
        field: dic.value,
        required: dic.required,
        component: 'Input',
        defaultValue: dic.default,
      };
      if (dic.form_type === 'select') {
        schema = {
          label: dic.name,
          field: dic.value,
          required: dic.required,
          component: 'JSelectInput',
          defaultValue: dic.default,
          componentProps: {
            showSearch: true,
            options: dic.options,
          },
        };
      } else if (dic.form_type === 'codeEditor') {
        schema = {
          label: dic.name,
          field: dic.value,
          required: dic.required,
          component: 'MonacoEditor',
          defaultValue: dic.default,
          componentProps: {
            language: dic.language || 'python',
          },
        };
      } else if (dic.form_type === 'select_fields') {
        let options = [];
        for (let n = 0; n < fields.value.length; n++) {
          options.push({ label: fields.value[n].title, value: fields.value[n].key });
        }
        schema = {
          label: dic.name,
          field: dic.value,
          required: dic.required,
          component: 'JSelectMultiple',
          defaultValue: dic.default,
          componentProps: {
            showSearch: true,
            options: options,
          },
        };
      } else if (dic.form_type === 'select_field') {
        let options = [];
        for (let n = 0; n < fields.value.length; n++) {
          options.push({ label: fields.value[n].title, value: fields.value[n].key });
        }
        schema = {
          label: dic.name,
          field: dic.value,
          required: dic.required,
          component: 'JSelectInput',
          defaultValue: dic.default,
          componentProps: {
            showSearch: true,
            options: options,
          },
        };
      }
      schema_list.push(schema);
    }
    return schema_list;
  }
  // 初始化算法表单及任务参数
  async function initForm() {
    schemas.value = genSchemas(alg_params.value.params);
    console.log(111, schemas.value);
    console.log(222, alg_params.value, await formElRef.value.getFieldsValue());
    await formElRef.value.setFieldsValue(alg_params.value.rule_dict);
    console.log(333, await formElRef.value.getFieldsValue());
  }
  // 重置算法表单及任务参数
  async function resetForm() {
    await formElRef.value.setFieldsValue({});
    schemas.value = [];
    await formElRef.value.resetFields();
    await formElRef.value.clearValidate();
    console.log(444, await formElRef.value.validate());
  }
  // 拖拽算法到流程中
  function cloneAlg(item) {
    console.log('clone', item);
    const alg_info = cloneObject(item);
    alg_info.rule_dict = {};
    return alg_info;
  }
  function handelDragAlg(drag_info) {
    console.log('drag alg 111', drag_info);
    let new_index = null;
    if (drag_info.added) {
      new_index = drag_info.added.newIndex;
      setParams(process_rules.value[new_index], new_index);
    }
    console.log('drag alg 222', new_index, process_rules.value, alg_params.value);
  }
  // 拖拽算法事件
  function handelDrag(drag_info) {
    console.log('drag111', drag_info);
    let new_index = null;
    if (drag_info.added) {
      new_index = drag_info.added.newIndex;
    } else if (drag_info.moved) {
      new_index = drag_info.moved.newIndex;
    }
    setParams(process_rules.value[new_index], new_index);
    console.log('drag222', new_index, process_rules.value, alg_params.value);
  }
  // 删除流程
  function delRule(index) {
    process_rules.value.splice(index, 1);
    alg_params.value = {};
    editIndex.value = null;
  }
  // 设置算法参数
  async function setParams(element: {}, index) {
    console.log('set params', element, index);
    alg_params.value = element;
    editIndex.value = index;
    await resetForm();
    await previewData(index > 0 ? index-1 : 0, false);
    await initForm();
  }
  // 预览数据
  async function previewData(index = null, set_params = true) {
    // 从父组件拿到抽取配置
    emit('gen_params', (val) => {
      console.log('parent666', val);
      extract.value = val.extract;
    });
    if (set_params) {
      alg_params.value.rule_dict = await formElRef.value.validate();
    }
    loading.value = true;
    try {
      let rules = process_rules.value;
      if (index != null) {
        rules = process_rules.value.slice(0, index + 1);
      }
      const res_data = await previewEtlData({
        task_params: {
          extract: extract.value,
          process_rules: rules,
        },
        run_load: false,
      });
      if (res_data) {
        console.log(res_data);
        dataSource.value = parseTableRecords(res_data.data);
        // 设置字段
        let _fields = res_data.fields;
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
      } else {
        console.log('error', res_data);
      }
    } catch (e) {
      console.log(e);
    } finally {
      loading.value = false;
    }
  }
  // 生成数据抽取配置
  function genTransform() {
    return process_rules.value;
  }
  // 初始化数据转换配置
  async function initData(taskParams) {
    console.log('init load', taskParams);
    if (!taskParams.extract) {
      extract.value = {};
      process_rules.value = [];
    } else {
      extract.value = taskParams.extract;
      process_rules.value = taskParams.process_rules || [];
    }
    alg_params.value = {};
    editIndex.value = null;
  }
  onMounted(async () => {
    // 加载算法列表
    alg_list.value = await allList({ type: 'etl_algorithm' });
    console.log('all alg', alg_list.value);
  });
  defineExpose({
    genTransform,
    initData,
  });
</script>

<style>
  .alg-list-panel {
    height: 400px;
    overflow: scroll;
  }
  .alg-list-panel::-webkit-scrollbar {
    display: none;
  }
  .alg-setting-panel {
    height: 500px;
    overflow: scroll;
  }
  .alg-setting-panel::-webkit-scrollbar {
    display: none;
  }
  .alg-box {
    width: 100%;
    height: 30px;
    color: #333;
    background: #f4f6fc;
    text-align: center;
    cursor: pointer;
    margin-bottom: 10px;
    border: 1px solid #d9d9d9;
    border-radius: 10px;
  }
  .flow-box {
    width: 100%;
    height: 30px;
    color: #333;
    background: #f4f6fc;
    text-align: center;
    cursor: pointer;
    margin-bottom: 10px;
    border: 1px solid #d9d9d9;
    border-radius: 10px;
  }
</style>
