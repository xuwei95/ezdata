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
          show-search
          :filter-option="(input, option) => {
            return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
          }"
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
          show-search
          :filter-option="(input, option) => {
            return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
          }"
        />
      </template>
      <template #model_conf="">
        <BasicForm :key="modelConfFormKey" @register="registerModelConfForm" />
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
  const modelConfFormKey = ref(0); // 用于强制重新渲染模型配置表单
  const { createMessage } = useMessage();
  //表单配置
  const [registerForm, { setProps, resetFields, setFieldsValue, getFieldsValue, validate }] = useForm({
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

        // 合并默认值和表单数据，只有当 model_conf 中有明确的值时才覆盖默认值
        const finalValues = { ...defaultValues };
        if (formData.model_conf && typeof formData.model_conf === 'object') {
          Object.keys(formData.model_conf).forEach(key => {
            if (formData.model_conf[key] !== undefined && formData.model_conf[key] !== null) {
              finalValues[key] = formData.model_conf[key];
            }
          });
        }

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
    } catch (error: any) {
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
      console.log(`开始加载模型配置: ${model_type}`, datasourceTypeMap.value);

      // 获取当前选择的数据源ID和类型
      const formData = await getFieldsValue();
      const datasourceId = formData?.datasource_id;
      const datasourceType = datasourceId ? datasourceTypeMap.value[datasourceId] : null;

      if (!datasourceType) {
        console.warn(`数据源ID ${datasourceId} 的类型未找到`);
        createMessage.warning(`无法获取数据源类型，请先选择数据源`);
        return [];
      }

      console.log(`数据源ID: ${datasourceId}, 数据源类型: ${datasourceType}`);
      const modelKey = `${datasourceType}:${model_type}`;
      console.log(`模型key: ${modelKey}`);
      const res = await getModelConfig(modelKey);
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
    } catch (error: any) {
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
      // 获取原始组件类型
      const componentType = item.type || item.component || 'Input';

      const schema: any = {
        label: item.label || '',
        field: item.field || '',
        required: item.required || false,
        component: convertComponentType(componentType),
      };

      // 初始化 componentProps
      schema.componentProps = {};
      // 处理默认值
      if (item.default !== undefined && item.default !== null) {
        schema.defaultValue = item.default;
      }
      
      
      // 合并后端传递的 componentProps
      if (item.componentProps && typeof item.componentProps === 'object') {
        schema.componentProps = { ...schema.componentProps, ...item.componentProps };
      }
      // 处理 min/max
      if (item.min !== undefined) {
        schema.componentProps.min = item.min;
      }
      if (item.max !== undefined) {
        schema.componentProps.max = item.max;
      }

      // 处理 MonacoEditor 特殊逻辑
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
      // 验证 schema 完整性
      if (!schema.field) {
        console.error('[Convert Schema] Invalid schema: missing field', item);
        return null;
      }
      if (!schema.component) {
        console.error('[Convert Schema] Invalid schema: missing component', schema);
        return null;
      }

      // 确保 componentProps 始终是一个对象
      if (!schema.componentProps || typeof schema.componentProps !== 'object') {
        schema.componentProps = {};
      }

      console.log('Converted schema:', schema);
      return schema;
    }).filter(s => s !== null); // 过滤掉无效的 schema
  };

  // 转换组件类型
  const convertComponentType = (component: string) => {
    const componentMap = {
      'Input': 'Input',
      'Number': 'InputNumber',
      'InputNumber': 'InputNumber',
      'Password': 'InputPassword',
      'Select': 'JSelectInput',
      'RadioGroup': 'RadioGroup',
      'boolean': 'RadioGroup',
      'bool': 'RadioGroup',
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
    console.log(`[Model Type Change] selected ${value}`);

    if (!value) {
      console.log('[Model Type Change] value is empty, clearing form');
      try {
        modelConfFormKey.value++; // 强制重新渲染
        await clearModelConfValidate();
        await resetModelConfSchema([]);
        await resetModelConfFields();
      } catch (error) {
        console.error('[Model Type Change] Error clearing form:', error);
      }
      return;
    }

    try {
      // 强制重新渲染表单组件，避免组件复用导致的状态问题
      modelConfFormKey.value++;

      // 清空旧表单
      console.log('[Model Type Change] Clearing old form data');
      // 先清除验证，避免卸载时的验证错误
      await clearModelConfValidate();
      await resetModelConfSchema([]);
      await resetModelConfFields();

      // 等待 Vue 完成清理，使用 nextTick 确保响应式更新完成
      await new Promise(resolve => setTimeout(resolve, 50));

      // 加载该类型的配置schema
      console.log('[Model Type Change] Loading config for:', value);
      let schema = modelConfSchemaMap.value[value];
      if (!schema) {
        console.log('[Model Type Change] Schema not cached, fetching from backend');
        schema = await loadModelConfig(value);
      } else {
        console.log('[Model Type Change] Using cached schema');
      }

      if (schema && schema.length > 0) {
        console.log(`[Model Type Change] Loaded ${schema.length} fields`);

        // 验证 schema 完整性
        const validSchema = schema.filter(item => item && item.field && item.component);
        if (validSchema.length !== schema.length) {
          console.warn('[Model Type Change] Some schema items are invalid', schema);
        }

        // 重置模型配置表单schema
        await resetModelConfSchema(validSchema);

        // 等待 Vue 完成渲染
        await new Promise(resolve => setTimeout(resolve, 50));

        await resetModelConfFields();

        // 提取 schema 中的默认值并设置到表单
        const defaultValues: Record<string, any> = {};
        validSchema.forEach((item: any) => {
          if (item.defaultValue !== undefined) {
            defaultValues[item.field] = item.defaultValue;
          }
        });
        console.log('[Model Type Change] Setting default values:', defaultValues);

        // 设置默认值到表单（即使默认值为 false 也要设置）
        await setModelConfFieldsValue(defaultValues);
        console.log('[Model Type Change] Form initialized successfully');
      } else {
        // 如果schema为空，重置为空数组
        console.warn('[Model Type Change] Schema is empty');
        await clearModelConfValidate();
        await resetModelConfSchema([]);
        await resetModelConfFields();
      }
    } catch (error) {
      console.error('[Model Type Change] Error occurred:', error);
      try {
        await clearModelConfValidate();
        await resetModelConfSchema([]);
        await resetModelConfFields();
      } catch (resetError) {
        console.error('[Model Type Change] Error resetting form:', resetError);
      }
      createMessage.error(`切换模型类型失败: ${error?.message || '未知错误'}`);
    }
  };
  // 查询数据源列表
  async function fetchDataSources() {
    let data_li = await allSourceList({});
    datasourceOptions.value = [];
    datasourceTypeMap.value = {};
    for (let i = 0; i < data_li.length; i++) {
      datasourceOptions.value.push({ label: data_li[i].name, value: data_li[i].id });
      datasourceTypeMap.value[data_li[i].id] = data_li[i].type;
    }
  }
  //表单提交事件
  async function handleSubmit() {
    try {
      let values = await validate();
      // 设置连接配置
      let v = await getModelConfFieldsValue();
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
