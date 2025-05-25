<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose defaultFullscreen showFooter :title="title" :width="'800px'" @ok="handleSubmit">
    <a-steps v-model:current="current">
      <a-step title="基本信息" disabled />
      <a-step title="任务配置" disabled />
    </a-steps>
    <div v-show="current === 0">
      <BasicForm @register="registerForm" />
    </div>
    <div v-show="current === 1">
      <div v-if="templateInfo.type === 1">
        <component ref="componentForm" :is="componentMap.get(templateInfo.component)" :taskParams="taskParams" :templateInfo="templateInfo" />
      </div>
      <div v-if="templateInfo.type === 2">
        <dynamicTaskForm ref="dynamicForm" :taskParams="taskParams" :templateInfo="templateInfo" />
      </div>
    </div>
    <a-button v-if="current < 1" type="primary" @click="nextStep">下一步</a-button>
    <a-button v-if="current > 0" style="margin-left: 8px" @click="prevStep">上一步</a-button>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, computed, unref, reactive } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, useForm } from '/@/components/Form/index';
  import { formSchema } from '../task.data';
  import { getInfoById, getTemplateParams, saveOrUpdate } from '../task.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  import dynamicTaskForm from './dynamicTaskForm.vue';
  import { componentMap } from './templates/index';
  const dynamicForm = ref(null);
  const componentForm = ref(null);
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  // 任务模版信息
  const templateInfo = ref({});
  const template_code = ref('');
  const isUpdate = ref(true);
  const isCopy = ref(false);
  const taskParams = ref({});
  const current = ref<number>(0);
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
    isCopy.value = !!data?.isCopy;
    current.value = 0;
    taskParams.value = {};
    if (unref(isUpdate)) {
      // 请求详情接口拿到详情数据
      let formData = data.record;
      try {
        const res_data = await getInfoById({ id: data.record.id });
        if (res_data) {
          formData = res_data;
          taskParams.value = res_data.params;
          if (isCopy.value) {
            formData.id = '';
            formData.name = formData.name + '_copy';
            console.log('copy35324523', formData, taskParams.value);
          }
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
  //设置标题
  const title = computed(() => (!unref(isUpdate) ? '新增' : '编辑'));
  // 点击下一步
  async function nextStep() {
    let values = await validate();
    const res = await getTemplateParams({ code: values.template_code });
    if (res) {
      // 获取任务组件及参数
      templateInfo.value = res;
      console.log('next5555', res);
      console.log('next66666', templateInfo.value.component, componentMap, componentMap.get(templateInfo.value.component));
    } else {
      console.log('error', res);
    }
    current.value++;
  }
  // 点击上一步
  function prevStep() {
    current.value--;
  }
  //表单提交事件
  async function handleSubmit(v) {
    try {
      // 设置任务基础信息
      let values = await validate();
      // 类型设置为普通任务
      values.task_type = 1;
      // 设置任务参数
      console.log('000000', taskParams.value);
      try {
        if (templateInfo.value.type === 1) {
          taskParams.value = await componentForm.value.genTaskParams();
          console.log(1111111111, taskParams.value);
        } else {
          taskParams.value = await dynamicForm.value.genTaskParams();
          console.log(2222222222, taskParams.value);
        }
        values.params = taskParams.value;
      } catch (e) {
        console.log(44444444, e);
      }
      console.log(3333333333, isCopy.value, values, values.trigger_date);
      setModalProps({ confirmLoading: true });
      await saveOrUpdate(values, isCopy.value ? false : isUpdate.value);
      setModalProps({ confirmLoading: false });
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
