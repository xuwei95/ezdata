<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose showFooter :title="title" :width="'800px'" @ok="handleSubmit">
    <BasicForm @register="registerForm">
      <template #datasource_id="{ model, field }">
        <a-select
          v-model:value="model[field]"
          style="width: 100%"
          placeholder="请选择所属数据源"
          :options="datasourceOptions"
          @change="handleSourceChange"
          :disabled="datasourceDisabled"
        />
      </template>
      <template #type="{ model, field }">
        <a-select
          v-model:value="model[field]"
          style="width: 100%"
          placeholder="请选择模型类型"
          :options="typeOptions"
          @change="handleTypeChange"
          :disabled="typeDisabled"
        />
      </template>
      <template #model_conf="">
        <BasicForm @register="registerModelConfForm" />
      </template>
    </BasicForm>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, computed, unref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, useForm } from '/@/components/Form/index';
  import { formSchema } from '../datamodel.data';
  import { getInfoById, saveOrUpdate, allSourceList } from '../datamodel.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { SelectProps } from 'ant-design-vue';
  import { ModelFormSchemaMap, dataModelTypeOptionsMap } from '../../config';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const isUpdate = ref(true);
  const isCopy = ref(false);
  const typeOptions = ref<SelectProps['options']>([]);
  const typeDisabled = ref(false);
  const datasourceOptions = ref<SelectProps['options']>([]);
  const datasourceDisabled = ref(false);
  const datasourceTypeMap = ref({});
  const { createMessage } = useMessage();
  //表单配置
  const [registerForm, { setProps, resetFields, setFieldsValue, validate }] = useForm({
    labelWidth: 150,
    schemas: formSchema,
    showActionButtonGroup: false,
    baseColProps: { span: 24 },
  });
  const [
    registerModelConfForm,
    {
      getFieldsValue: getModelConfFieldsValue,
      setProps: setModelConfProps,
      resetSchema: resetModelConfSchema,
      resetFields: resetModelConfFields,
      setFieldsValue: setModelConfFieldsValue,
      clearValidate: clearModelConfValidate,
      validate: modelConfValidate,
    },
  ] = useForm({
    labelWidth: 150,
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
    isCopy.value = !!data?.isCopy;
    if (unref(isUpdate)) {
      // 请求详情接口拿到详情数据
      let formData = data.record;
      try {
        const res_data = await getInfoById({ id: data.record.id });
        if (res_data) {
          formData = res_data;
          if (isCopy.value) {
            formData.id = '';
            formData.name = formData.name + '_copy';
            console.log('copy35324523', formData);
          }
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
      await clearModelConfValidate();
      await resetModelConfSchema(ModelFormSchemaMap[formData.type]);
      await resetModelConfFields();
      // 模型配置表单赋值
      await setModelConfFieldsValue({
        ...formData.model_conf,
      });
      // 加载数据源下拉列表
      await fetchDataSources();
      // 加载模型类型下拉列表
      await handleModelTypes(formData.datasource_id, false);
      // 编辑时类型不允许切换
      typeDisabled.value = true;
      datasourceDisabled.value = true;
    } else {
      // 加载数据源下拉列表
      await fetchDataSources();
      // 加载模型类型下拉列表
      await handleModelTypes();
      typeDisabled.value = false;
      datasourceDisabled.value = false;
    }
    // 隐藏底部时禁用整个表单
    setProps({ disabled: !data?.showFooter });
    setModelConfProps({ disabled: !data?.showFooter });
  });
  //设置标题
  const title = computed(() => (!unref(isUpdate) ? '新增' : '编辑'));
  // 数据源切换
  const handleSourceChange = (value: string) => {
    console.log(`selected ${value}`);
    handleModelTypes(value);
  };
  // 切换可用数据模型类型下拉
  function handleModelTypes(datasource_id = '', reset = true) {
    let datasource_type = datasourceTypeMap[datasource_id] || '';
    let type_options = dataModelTypeOptionsMap[datasource_type] || [];
    typeOptions.value = type_options;
    // 切换数据源时将模型类型重置为可选项的第一个
    if (type_options.length > 0 && reset) {
      let new_type = type_options[0].value;
      setFieldsValue({ type: new_type });
      handleTypeChange(new_type);
    }
  }
  // 数据模型类型切换
  const handleTypeChange = (value) => {
    console.log(`type selected ${value}`);
    resetModelConfSchema(ModelFormSchemaMap[value]);
    resetModelConfFields();
  };
  // 查询数据源列表
  async function fetchDataSources() {
    let data_li = await allSourceList({});
    datasourceOptions.value = [];
    datasourceTypeMap.value = {};
    for (let i = 0; i < data_li.length; i++) {
      datasourceOptions.value.push({ label: data_li[i].name, value: data_li[i].id });
      datasourceTypeMap[data_li[i].id] = data_li[i].type;
    }
  }
  //表单提交事件
  async function handleSubmit(v) {
    try {
      let values = await validate();
      // 设置连接配置
      console.log(666, values);
      let v = await getModelConfFieldsValue();
      console.log(777, v);
      values.model_conf = await getModelConfFieldsValue();
      console.log('submit', values);
      setModalProps({ confirmLoading: true });
      //提交表单
      await saveOrUpdate(values, isCopy.value ? false : isUpdate.value);
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
