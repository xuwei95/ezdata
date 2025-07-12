<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose defaultFullscreen :title="title" :width="'800px'" @ok="handleSubmit">
    <BasicForm @register="registerForm" />
    <a-tabs :activeKey="activeKey" center @tabClick="handleChangePanel">
      <a-tab-pane tab="字段列表" key="fields" forceRender>
        <JVxeTable
          ref="FieldsTableRef"
          toolbar
          dragSort
          sortKey="sortNum"
          :sortBegin="3"
          rowSelection
          :maxHeight="580"
          :columns="FieldsEditColumns"
          :dataSource="fields"
        >
          <template #toolbarSuffix>
            <a-button @click="onGetData1">获取数据</a-button>
          </template>
        </JVxeTable>
      </a-tab-pane>
      <a-tab-pane tab="查询参数" key="query_params" forceRender>
        <JVxeTable
          ref="QueryParamsTableRef"
          toolbar
          dragSort
          sortKey="sortNum"
          :sortBegin="3"
          rowSelection
          :maxHeight="580"
          :columns="QueryParamsEditColumns"
          :dataSource="query_params"
        >
          <template #toolbarSuffix>
            <a-button @click="onGetData2">获取数据</a-button>
          </template>
        </JVxeTable>
      </a-tab-pane>
      <a-tab-pane tab="按钮设置" key="buttons" forceRender>
        <JVxeTable
          ref="ButtonsTableRef"
          toolbar
          dragSort
          sortKey="sortNum"
          :sortBegin="3"
          rowSelection
          :maxHeight="580"
          :columns="ButtonsEditColumns"
          :dataSource="buttons"
        >
          <template #toolbarSuffix>
            <a-button @click="onGetData3">获取数据</a-button>
          </template>
        </JVxeTable>
      </a-tab-pane>
    </a-tabs>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, computed, unref, reactive } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, useForm } from '/@/components/Form/index';
  import { formSchema, FieldsEditColumns, ButtonsEditColumns, QueryParamsEditColumns, defaultFields, defaultButtons } from '../CodeGenerator.data';
  import { getInfoById, saveOrUpdate } from '../CodeGenerator.api';
  import { JVxeTableInstance } from '/@/components/jeecg/JVxeTable/types';
  import { useMessage } from '/@/hooks/web/useMessage';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const isUpdate = ref(true);
  const activeKey = ref('fields');
  const FieldsTableRef = ref<JVxeTableInstance>();
  const fields = ref<any[]>([]);
  const query_params = ref<any[]>([]);
  const buttons = ref<any[]>([]);
  const ButtonsTableRef = ref<JVxeTableInstance>();
  const QueryParamsTableRef = ref<JVxeTableInstance>();
  const { createMessage } = useMessage();
  //表单配置
  const [registerForm, { setProps, resetFields, setFieldsValue, validate }] = useForm({
    //labelWidth: 150,
    schemas: formSchema,
    showActionButtonGroup: false,
    baseColProps: { span: 8 },
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
          let data = res_data;
          formData = data;
          // 设置字段, 查询参数，按钮参数
          fields.value = data.fields;
          query_params.value = data.query_params;
          buttons.value = data.buttons;
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
    } else {
      // 新增：初始化字段, 查询参数，按钮参数
      fields.value = defaultFields;
      query_params.value = [];
      buttons.value = defaultButtons;
    }
    // 隐藏底部时禁用整个表单
    setProps({ disabled: !data?.showFooter });
  });
  //设置标题
  const title = computed(() => (!unref(isUpdate) ? '新增' : '编辑'));
  //tab切换事件
  function handleChangePanel(key) {
    console.log('tab', key);
    activeKey.value = key;
  }
  function onGetData1() {
    createMessage.info('请看控制台');
    console.log(FieldsTableRef.value!.getTableData());
  }
  function onGetData2() {
    createMessage.info('请看控制台');
    console.log(QueryParamsTableRef.value!.getTableData());
  }
  function onGetData3() {
    createMessage.info('请看控制台');
    console.log(ButtonsTableRef.value!.getTableData());
  }
  //表单提交事件
  async function handleSubmit(v) {
    try {
      let values = await validate();
      console.log(111111, v, values);
      console.log(234234, FieldsTableRef.value!.getTableData());
      // console.log(fields, query_params, buttons);
      // 设置字段, 查询参数，按钮参数
      if (FieldsTableRef.value) {
        values.fields = FieldsTableRef.value!.getTableData();
      }
      if (QueryParamsTableRef.value) {
        values.query_params = QueryParamsTableRef.value!.getTableData();
      }
      if (ButtonsTableRef.value) {
        values.buttons = ButtonsTableRef.value!.getTableData();
      }
      console.log(2222, values);
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
