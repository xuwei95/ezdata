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
  import { ref, computed, unref, onMounted } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, useForm } from '/@/components/Form/index';
  import { formSchema } from '../datasource.data';
  import { getInfoById, saveOrUpdate, ConnTest, getDataSourceTypes, getDataSourceConfig } from '../datasource.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const isUpdate = ref(true);
  const typeDisabled = ref(false);
  const conn_status = ref(0);
  const loading = ref(false);
  const { createMessage } = useMessage();

  // 动态数据源类型选项和配置
  const dataSourceTypeOptions = ref([]);
  const connFormSchemaMap = ref({});

  // 获取数据源类型
  const loadDataSourceTypes = async () => {
    try {
      const res = await getDataSourceTypes();
      if (res) {
        dataSourceTypeOptions.value = res;
      }
    } catch (error) {
      console.error('获取数据源类型失败:', error);
      createMessage.error('获取数据源类型失败');
    }
  };

  // 获取数据源配置
  const loadDataSourceConfig = async (type: string) => {
    if (!type) {
      console.warn('数据源类型为空');
      return [];
    }
    try {
      const res = await getDataSourceConfig(type);
      if (res&& Array.isArray(res) && res.length > 0) {
        // 转换后端配置格式为前端表单schema格式
        const schema = convertToFormSchema(res);
        connFormSchemaMap.value[type] = schema;
        return schema;
      } else {
        console.warn(`数据源类型 ${type} 的配置为空`);
        return [];
      }
    } catch (error) {
      console.error('获取数据源配置失败:', error);
      createMessage.error(`获取数据源配置失败: ${error?.message || '未知错误'}`);
      return [];
    }
  };

  // 转换后端配置格式为前端FormSchema格式
  const convertToFormSchema = (config: any[]) => {
    return config.map(item => {
      const schema: any = {
        label: item.label,
        field: item.field,
        required: item.required,
        component: convertComponentType(item.component),
      };

      if (item.default !== undefined) {
        schema.defaultValue = item.default;
      }

      if (item.options) {
        schema.componentProps = {
          options: item.options
        };
      }

      if (item.min !== undefined) {
        schema.componentProps = schema.componentProps || {};
        schema.componentProps.min = item.min;
      }

      if (item.if_show) {
        schema.ifShow = ({ values }) => values[item.if_show.field] === item.if_show.value;
      }

      return schema;
    });
  };

  // 转换组件类型
  const convertComponentType = (component: string) => {
    const componentMap = {
      'Input': 'Input',
      'Number': 'InputNumber',
      'Password': 'InputPassword',
      'Select': 'JSelectInput',
      'Radio': 'RadioGroup',
      'JSONEditor': 'MonacoEditor'
    };
    return componentMap[component] || 'Input';
  };
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
      setFieldsValue({
        ...formData,
      });

      // 加载数据源配置
      let schema = connFormSchemaMap.value[formData.type];
      if (!schema) {
        schema = await loadDataSourceConfig(formData.type);
      }

      if (schema && schema.length > 0) {
        // 重置连接配置表单schema
        resetConnSchema(schema);
        resetConnFields();
        // 连接配置表单赋值
        setConnFieldsValue({
          ...formData.conn_conf,
        });
      } else {
        // 如果schema为空，重置为空数组，避免表单显示错误
        resetConnSchema([]);
        resetConnFields();
        createMessage.warning(`数据源类型 ${formData.type} 的配置表单未加载成功`);
      }

      // 编辑时类型不允许切换
      typeDisabled.value = true;
      // 设置连接状态
      conn_status.value = formData.stauts;
    } else {
      typeDisabled.value = false;
      conn_status.value = 0;
      // 加载默认数据源配置（mysql）
      const defaultType = 'mysql';
      let schema = connFormSchemaMap.value[defaultType];
      if (!schema) {
        schema = await loadDataSourceConfig(defaultType);
      }
      if (schema && schema.length > 0) {
        resetConnSchema(schema);
        resetConnFields();
      } else {
        // 如果默认配置加载失败，重置为空数组
        resetConnSchema([]);
        resetConnFields();
        createMessage.warning('默认数据源配置加载失败，请选择数据源类型后重试');
      }
    }
    // 隐藏底部时禁用整个表单
    setProps({ disabled: !data?.showFooter });
    setConnProps({ disabled: !data?.showFooter });
  });
  //设置标题
  const title = computed(() => (!unref(isUpdate) ? '新增' : '编辑'));
  // 数据源类型切换
  const handleTypeChange = async (value: string) => {
    console.log(`selected ${value}`);

    if (!value) {
      resetConnSchema([]);
      resetConnFields();
      return;
    }

    // 加载该类型的配置schema
    let schema = connFormSchemaMap.value[value];
    if (!schema) {
      schema = await loadDataSourceConfig(value);
    }

    if (schema && schema.length > 0) {
      // 重置连接配置表单schema
      resetConnSchema(schema);
      resetConnFields();
    } else {
      // 如果schema为空，重置为空数组
      resetConnSchema([]);
      resetConnFields();
    }
  };
  // 连通性测试
  async function connectTest(v) {
    try {
      let values = getFieldsValue();
      let conn_type = values.type;
      
      if (!conn_type) {
        createMessage.error('请先选择数据源类型');
        return;
      }

      let conn_conf = await connValidate();

      loading.value = true;
      await ConnTest({ type: conn_type, conn_conf: conn_conf });
      loading.value = false;
      conn_status.value = 1;
      createMessage.success('连接测试成功');
      console.log('connSucc', conn_status.value);
    } catch (e) {
      conn_status.value = 0;
      loading.value = false;
      const errorMsg = e?.response?.data?.msg || e?.message || '连接测试失败';
      createMessage.error(`连接测试失败: ${errorMsg}`);
      console.log('connError', e, conn_status.value);
    }
  }
  //表单提交事件
  async function handleSubmit(v) {
    try {
      let values = await validate();
      
      // 检查数据源类型
      if (!values.type) {
        createMessage.error('请选择数据源类型');
        return;
      }

      // 检查连接配置表单是否有字段
      let schema = connFormSchemaMap.value[values.type];
      if (!schema || schema.length === 0) {
        // 尝试重新加载配置
        schema = await loadDataSourceConfig(values.type);
        if (!schema || schema.length === 0) {
          createMessage.error('连接配置表单未加载，请刷新页面重试');
          return;
        }
      }

      // 设置连接配置
      let conn_conf = await connValidate();
      
      // 检查连接配置是否为空
      if (!conn_conf || Object.keys(conn_conf).length === 0) {
        createMessage.error('请填写连接配置信息');
        return;
      }

      values.conn_conf = conn_conf;
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
    } catch (error) {
      const errorMsg = error?.response?.data?.msg || error?.message || '提交失败';
      createMessage.error(`提交失败: ${errorMsg}`);
    } finally {
      setModalProps({ confirmLoading: false });
    }
  }

  // 组件挂载时加载数据源类型
  onMounted(() => {
    loadDataSourceTypes();
  });
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
