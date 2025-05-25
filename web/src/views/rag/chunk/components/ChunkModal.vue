<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose defaultFullscreen showFooter :title="title" :width="'800px'" @ok="handleSubmit">
    <BasicForm @register="registerForm" />
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, computed, unref, reactive } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicForm, FormSchema, useForm } from "/@/components/Form/index";
  import { getInfoById, saveOrUpdate } from '../chunk.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { allList as allDataSetList } from '@/views/rag/dataset/dataset.api';
  import { allList as allDocumentList } from '@/views/rag/document/document.api';
  import { allList as allDataModelList } from '@/views/dataManage/dataModel/datamodel.api';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const isUpdate = ref(true);
  const { createMessage } = useMessage();
  const urlParams = new URLSearchParams(window.location.search);
  const defaultDocumentId = urlParams.get('document_id') || '';
  //表单数据
  const formSchema: FormSchema[] = [
    {
      label: '所属数据集',
      field: 'dataset_id',
      required: false,
      component: 'ApiSelect',
      dynamicDisabled: ({ values }) => {
        return !!values.id;
      },
      componentProps: {
        api: allDataSetList,
        params: {},
        labelField: 'name',
        valueField: 'id',
      },
      ifShow: defaultDocumentId == '',
    },
    {
      label: '所属文档',
      field: 'document_id',
      required: false,
      component: 'ApiSelect',
      defaultValue: defaultDocumentId,
      dynamicDisabled: ({ values }) => {
        return !!values.id || defaultDocumentId != '';
      },
      componentProps: {
        api: allDocumentList,
        params: {},
        labelField: 'name',
        valueField: 'id',
      },
      ifShow: defaultDocumentId != '',
    },
    {
      label: '所属数据模型',
      field: 'datamodel_id',
      required: false,
      component: 'ApiSelect',
      dynamicDisabled: ({ values }) => {
        return !!values.id;
      },
      componentProps: {
        api: allDataModelList,
        params: {},
        labelField: 'name',
        valueField: 'id',
      },
      ifShow: defaultDocumentId == '',
    },
    {
      label: '类型',
      field: 'chunk_type',
      required: true,
      component: 'RadioGroup',
      defaultValue: 'chunk',
      dynamicDisabled: ({ values }) => {
        return !!values.id;
      },
      componentProps: {
        options: [
          { label: '知识段', value: 'chunk' },
          { label: '问答对', value: 'qa' },
        ],
      },
    },
    {
      label: '问题',
      field: 'question',
      required: true,
      component: 'Input',
      ifShow: ({ values }) => values.chunk_type == 'qa',
    },
    {
      label: '回答',
      field: 'answer',
      required: true,
      component: 'JMarkdownEditor',
      ifShow: ({ values }) => values.chunk_type == 'qa',
    },
    {
      label: '内容',
      field: 'content',
      required: true,
      component: 'JMarkdownEditor',
      ifShow: ({ values }) => values.chunk_type != 'qa',
    },
    {
      label: '状态',
      field: 'status',
      required: true,
      component: 'RadioGroup',
      defaultValue: 1,
      componentProps: {
        options: [
          { label: '已同步', value: 1 },
          { label: '未同步', value: 0 },
        ],
      },
    },
    {
      label: '标记状态',
      field: 'star_flag',
      required: true,
      component: 'RadioGroup',
      defaultValue: 0,
      componentProps: {
        options: [
          { label: '已标记', value: 1 },
          { label: '未标记', value: 0 },
        ],
      },
    },
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
    }
    // 隐藏底部时禁用整个表单
    setProps({ disabled: !data?.showFooter });
  });
  //设置标题
  const title = computed(() => (!unref(isUpdate) ? '新增' : '编辑'));
  //表单提交事件
  async function handleSubmit(v) {
    try {
      let values = await validate();
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
