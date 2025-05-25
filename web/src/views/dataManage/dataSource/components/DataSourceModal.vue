<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose showFooter :title="title" :width="'800px'" @ok="handleSubmit">
    <BasicForm @register="registerForm">
      <template #type="{ model, field }">
        <a-select
          v-model:value="model[field]"
          style="width: 100%"
          placeholder="请选择数据源类型"
          :options="dataSourceTypeOptions"
          @change="handleTypeChange"
          :disabled="typeDisabled"
        />
      </template>
      <template #conn_conf="">
        <BasicForm @register="registerConnForm">
          <template #formFooter>
            <div style="width: 100%; text-align: center">
              <a-button :loading="loading" @click="connectTest">连通性测试</a-button>
            </div>
          </template>
        </BasicForm>
      </template>
    </BasicForm>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, computed, unref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, useForm } from '/@/components/Form/index';
  import { formSchema } from '../datasource.data';
  import { getInfoById, saveOrUpdate, ConnTest } from '../datasource.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { dataSourceTypeOptions, ConnFormSchemaMap } from '../../config/index';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const isUpdate = ref(true);
  const typeDisabled = ref(false);
  const conn_status = ref(0);
  const loading = ref(false);
  const { createMessage } = useMessage();
  //表单配置
  const [registerForm, { setProps, getFieldsValue, resetFields, setFieldsValue, validate }] = useForm({
    labelWidth: 150,
    schemas: formSchema,
    showActionButtonGroup: false,
    baseColProps: { span: 24 },
  });
  const [
    registerConnForm,
    {
      setProps: setConnProps,
      resetSchema: resetConnSchema,
      resetFields: resetConnFields,
      setFieldsValue: setConnFieldsValue,
      validate: connValidate,
    },
  ] = useForm({
    labelWidth: 150,
    schemas: ConnFormSchemaMap['mysql'],
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
      resetConnSchema(ConnFormSchemaMap[formData.type]);
      resetConnFields();
      // 连接配置表单赋值
      setConnFieldsValue({
        ...formData.conn_conf,
      });
      // 编辑时类型不允许切换
      typeDisabled.value = true;
      // 设置连接状态
      conn_status.value = formData.stauts;
    } else {
      typeDisabled.value = false;
      conn_status.value = 0;
    }
    // 隐藏底部时禁用整个表单
    setProps({ disabled: !data?.showFooter });
    setConnProps({ disabled: !data?.showFooter });
  });
  //设置标题
  const title = computed(() => (!unref(isUpdate) ? '新增' : '编辑'));
  // 数据源类型切换
  const handleTypeChange = (value: string) => {
    console.log(`selected ${value}`);
    // 重置连接配置表单schema
    resetConnSchema(ConnFormSchemaMap[value]);
    resetConnFields();
  };
  // 连通性测试
  async function connectTest(v) {
    try {
      let values = getFieldsValue();
      let conn_type = values.type;
      let conn_conf = await connValidate();
      loading.value = true;
      await ConnTest({ type: conn_type, conn_conf: conn_conf });
      loading.value = false;
      conn_status.value = 1;
      console.log('connSucc', conn_status.value);
    } catch (e) {
      conn_status.value = 0;
      loading.value = false;
      console.log('connError', e, conn_status.value);
    }
  }
  //表单提交事件
  async function handleSubmit(v) {
    try {
      let values = await validate();
      // 设置连接配置
      values.conn_conf = await connValidate();
      // 设置连接状态
      values.status = conn_status.value;
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
