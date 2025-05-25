<template>
  <BasicDrawer
    v-bind="$attrs"
    @register="registerDrawer"
    :title="getTitle"
    :width="adaptiveWidth"
    @ok="handleSubmit"
    :showFooter="showFooter"
    destroyOnClose
  >
    <BasicForm @register="registerForm" />
  </BasicDrawer>
</template>
<script lang="ts" setup>
  import { defineComponent, ref, computed, unref, useAttrs } from 'vue';
  import { BasicForm, useForm } from '/@/components/Form/index';
  import { formSchema } from './user.data';
  import { BasicDrawer, useDrawerInner } from '/@/components/Drawer';
  import { saveOrUpdateUser, getUserRoles, getUserDepartList } from './user.api';
  import { useDrawerAdaptiveWidth } from '/@/hooks/jeecg/useAdaptiveWidth';
  // 声明Emits
  const emit = defineEmits(['success', 'register']);
  const attrs = useAttrs();
  const isUpdate = ref(true);
  const rowId = ref('');
  const departOptions = ref([]);
  //表单配置
  const [registerForm, { setProps, resetFields, setFieldsValue, validate, updateSchema }] = useForm({
    labelWidth: 90,
    schemas: formSchema,
    showActionButtonGroup: false,
  });
  // TODO [VUEN-527] https://www.teambition.com/task/6239beb894b358003fe93626
  const showFooter = ref(true);
  //表单赋值
  const [registerDrawer, { setDrawerProps, closeDrawer }] = useDrawerInner(async (data) => {
    await resetFields();
    showFooter.value = data?.showFooter ?? true;
    setDrawerProps({ confirmLoading: false, showFooter: showFooter.value });
    isUpdate.value = !!data?.isUpdate;
    if (unref(isUpdate)) {
      rowId.value = data.record.id;
      //租户信息定义成数组
      // if (data.record.relTenantIds && !Array.isArray(data.record.relTenantIds)) {
      //   data.record.relTenantIds = data.record.relTenantIds.split(',');
      // } else {
      //   //【issues/I56C5I】用户管理中连续点两次编辑租户配置就丢失了
      //   //data.record.relTenantIds = [];
      // }

      //查角色/赋值/try catch 处理，不然编辑有问题
      try {
        const userRoles = await getUserRoles({ user_id: data.record.id });
        if (userRoles && userRoles.length > 0) {
          data.record.selectedroles = userRoles;
        }
      } catch (error) {}

      //查所属部门/赋值/try catch 处理，不然编辑有问题
      try {
        const userDeparts = await getUserDepartList({ user_id: data.record.id });
        if (userDeparts && userDeparts.length > 0) {
          data.record.selecteddeparts = userDeparts;
        }
      } catch (error) {}
      // const userDepart = await getUserDepartList({ user_id: data.record.id });
      // if (userDepart && userDepart.length > 0) {
      //   data.record.selecteddeparts = userDepart;
      //   let selectDepartKeys = Array.from(userDepart, ({ key }) => key);
      //   data.record.selecteddeparts = selectDepartKeys.join(',');
      //   departOptions.value = userDepart.map((item) => {
      //     return { label: item.title, value: item.key };
      //   });
      // }
      // //负责部门/赋值
      // data.record.depart_id_list && !Array.isArray(data.record.depart_id_list) && (data.record.depart_id_list = data.record.depart_id_list.split(','));
      // //update-begin---author:zyf   Date:20211210  for：避免空值显示异常------------
      // data.record.depart_id_list = data.record.depart_id_list == '' ? [] : data.record.depart_id_list;
      // //update-begin---author:zyf   Date:20211210  for：避免空值显示异常------------
    }
    //处理角色用户列表情况(和角色列表有关系)
    data.selectedroles && (await setFieldsValue({ selectedroles: data.selectedroles }));
    //处理部门用户列表情况
    data.selecteddeparts && (await setFieldsValue({ selecteddeparts: data.selecteddeparts }));
    //编辑时隐藏密码/角色列表隐藏角色信息/我的部门时隐藏所属部门
    updateSchema([
      {
        field: 'password',
        show: !unref(isUpdate),
      },
      {
        field: 'confirmPassword',
        ifShow: !unref(isUpdate),
      },
      {
        field: 'selectedroles',
        show: !data.isRole,
      },
      {
        field: 'departIds',
        componentProps: { options: departOptions },
      },
      {
        field: 'selecteddeparts',
        show: !data?.departDisabled ?? false,
      },
    ]);
    // 无论新增还是编辑，都可以设置表单值
    if (typeof data.record === 'object') {
      setFieldsValue({
        ...data.record,
      });
    }
    // 隐藏底部时禁用整个表单
    //update-begin-author:taoyan date:2022-5-24 for: VUEN-1117【issue】0523周开源问题
    setProps({ disabled: !showFooter.value });
    //update-end-author:taoyan date:2022-5-24 for: VUEN-1117【issue】0523周开源问题
  });
  //获取标题
  const getTitle = computed(() => (!unref(isUpdate) ? '新增用户' : '编辑用户'));
  const { adaptiveWidth } = useDrawerAdaptiveWidth();

  //提交事件
  async function handleSubmit() {
    try {
      let values = await validate();
      setDrawerProps({ confirmLoading: true });
      // values.user_identity === 1 && (values.depart_id_list = '');
      //提交表单
      await saveOrUpdateUser(values, unref(isUpdate));
      //关闭弹窗
      closeDrawer();
      //刷新列表
      emit('success');
    } finally {
      setDrawerProps({ confirmLoading: false });
    }
  }
</script>
