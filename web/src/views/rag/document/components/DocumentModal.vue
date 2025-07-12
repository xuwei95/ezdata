<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose showFooter :title="title" :width="'800px'" @ok="handleSubmit">
    <BasicForm @register="registerForm">
      <template #document_type="{ model, field }">
        <a-select
          v-model:value="model[field]"
          style="width: 100%"
          placeholder="请选择文档类型"
          :options="documentTypeOptions"
          @change="handleTypeChange"
          :disabled="typeDisabled"
        />
      </template>
      <template #meta_data="">
        <BasicForm @register="registerMetadataForm" />
      </template>
<!--      <template #chunk_strategy="">-->
<!--        <BasicForm @register="registerStrategyForm" />-->
<!--      </template>-->
    </BasicForm>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, computed, unref, reactive } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, FormSchema, useForm } from "/@/components/Form/index";
  import { documentTypeOptions, metaDataFormSchemaMap } from '../document.data';
  import { getInfoById, saveOrUpdate } from '../document.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { allList as allDataSetList } from "@/views/rag/dataset/dataset.api";
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const isUpdate = ref(true);
  const { createMessage } = useMessage();
  const typeDisabled = ref(false);
  //表单数据
  const urlParams = new URLSearchParams(window.location.search);
  const defaultDatasetId = urlParams.get('dataset_id') || '';
  const formSchema: FormSchema[] = [
    {
      label: '名称',
      field: 'name',
      required: false,
      component: 'Input',
    },
    {
      label: '所属数据集',
      field: 'dataset_id',
      required: false,
      component: 'ApiSelect',
      defaultValue: defaultDatasetId,
      dynamicDisabled: ({ values }) => {
        return !!values.id || defaultDatasetId != '';
      },
      componentProps: {
        api: allDataSetList,
        params: {},
        labelField: 'name',
        valueField: 'id',
      },
    },
    {
      label: '文档类型',
      field: 'document_type',
      required: true,
      defaultValue: 'upload_file',
      slot: 'document_type',
      component: 'Input',
    },
    {
      label: '',
      field: 'meta_data',
      required: false,
      slot: 'meta_data',
      component: 'Input',
    },
    // {
    //   label: '',
    //   field: 'chunk_strategy',
    //   required: true,
    //   slot: 'chunk_strategy',
    //   component: 'Input',
    // },
    {
      label: '简介描述',
      field: 'description',
      required: false,
      component: 'InputTextArea',
    },
    // TODO 主键隐藏字段，目前写死为ID
    {
      label: '',
      field: 'id',
      component: 'Input',
      show: false,
    },
  ];
  //表单配置
  const [registerForm, { setProps, resetFields, setFieldsValue, validate }] = useForm({
    //labelWidth: 150,
    schemas: formSchema,
    showActionButtonGroup: false,
    baseColProps: { span: 24 },
  });
  const [
    registerMetadataForm,
    {
      setProps: setMetadataProps,
      resetSchema: resetMetadataSchema,
      resetFields: resetMetadataFields,
      setFieldsValue: setMetadataFieldsValue,
      validate: MetadataValidate,
    },
  ] = useForm({
    labelWidth: 150,
    schemas: metaDataFormSchemaMap['upload_file'],
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
      setFieldsValue({
        ...formData,
      });
      // 重置连接配置表单schema
      resetMetadataSchema(metaDataFormSchemaMap[formData.document_type]);
      resetMetadataFields();
      // 连接配置表单赋值
      setMetadataFieldsValue({
        ...formData.meta_data,
      });
      // 编辑时类型不允许切换
      typeDisabled.value = true;
    } else {
      typeDisabled.value = false;
    }
    // 隐藏底部时禁用整个表单
    setProps({ disabled: !data?.showFooter });
    setMetadataProps({ disabled: !data?.showFooter });
  });
  //设置标题
  const title = computed(() => (!unref(isUpdate) ? '新增' : '编辑'));
  // 数据模型类型切换
  const handleTypeChange = (value) => {
    console.log(`type selected ${value}`);
    resetMetadataSchema(metaDataFormSchemaMap[value]);
    resetMetadataFields();
  };
  //表单提交事件
  async function handleSubmit(v) {
    try {
      let values = await validate();
      setModalProps({ confirmLoading: true });
      // 设置连接配置
      values.meta_data = await MetadataValidate();
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
