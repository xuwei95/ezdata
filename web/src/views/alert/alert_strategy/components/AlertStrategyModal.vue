<template>
  <BasicModal v-bind="$attrs" @register="registerModal" defaultFullscreen destroyOnClose showFooter :title="title" width="800px" @ok="handleSubmit">
    <BasicForm @register="registerForm">
      <template #template_code="{ model, field }">
        <a-select
          v-model:value="model[field]"
          style="width: 300px"
          placeholder="请选择策略模版"
          :options="TemplateCodeOptions"
          @change="handleTemplateCodeChange"
          :disabled="!!model.id"
        />
      </template>
      <template #trigger_conf="">
        <component ref="componentForm" :is="componentMap.get(template_code)" :triggerConf="trigger_conf" />
      </template>
      <template #forward_conf="">
        <AlertForwardList ref="forwardForm" :forwardConf="forward_conf" />
      </template>
    </BasicForm>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, computed, unref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, useForm } from '/@/components/Form/index';
  import { formSchema } from '../alert_strategy.data';
  import { getInfoById, saveOrUpdate } from '../alert_strategy.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { componentMap, TemplateCodeOptions } from './templates/index';
  import AlertForwardList from './AlertForwardList.vue';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const isUpdate = ref(true);
  const { createMessage } = useMessage();
  const componentForm = ref(null);
  const forwardForm = ref(null);
  const template_code = ref('');
  const trigger_conf = ref({});
  const forward_conf = ref([]);
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
          template_code.value = res_data.template_code;
          trigger_conf.value = res_data.trigger_conf;
          forward_conf.value = res_data.forward_conf;
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
    }
    // 隐藏底部时禁用整个表单
    setProps({ disabled: !data?.showFooter });
  });
  // 数据源类型切换
  const handleTemplateCodeChange = (value: string) => {
    console.log(`selected ${value}`);
    template_code.value = value;
    trigger_conf.value = {};
  };
  //设置标题
  const title = computed(() => (!unref(isUpdate) ? '新增' : '编辑'));
  //表单提交事件
  async function handleSubmit(v) {
    try {
      let values = await validate();
      trigger_conf.value = await componentForm.value.genParams();
      values.trigger_conf = trigger_conf.value;
      forward_conf.value = await forwardForm.value.genParams();
      values.forward_conf = forward_conf.value;
      console.log(values);
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
