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
  import { getInfoById, saveOrUpdate, allSourceList, getModelTypes, getModelConfig } from '../datamodel.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { SelectProps } from 'ant-design-vue';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const isUpdate = ref(true);
  const isCopy = ref(false);
  const typeOptions = ref<SelectProps['options']>([]);
  const typeDisabled = ref(false);
  const datasourceOptions = ref<SelectProps['options']>([]);
  const datasourceDisabled = ref(false);
  const datasourceTypeMap = ref({});
  const modelConfSchemaMap = ref({});
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
      // 加载数据源下拉列表
      await fetchDataSources();
      // 加载模型类型下拉列表
      await handleModelTypes(formData.datasource_id, false);

      // 加载模型配置
      let schema = modelConfSchemaMap.value[formData.type];
      if (!schema) {
        schema = await loadModelConfig(formData.type);
      }

      if (schema && schema.length > 0) {
        // 重置模型配置表单schema
        await clearModelConfValidate();
        await resetModelConfSchema(schema);
        await resetModelConfFields();

        // 提取默认值
        const defaultValues: Record<string, any> = {};
        schema.forEach((item: any) => {
          if (item.defaultValue !== undefined) {
            defaultValues[item.field] = item.defaultValue;
          }
        });

        // 合并默认值和表单数据，表单数据优先级更高
        const finalValues = { ...defaultValues, ...formData.model_conf };

        // 模型配置表单赋值
        await setModelConfFieldsValue(finalValues);
      } else {
        // 如果schema为空，重置为空数组
        await clearModelConfValidate();
        await resetModelConfSchema([]);
        await resetModelConfFields();
        createMessage.warning(`数据模型类型 ${formData.type} 的配置表单未加载成功`);
      }
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
  // 加载数据模型类型列表
  const loadModelTypes = async (datasource_id: string) => {
    if (!datasource_id) {
      console.warn('数据源ID为空');
      return [];
    }
    try {
      const res = await getModelTypes(datasource_id);
      if (res && Array.isArray(res) && res.length > 0) {
        return res;
      } else {
        console.warn(`数据源 ${datasource_id} 的模型类型为空`);
        return [];
      }
    } catch (error) {
      console.error('获取数据模型类型失败:', error);
      createMessage.error(`获取数据模型类型失败: ${error?.message || '未知错误'}`);
      return [];
    }
  };

  // 加载数据模型配置
  const loadModelConfig = async (model_type: string) => {
    if (!model_type) {
      console.warn('数据模型类型为空');
      return [];
    }
    try {
      console.log(`开始加载模型配置: ${model_type}`);
      const res = await getModelConfig(model_type);
      console.log(`后端返回的配置:`, res);

      if (res && Array.isArray(res) && res.length > 0) {
        // 转换后端配置格式为前端表单schema格式
        const schema = convertToFormSchema(res);
        console.log(`转换后的 schema:`, schema);
        modelConfSchemaMap.value[model_type] = schema;
        return schema;
      } else {
        console.warn(`数据模型类型 ${model_type} 的配置为空`, res);
        return [];
      }
    } catch (error) {
      console.error('获取数据模型配置失败:', error);
      createMessage.error(`获取数据模型配置失败: ${error?.message || '未知错误'}`);
      return [];
    }
  };

  // 转换后端配置格式为前端FormSchema格式
  const convertToFormSchema = (config: any[]) => {
    if (!config || !Array.isArray(config)) {
      console.error('Invalid config:', config);
      return [];
    }

    return config.map(item => {
      const schema: any = {
        label: item.label || '',
        field: item.field || '',
        required: item.required || false,
        component: convertComponentType(item.component || 'Input'),
      };

      // 初始化 componentProps
      schema.componentProps = {};

      // 处理默认值
      if (item.default !== undefined && item.default !== null) {
        schema.defaultValue = item.default;
      }

      // 合并后端传递的 componentProps
      if (item.componentProps && typeof item.componentProps === 'object') {
        schema.componentProps = { ...item.componentProps };
      }

      // 处理 options（向后兼容，如果后端直接传 options）
      if (item.options && Array.isArray(item.options)) {
        if (!schema.componentProps.options) {
          schema.componentProps.options = item.options;
        }
      }

      // 处理 min/max
      if (item.min !== undefined) {
        schema.componentProps.min = item.min;
      }
      if (item.max !== undefined) {
        schema.componentProps.max = item.max;
      }

      // 处理 MonacoEditor 特殊逻辑
      const componentType = item.component || '';
      if (componentType === 'JSONEditor' || componentType === 'MonacoEditor') {
        // 如果后端没有指定 language，默认使用 json
        if (!schema.componentProps.language) {
          schema.componentProps.language = 'json';
        }
      }

      // 处理 placeholder
      if (item.placeholder) {
        schema.componentProps.placeholder = item.placeholder;
      }

      // 处理条件显示
      if (item.if_show && typeof item.if_show === 'object') {
        const ifShowField = item.if_show.field;
        const ifShowValue = item.if_show.value;
        schema.ifShow = ({ values }) => values[ifShowField] === ifShowValue;
      }

      console.log('Converted schema:', schema);
      return schema;
    });
  };

  // 转换组件类型
  const convertComponentType = (component: string) => {
    const componentMap = {
      'Input': 'Input',
      'Number': 'InputNumber',
      'InputNumber': 'InputNumber',
      'Password': 'InputPassword',
      'Select': 'JSelectInput',
      'Radio': 'RadioGroup',
      'JSONEditor': 'MonacoEditor',
      'MonacoEditor': 'MonacoEditor',
      'JDictSelectTag': 'JDictSelectTag',
      'JCheckbox': 'JCheckbox',
      'JSelectInput': 'JSelectInput',
      'Textarea': 'InputTextArea'
    };
    return componentMap[component] || 'Input';
  };

  // 切换可用数据模型类型下拉
  async function handleModelTypes(datasource_id = '', reset = true) {
    if (!datasource_id) {
      typeOptions.value = [];
      return;
    }

    // 加载该数据源支持的模型类型
    const type_options = await loadModelTypes(datasource_id);
    typeOptions.value = type_options;

    // 切换数据源时将模型类型重置为可选项的第一个
    if (type_options.length > 0 && reset) {
      let new_type = type_options[0].value;
      setFieldsValue({ type: new_type });
      await handleTypeChange(new_type);
    }
  }

  // 数据模型类型切换
  const handleTypeChange = async (value) => {
    console.log(`type selected ${value}`);

    if (!value) {
      resetModelConfSchema([]);
      resetModelConfFields();
      return;
    }

    // 加载该类型的配置schema
    let schema = modelConfSchemaMap.value[value];
    if (!schema) {
      schema = await loadModelConfig(value);
    }

    if (schema && schema.length > 0) {
      // 重置模型配置表单schema
      await resetModelConfSchema(schema);
      await resetModelConfFields();

      // 提取 schema 中的默认值并设置到表单
      const defaultValues: Record<string, any> = {};
      schema.forEach((item: any) => {
        if (item.defaultValue !== undefined) {
          defaultValues[item.field] = item.defaultValue;
        }
      });
      if (Object.keys(defaultValues).length > 0) {
        await setModelConfFieldsValue(defaultValues);
      }
    } else {
      // 如果schema为空，重置为空数组
      await resetModelConfSchema([]);
      await resetModelConfFields();
    }
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
