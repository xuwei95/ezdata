<template>
  <div class="m-4">
    <BasicForm
      ref="formElRef"
      :showActionButtonGroup="false"
      :labelWidth="100"
      :schemas="schemas"
      :actionColOptions="{ span: 24 }"
    />
  </div>
</template>
<script lang="ts">
  import { defineComponent, onMounted, PropType, ref, watch } from 'vue';
  import { BasicForm, FormActionType, FormProps } from '/@/components/Form';
  let schemas = ref([]);
  export default defineComponent({
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
        await initForm();
        await initParams();
      });
      // 重置表单及任务参数
      async function initParams() {
        schemas.value = props.templateInfo.params;
        console.log(222, await formElRef.value.getFieldsValue());
        await formElRef.value.setFieldsValue(props.taskParams);
        console.log(333, await formElRef.value.getFieldsValue());
      }
      // 重置表单及任务参数
      async function initForm() {
        await formElRef.value.setFieldsValue({});
        schemas.value = [];
        await formElRef.value.resetFields();
        await formElRef.value.clearValidate();
        console.log(444, await formElRef.value.validate());
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
