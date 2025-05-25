modal_type_map = {1: 'Modal', 2: 'Drawer'}


def gen_modal_code(params):
    '''
    生成编辑弹窗代码
    :param params:
    :return:
    '''
    base_code = """
<template>
  <Basic${modal_type} v-bind="$attrs" @register="register${modal_type}" destroyOnClose showFooter :title="title" :width="'${modal_width}'" @ok="handleSubmit">
    <BasicForm @register="registerForm" />
  </Basic${modal_type}>
</template>

<script lang="ts" setup>
  import { ref, computed, unref, reactive } from 'vue';
  import { Basic${modal_type}, use${modal_type}Inner } from '/@/components/${modal_type}';
  import { BasicForm, useForm } from '/@/components/Form/index';
  import { formSchema } from '../${module_name}.data';
  import { getInfoById, saveOrUpdate } from '../${module_name}.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const isUpdate = ref(true);
  const { createMessage } = useMessage();
  //表单配置
  const [registerForm, { setProps, resetFields, setFieldsValue, validate }] = useForm({
    //labelWidth: 150,
    schemas: formSchema,
    showActionButtonGroup: false,
    baseColProps: { span: ${baseColSpan} },
  });
  //表单赋值
  const [register${modal_type}, { set${modal_type}Props, close${modal_type} }] = use${modal_type}Inner(async (data) => {
    //重置表单
    await resetFields();
    set${modal_type}Props({ confirmLoading: false, showCancelBtn: !!data?.showFooter, showOkBtn: !!data?.showFooter });
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
      set${modal_type}Props({ confirmLoading: true });
      //提交表单
      await saveOrUpdate(values, isUpdate.value);
      //关闭弹窗
      close${modal_type}();
      //刷新列表
      emit('success');
    } finally {
      set${modal_type}Props({ confirmLoading: false });
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
        """
    module_name = params.get('module_name')
    form_style = params.get('form_style', 1)
    baseColSpan = str(int(24 / form_style))
    modal_type = params['modal_type']
    modal_type = modal_type_map.get(modal_type)
    modal_width = params.get('modal_width')
    modal_width = f"{modal_width}px" if modal_width != 0 else '100%'
    res_code = base_code.replace('${modal_type}', modal_type)
    res_code = res_code.replace('${baseColSpan}', baseColSpan)
    res_code = res_code.replace('${modal_width}', modal_width)
    res_code = res_code.replace('${module_name}', module_name)
    res_code = res_code.strip() + '\n'
    return res_code


if __name__ == '__main__':
    from web_apps.code_generator.db_models import CodeGenModel, db
    import json
    from utils.common_utils import get_json_value

    obj = db.session.query(CodeGenModel).filter(CodeGenModel.id == '5deb88593c024033ae6de2f9ed5e7806').first()
    params = obj.to_dict()
    params['fields'] = json.loads(params['fields'])
    params['query_params'] = json.loads(params['query_params'])
    params['buttons'] = json.loads(params['buttons'])
    print(params)
    modal_code = gen_modal_code(params)
    print(modal_code)
    f = open('out/modal.vue', 'w')
    f.write(modal_code)