<template>
  <div class="m-4">
    <BasicForm ref="formElRef" :showActionButtonGroup="false" :labelWidth="100" :schemas="schemas" :actionColOptions="{ span: 24 }" />
  </div>
</template>
<script lang="ts">
  import { defineComponent, onMounted, PropType, ref, watch } from 'vue';
  import { BasicForm, FormActionType, FormProps } from '/@/components/Form';
  let schemas = ref([
    {
      label: '并发数',
      field: 'concurrency',
      required: true,
      component: 'InputNumber',
      defaultValue: 1,
      colProps: {
        style: {
          width: '300px',
        },
      },
    },
    {
      label: '集群地址',
      field: 'master',
      required: true,
      component: 'Input',
      colProps: {
        style: {
          width: '600px',
        },
      },
    },
    {
      field: 'language',
      label: '语言',
      required: true,
      component: 'RadioGroup',
      defaultValue: 'python',
      componentProps: {
        options: [
          { label: 'python', value: 'python' },
          { label: 'scala', value: 'scala' },
          { label: 'java', value: 'java' },
          { label: 'sql', value: 'sql' },
        ],
      },
    },
    {
      label: '部署包地址',
      field: 'package',
      required: true,
      component: 'Input',
      colProps: {
        style: {
          width: '600px',
        },
      },
      ifShow: ({ values }) => values.language == 'java' || values.language == 'scala',
    },
    {
      label: '运行类',
      field: 'class',
      required: false,
      component: 'Input',
      colProps: {
        style: {
          width: '300px',
        },
      },
      ifShow: ({ values }) => values.language == 'java' || values.language == 'scala',
    },
    {
      field: 'run_type',
      label: '运行模式',
      required: true,
      component: 'RadioGroup',
      defaultValue: 'code',
      componentProps: {
        options: [
          { label: '代码模式', value: 'code' },
          { label: '文件模式', value: 'file' },
        ],
      },
      ifShow: ({ values }) => values.language == 'python',
    },
    {
      field: 'code',
      component: 'MonacoEditor',
      label: '代码',
      required: true,
      componentProps: {
        language: 'python',
        height: '400px',
      },
      ifShow: ({ values }) => values.language == 'python' && values.run_type == 'code',
    },
    {
      field: 'file',
      component: 'Input',
      label: '文件地址',
      required: true,
      colProps: {
        style: {
          width: '600px',
        },
      },
      ifShow: ({ values }) => values.language == 'python' && values.run_type == 'file',
    },
    {
      field: 'code',
      component: 'MonacoEditor',
      label: 'sql',
      required: true,
      componentProps: {
        language: 'sql',
        height: '400px',
      },
      ifShow: ({ values }) => values.language == 'sql',
    },
  ]);
  export default defineComponent({
    name: 'FlinkTask',
    components: { BasicForm },
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
      const formElRef = ref<Nullable<FormActionType>>(null);
      onMounted(async () => {
        console.log(111, props.taskParams, props.templateInfo.params, await formElRef.value.getFieldsValue());
        await initParams();
      });
      // 重置表单及任务参数
      async function initParams() {
        console.log(222, await formElRef.value.getFieldsValue());
        await formElRef.value.setFieldsValue(props.taskParams);
        console.log(333, await formElRef.value.getFieldsValue());
      }
      // 获取任务参数
      async function genTaskParams() {
        return await formElRef.value.validate();
      }
      watch(
        () => props.taskParams,
        () => {
          initParams();
        },
        { deep: true }
      );
      return {
        formElRef,
        schemas,
        genTaskParams,
        setProps(props: FormProps) {
          const formEl = formElRef.value;
          if (!formEl) return;
          formEl.setProps(props);
        },
      };
    },
  });
</script>
