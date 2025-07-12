<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose showFooter :title="title" :width="'800px'" @ok="handleSubmit">
    <BasicForm @register="registerForm">
      <template #field_type="{ model, field }">
        <a-select
          v-model:value="model[field]"
          style="width: 100%"
          placeholder="请选择模型类型"
          :options="typeOptions"
          @change="handleTypeChange"
          :disabled="typeDisabled"
        />
      </template>
      <template #ext_params="">
        <BasicForm @register="registerFieldConfForm" />
      </template>
    </BasicForm>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, computed, unref, reactive, defineProps } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, useForm } from '/@/components/Form/index';
  import { formSchema } from '../datamodel_field.data';
  import { getInfoById, saveOrUpdate } from '../datamodel_field.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { SelectProps } from 'ant-design-vue';
  import { ModelFieldSchemaMap } from '../../../../config';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const props = defineProps({ datamodel_id: String, model_type: String });
  const typeOptions = ref<SelectProps['options']>([]);
  const typeDisabled = ref(false);
  const isUpdate = ref(true);
  const { createMessage } = useMessage();
  //表单配置
  const [registerForm, { setProps, resetFields, setFieldsValue, updateSchema, validate }] = useForm({
    //labelWidth: 150,
    schemas: formSchema,
    showActionButtonGroup: false,
    baseColProps: { span: 24 },
  });
  const [
    registerFieldConfForm,
    {
      setProps: setFieldConfProps,
      resetSchema: resetFieldConfSchema,
      resetFields: resetFieldConfFields,
      setFieldsValue: setFieldConfFieldsValue,
      validate: FieldConfValidate,
    },
  ] = useForm({
    schemas: [],
    showActionButtonGroup: false,
    baseColProps: { span: 24 },
  });
  //表单赋值
  const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
    //重置表单
    await resetFields();
    setModalProps({ confirmLoading: false, showCancelBtn: !!data?.showFooter, showOkBtn: !!data?.showFooter });
    isUpdate.value = !!data?.isUpdate;
    if (unref(isUpdate)) {
      // 请求详情接口拿到详情数据
      let formData = data.record;
      try {
        const res_data = await getInfoById({ id: data.record.id });
        if (res_data) {
          formData = res_data;
        } else {
          console.log('error', res_data);
        }
      } catch (error) {
        console.log('error', error);
      }
      //表单赋值
      await setFieldsValue({
        ...formData,
      });
      // 重置模型配置表单schema
      let fieldSchema = ModelFieldSchemaMap[props.model_type] || [];
      if (fieldSchema.length > 0) {
        // 显示拓展参数
        await updateSchema({ field: 'ext_params', show: true });
        await resetFieldConfSchema(fieldSchema);
      } else {
        // 隐藏拓展参数
        await updateSchema({ field: 'ext_params', show: false });
      }
      await resetFieldConfFields();
      // 模型配置表单赋值
      await setFieldConfFieldsValue({
        ...formData.ext_params,
      });
    } else {
      // 重置模型配置表单schema
      console.log(props.model_type, ModelFieldSchemaMap);
      let fieldSchema = ModelFieldSchemaMap[props.model_type] || [];
      if (fieldSchema.length > 0) {
        // 显示拓展参数
        await updateSchema({ field: 'ext_params', show: true });
        await resetFieldConfSchema(fieldSchema);
      } else {
        // 隐藏拓展参数
        await updateSchema({ field: 'ext_params', show: false });
      }
      await resetFieldConfFields();
    }
    // 隐藏底部时禁用整个表单
    await setProps({ disabled: !data?.showFooter });
    await setFieldConfProps({ disabled: !data?.showFooter });
  });
  //设置标题
  const title = computed(() => (!unref(isUpdate) ? '新增' : '编辑'));
  // 数据模型类型切换
  const handleTypeChange = (value: string) => {
    console.log(`type selected ${value}`);
  };
  //表单提交事件
  async function handleSubmit() {
    try {
      let values = await validate();
      values.datamodel_id = props.datamodel_id;
      values.ext_params = await FieldConfValidate();
      setModalProps({ confirmLoading: true });
      //提交表单
      await saveOrUpdate(values, isUpdate.value);
      //关闭弹窗
      closeModal();
      //刷新列表
      emit('success');
    } finally {
      setModalProps({ confirmLoading: false });
    }
  }
</script>

<style lang="less" scoped>
  /** 时间和数字输入框样式 */
  :deep(.ant-input-number) {
    width: 100%;
  }

  :deep(.ant-calendar-picker) {
    width: 100%;
  }
</style>
