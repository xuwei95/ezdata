<template>
  <div class="m-4">
    <div class="extract-panel">
      <dataExtract ref="extractForm" />
    </div>
    <div class="transform-panel">
      <dataTransform ref="transForm" @gen_params="genParams" />
    </div>
    <div class="load-panel">
      <dataLoad ref="loadForm" @gen_params="genParams" />
    </div>
  </div>
</template>
<script lang="ts">
  import { defineComponent, onMounted, PropType, watch, ref } from 'vue';
  import dataExtract from './components/dataExtract.vue';
  import dataLoad from './components/dataLoad.vue';
  import dataTransform from './components/dataTransform.vue';
  import { cloneObject } from '/@/utils';
  export default defineComponent({
    name: 'EtlTask',
    components: {
      dataExtract,
      dataLoad,
      dataTransform,
    },
    props: {
      taskParams: {
        type: Object as PropType<Recordable>,
        default: () => ({}),
      },
      templateInfo: {
        type: Object as PropType<Recordable>,
        default: () => ({}),
      },
    },
    setup(props, { emit }) {
      const extractForm = ref(null);
      const transForm = ref(null);
      const loadForm = ref(null);
      const etlParams = ref({});
      onMounted(async () => {
        await initParams();
      });
      // 重置表单及任务参数
      async function initParams() {
        console.log('init', props.taskParams);
        etlParams.value = cloneObject(props.taskParams);
        // 初始化数据抽取
        extractForm.value.initData(etlParams.value);
        // 初始化数据转换
        transForm.value.initData(etlParams.value);
        // 初始化数据装载
        loadForm.value.initData(etlParams.value);
      }
      // 获取任务参数
      const genParams = (callback) => {
        let data = {
          extract: extractForm.value.genExtract(),
          process_rules: transForm.value.genTransform(),
          load: loadForm.value.genLoad(),
        };
        console.log('gen params666', data);
        callback(data); //返回data值
      };
      // 获取任务参数
      async function genTaskParams() {
        console.log('submit', extractForm.value, transForm.value, loadForm.value);
        console.log('extract', extractForm.value.genExtract());
        console.log('process_rules', transForm.value.genTransform());
        console.log('load', loadForm.value.genLoad());
        return {
          extract: extractForm.value.genExtract(),
          process_rules: transForm.value.genTransform(),
          load: loadForm.value.genLoad(),
        };
      }
      watch(
        () => props.taskParams,
        () => {
          initParams();
        },
        { deep: true }
      );
      return {
        genParams,
        genTaskParams,
        extractForm,
        transForm,
        loadForm,
      };
    },
  });
</script>
<style scoped>
  .extract-panel {
    height: 520px;
    overflow: scroll;
    border-bottom: 1px solid rgb(242, 242, 242);
    padding: 20px;
  }
  .transform-panel {
    height: 580px;
    overflow: scroll;
    border-bottom: 1px solid rgb(242, 242, 242);
    padding: 20px;
  }
  .load-panel {
    height: 520px;
    overflow: scroll;
    border-bottom: 1px solid rgb(242, 242, 242);
    padding: 20px;
  }
</style>
