<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose showFooter :title="title" :width="'800px'" @ok="handleSubmit">
    <BasicForm @register="registerForm" />
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, computed, unref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, useForm } from '/@/components/Form/index';
  import { formSchema } from '../datamodel_field.data';
  import { getInfoById, saveOrUpdate } from '../datamodel_field.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const props = defineProps({ datamodel_id: String, model_type: String });
  const isUpdate = ref(true);
  const { createMessage } = useMessage();
  //表单配置
  const [registerForm, { setProps, resetFields, setFieldsValue, validate }] = useForm({
    //labelWidth: 150,
    schemas: formSchema,
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
      // 将 ext_params 对象转换为 JSON 字符串
      if (formData.ext_params && typeof formData.ext_params === 'object') {
        formData.ext_params = JSON.stringify(formData.ext_params, null, 2);
      }
      //表单赋值
      await setFieldsValue({
        ...formData,
      });
    } else {
      // 新增时，如果有 ext_params 对象，转换为 JSON 字符串
      if (data?.record?.ext_params && typeof data.record.ext_params === 'object') {
        data.record.ext_params = JSON.stringify(data.record.ext_params, null, 2);
      }
      await setFieldsValue({
        ...data?.record,
      });
    }
    // 隐藏底部时禁用整个表单
    await setProps({ disabled: !data?.showFooter });
  });
  //设置标题
  const title = computed(() => (!unref(isUpdate) ? '新增' : '编辑'));
  //表单提交事件
  async function handleSubmit() {
    try {
      let values = await validate();
      values.datamodel_id = props.datamodel_id;
      // 将 ext_params 字符串转换为对象
      if (values.ext_params && typeof values.ext_params === 'string') {
        try {
          values.ext_params = JSON.parse(values.ext_params);
        } catch (e) {
          createMessage.error('拓展参数格式错误，请输入有效的 JSON 格式');
          return;
        }
      }
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
