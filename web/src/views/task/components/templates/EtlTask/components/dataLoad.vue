<template>
  <a-row>
    <a-col :span="12" style="padding-left: 5px; padding-right: 5px; border-right: 1px dashed rgb(217, 217, 217);">
      <div style="font-weight: 700;">数据装载</div>
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
      装载方式
      <br />
      <a-select
        v-model:value="load_type"
        style="width: 300px"
        @change="handleLoadTypeChange"
      >
        <a-select-option v-for="(item, index) in load_type_options" :key="index" :value="item.value">{{ item.name }}</a-select-option>
      </a-select>
      <br />
      <div v-show="load_type !== 'insert'">
        唯一字段
        <br />
        <a-select
          mode="multiple"
          v-model:value="only_fields"
          style="width: 300px"
          show-search
        >
          <a-select-option v-for="(item, index) in fields" :key="index" :value="item.key">{{ item.title }}</a-select-option>
        </a-select>
        <a-button @click="syncData" :loading="iconLoading">同步</a-button>
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
          <a-button @click="loadData" style="float: right">测试</a-button>
        </template>
      </JVxeTable>
    </a-col>
  </a-row>
</template>

<script lang="ts" setup>
  import { onMounted, ref } from 'vue';
  import type { SelectProps } from 'ant-design-vue';
  import { allList } from '/@/views/dataManage/dataModel/datamodel.api';
  import { previewEtlData } from '/@/views/dataManage/dataQuery/dataquery.api';
  import { JVxeTypes } from '/@/components/jeecg/JVxeTable/src/types';
  import { parseTableRecords } from '/@/utils/common_utils';
  import { Modal } from 'ant-design-vue';
  const emit = defineEmits(['gen_params']);
  const loading = ref(false); // loading
  const iconLoading = ref(false); // iconLoading
  const dataModelList = ref([]); // 数据模型列表
  const model_id = ref(''); // 数据模型id
  const load_type = ref('insert'); // 抽取方式
  const only_fields = ref([]); // 唯一字段列表
  const extract = ref({}); // 抽取配置
  const process_rules = ref([]); // 处理规则
  const dataSource = ref<any[]>([]); // 数据列表
  const fields = ref([]); // 字段列表
  const load_type_options = ref<SelectProps['options']>([
    {
      name: '插入',
      value: 'insert',
    },
    {
      name: '更新',
      value: 'update',
    },
    {
      name: '无则插入有则更新',
      value: 'upsert',
    },
  ]); // 抽取方式下拉配置
  // 监听模型发生变化
  async function handleModelChange(id) {
    model_id.value = id;
    // await fetchData(true);
    console.log(model_id.value);
  }
  // 监听抽取方式变化
  async function handleLoadTypeChange(t) {
    load_type.value = t;
    console.log(load_type.value);
  }
  // 数据装载预览
  async function loadData() {
    // 从父组件拿到抽取和转换配置
    Modal.confirm({
      title: '测试确认',
      content: '确认测试写入，数据将直接写入目标源？',
      okText: '确认',
      cancelText: '取消',
      async onOk() {
        emit('gen_params', (val) => {
          console.log('parent777', val);
          extract.value = val.extract;
          process_rules.value = val.process_rules;
        });
        loading.value = true;
        try {
          const res_data = await previewEtlData({
            task_params: {
              extract: extract.value,
              process_rules: process_rules.value,
              load: genLoad(),
            },
            run_load: true,
          });
          if (res_data) {
            console.log(res_data);
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
            dataSource.value = parseTableRecords(res_data.data);
          } else {
            console.log('error', res_data);
          }
        } catch (e) {
          console.log(e);
        } finally {
          loading.value = false;
        }
      },
    });
  }
  // 同步数据装载字段
  async function syncData() {
    // 从父组件拿到抽取和转换配置
    emit('gen_params', (val) => {
      console.log('parent777', val);
      extract.value = val.extract;
      process_rules.value = val.process_rules;
    });
    iconLoading.value = true;
    try {
      const res_data = await previewEtlData({
        task_params: {
          extract: extract.value,
          process_rules: process_rules.value || [],
        },
        run_load: false,
      });
      if (res_data) {
        console.log(res_data);
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
      iconLoading.value = false;
    }
  }
  // 初始化装载配置
  async function initData(taskParams) {
    console.log('init load', taskParams);
    extract.value = taskParams.extract || {};
    process_rules.value = taskParams.process_rules || [];
    const load_info = taskParams.load;
    if (!load_info) {
      model_id.value = '';
      load_type.value = 'insert';
      only_fields.value = [];
    } else {
      model_id.value = load_info.model_id;
      load_type.value = load_info.load_type || 'insert';
      only_fields.value = load_info.only_fields || [];
    }
  }
  // 生成数据抽取配置
  function genLoad() {
    return {
      model_id: model_id.value,
      load_type: load_type.value,
      only_fields: only_fields.value,
    };
  }
  onMounted(async () => {
    // 加载数据模型列表
    dataModelList.value = await allList({ auth_type: 'load' });
    console.log(dataModelList.value);
  });
  defineExpose({
    genLoad,
    initData,
  });
</script>
