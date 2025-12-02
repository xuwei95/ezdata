<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose showFooter :title="title" :width="'1000px'" @ok="handleSubmit">
    <BasicForm @register="registerForm">
      <template #type="{ model, field }">
        <a-select
          v-model:value="model[field]"
          style="width: 100%"
          placeholder="请选择数据源类型"
          :options="dataSourceTypeOptions"
          @change="handleTypeChange"
          :disabled="typeDisabled"
          show-search
          :filter-option="(input, option) => {
            return option.label.toLowerCase().indexOf(input.toLowerCase()) >= 0;
          }"
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
  const formLoading = ref(false);
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
      if (res && Array.isArray(res) && res.length > 0) {
        // 转换后端配置格式为前端表单schema格式
        const schema = convertToFormSchema(res);
        connFormSchemaMap.value[type] = schema;
        return schema;
      } else {
        console.warn(`数据源类型 ${type} 的配置为空`);
        // 清空该类型的缓存
        connFormSchemaMap.value[type] = [];
        return [];
      }
    } catch (error) {
      console.error('获取数据源配置失败:', error);
      createMessage.error(`获取数据源配置失败: ${error?.message || '未知错误'}`);
      // 清空该类型的缓存，确保不会使用旧数据
      connFormSchemaMap.value[type] = [];
      return [];
    }
  };

  // 转换后端配置格式为前端FormSchema格式
  const convertToFormSchema = (config: any[]) => {
    if (!config || !Array.isArray(config)) {
      console.error('Invalid config:', config);
      return [];
    }

    // 先转换所有字段
    const schemas = config.map(item => {
      // 获取原始组件类型
      const componentType = item.type || item.component || 'Input';

      const schema: any = {
        label: item.label || item.field || '',
        field: item.field || '',
        required: item.required || false,
        component: convertComponentType(componentType),
      };

      // 初始化 componentProps
      schema.componentProps = {};

      // 如果是 boolean/bool 类型且使用 RadioGroup，先添加默认选项
      if ((componentType === 'boolean' || componentType === 'bool') && schema.component === 'RadioGroup') {
        schema.componentProps.options = [
          { label: '是', value: true },
          { label: '否', value: false },
        ];
        // 确保 bool 类型有默认值，如果没有指定则默认为 false
        if (item.default !== undefined && item.default !== null) {
          schema.defaultValue = item.default;
          // 确保默认值是布尔类型
          if (typeof schema.defaultValue !== 'boolean') {
            schema.defaultValue = schema.defaultValue === 'true' || schema.defaultValue === 1 || schema.defaultValue === '1' || schema.defaultValue === true;
          }
        } else {
          // 如果没有指定默认值，设置为 false
          schema.defaultValue = false;
        }
      } else {
        // 处理其他类型的默认值
        if (item.default !== undefined && item.default !== null) {
          schema.defaultValue = item.default;
        }
      }

      // 处理 description - 作为帮助提示
      if (item.description) {
        schema.helpMessage = item.description;
      }

      // 处理 placeholder - 优先使用 example，其次使用 description
      if (item.placeholder !== undefined) {
        schema.componentProps.placeholder = item.placeholder;
      } else if (item.description && !item.example) {
        schema.componentProps.placeholder = item.description;
      }

      // 合并后端传递的 componentProps（不覆盖已设置的 options）
      if (item.componentProps && typeof item.componentProps === 'object') {
        schema.componentProps = {
          ...schema.componentProps,
          ...item.componentProps,
          // 如果是 RadioGroup 且我们已经设置了 options，不要被后端覆盖（除非后端明确提供了 options）
          ...(schema.component === 'RadioGroup' && schema.componentProps.options && !item.componentProps.options
            ? { options: schema.componentProps.options }
            : {})
        };
      }

      // 处理 min/max
      if (item.min !== undefined) {
        schema.componentProps.min = item.min;
      }
      if (item.max !== undefined) {
        schema.componentProps.max = item.max;
      }

      return schema;
    });

    // 排序：必填参数在前，非必填参数在后
    const requiredSchemas = schemas.filter(s => s.required);
    const optionalSchemas = schemas.filter(s => !s.required);

    return [...requiredSchemas, ...optionalSchemas];
  };

  // 转换组件类型
  const convertComponentType = (component: string) => {
    const componentMap = {
      'Input': 'Input',
      'string': 'Input',
      'Number': 'InputNumber',
      'number': 'InputNumber',
      'InputNumber': 'InputNumber',
      'Password': 'InputPassword',
      'password': 'InputPassword',
      'Select': 'JSelectInput',
      'Radio': 'RadioGroup',
      'RadioGroup': 'RadioGroup',
      'boolean': 'RadioGroup',
      'bool': 'RadioGroup',
      'Switch': 'Switch',
      'JSONEditor': 'MonacoEditor',
      'MonacoEditor': 'MonacoEditor',
      'JDictSelectTag': 'JDictSelectTag',
      'JCheckbox': 'JCheckbox',
      'JSelectInput': 'JSelectInput',
      'Textarea': 'InputTextArea'
    };
    return componentMap[component] || 'Input';
  };
  //表单配置
  const [registerForm, { setProps, getFieldsValue, resetFields, setFieldsValue, validate }] = useForm({
    labelWidth: 240,
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
    labelWidth: 240,
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
        await resetConnSchema(schema);
        await resetConnFields();

        // 先提取默认值
        const defaultValues: Record<string, any> = {};
        schema.forEach((item: any) => {
          if (item.defaultValue !== undefined) {
            defaultValues[item.field] = item.defaultValue;
          }
        });

        // 合并默认值和表单数据，只有当 conn_conf 中有明确的值时才覆盖默认值
        const finalValues = { ...defaultValues };
        if (formData.conn_conf && typeof formData.conn_conf === 'object') {
          Object.keys(formData.conn_conf).forEach(key => {
            if (formData.conn_conf[key] !== undefined && formData.conn_conf[key] !== null) {
              finalValues[key] = formData.conn_conf[key];
            }
          });
        }

        // 连接配置表单赋值
        await setConnFieldsValue(finalValues);
      } else {
        // 如果schema为空，重置为空数组，避免表单显示错误
        await resetConnSchema([]);
        await resetConnFields();
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
      // 设置主表单的默认类型
      setFieldsValue({
        type: defaultType,
      });
      
      let schema = connFormSchemaMap.value[defaultType];
      if (!schema) {
        schema = await loadDataSourceConfig(defaultType);
      }
      if (schema && schema.length > 0) {
        await resetConnSchema(schema);
        await resetConnFields();

        // 提取 schema 中的默认值并设置到表单
        const defaultValues: Record<string, any> = {};
        schema.forEach((item: any) => {
          if (item.defaultValue !== undefined) {
            defaultValues[item.field] = item.defaultValue;
          }
        });
        // 设置默认值到表单（即使默认值为 false 也要设置）
        await setConnFieldsValue(defaultValues);
      } else {
        // 如果默认配置加载失败，重置为空数组
        await resetConnSchema([]);
        await resetConnFields();
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

    // 立即清空表单，避免旧数据残留
    await resetConnSchema([]);
    await resetConnFields();

    if (!value) {
      return;
    }

    // 设置表单加载状态
    formLoading.value = true;
    setConnProps({ loading: true });

    try {
      // 加载该类型的配置schema
      let schema = connFormSchemaMap.value[value];
      if (!schema) {
        schema = await loadDataSourceConfig(value);
      }

      if (schema && schema.length > 0) {
        // 重置连接配置表单schema
        await resetConnSchema(schema);
        await resetConnFields();

        // 提取 schema 中的默认值并设置到表单
        const defaultValues: Record<string, any> = {};
        schema.forEach((item: any) => {
          if (item.defaultValue !== undefined) {
            defaultValues[item.field] = item.defaultValue;
          }
        });
        // 设置默认值到表单（即使默认值为 false 也要设置）
        await setConnFieldsValue(defaultValues);
      } else {
        // 如果schema为空，确保表单被清空
        await resetConnSchema([]);
        await resetConnFields();
        createMessage.warning(`数据源类型 ${value} 的配置加载失败`);
      }
    } catch (error) {
      // 发生错误时，确保表单被清空
      await resetConnSchema([]);
      await resetConnFields();
      console.error('切换数据源类型失败:', error);
      createMessage.error('切换数据源类型失败，请重试');
    } finally {
      // 清除加载状态
      formLoading.value = false;
      setConnProps({ loading: false });
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
