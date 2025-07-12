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
      label: '告警等级',
      field: 'level',
      required: true,
      component: 'JDictSelectTag',
      componentProps: {
        dictCode: 'alert_level',
        placeholder: '请选择告警等级',
        stringToNumber: true,
      },
      colProps: {
        style: {
          width: '600px',
        },
      },
    },
    {
      label: '告警业务',
      field: 'biz',
      required: true,
      defaultValue: 'scheduler',
      component: 'Input',
      colProps: {
        style: {
          width: '600px',
        },
      },
    },
    {
      label: '告警指标',
      field: 'metric',
      required: true,
      defaultValue: 'task_fail',
      component: 'Input',
      colProps: {
        style: {
          width: '600px',
        },
      },
    },
  ]);
  export default defineComponent({
    name: 'TaskFailStrategy',
    components: { BasicForm },
    props: {
      triggerConf: {
        type: Object as PropType<Recordable>,
        default: () => ({}),
      },
    },
    setup(props, { emit }) {
      const formElRef = ref<Nullable<FormActionType>>(null);
      onMounted(async () => {
        console.log(111, props.triggerConf, await formElRef.value.getFieldsValue());
        await initParams();
      });
      // 重置表单及任务参数
      async function initParams() {
        console.log(222, await formElRef.value.getFieldsValue());
        await formElRef.value.setFieldsValue(props.triggerConf);
        console.log(333, await formElRef.value.getFieldsValue());
      }
      // 获取参数
      async function genParams() {
        return await formElRef.value.validate();
      }
      watch(
        () => props.triggerConf,
        () => {
          initParams();
        },
        { deep: true }
      );
      return {
        formElRef,
        schemas,
        genParams,
        setProps(props: FormProps) {
          const formEl = formElRef.value;
          if (!formEl) return;
          formEl.setProps(props);
        },
      };
    },
  });
</script>
