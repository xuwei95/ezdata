<!--用户选择组件-->
<template>
  <div>
    <JSelectBiz @change="handleChange" @handleOpen="handleOpen" :loading="loadingEcho" v-bind="attrs"></JSelectBiz>
    <UserSelectModal :rowKey="rowKey" @register="regModal" @getSelectResult="setValue" v-bind="getBindValue" :excludeUserIdList="excludeUserIdList"></UserSelectModal>
  </div>
</template>
<script lang="ts">
  import { unref } from 'vue';
  import UserSelectModal from './modal/UserSelectModal.vue';
  import JSelectBiz from './base/JSelectBiz.vue';
  import { defineComponent, ref, reactive, watchEffect, watch, provide } from 'vue';
  import { useModal } from '/@/components/Modal';
  import { propTypes } from '/@/utils/propTypes';
  import { useRuleFormItem } from '/@/hooks/component/useFormItem';
  import { useAttrs } from '/@/hooks/core/useAttrs';
  import { SelectValue } from 'ant-design-vue/es/select';

  export default defineComponent({
    name: 'JSelectUser',
    components: {
      UserSelectModal,
      JSelectBiz,
    },
    inheritAttrs: false,
    props: {
      value: propTypes.oneOfType([propTypes.string, propTypes.array]),
      labelKey: {
        type: String,
        default: 'realname',
      },
      rowKey: {
        type: String,
        default: 'username',
      },
      params: {
        type: Object,
        default: () => {},
      },
      //update-begin---author:wangshuai ---date:20230703  for：【QQYUN-5685】5、离职人员可以选自己------------
      //排除用户id的集合
      excludeUserIdList:{
        type: Array,
        default: () => [],
      }
      //update-end---author:wangshuai ---date:20230703  for：【QQYUN-5685】5、离职人员可以选自己------------
    },
    emits: ['options-change', 'change', 'update:value'],
    setup(props, { emit }) {
      const emitData = ref<any[]>();
      //注册model
      const [regModal, { openModal }] = useModal();
      //表单值
      const [state] = useRuleFormItem(props, 'value', 'change', emitData);
      //下拉框选项值
      const selectOptions = ref<SelectValue>([]);
      //下拉框选中值
      let selectValues = reactive<Recordable>({
        value: [],
        change: false,
      });
      // 是否正在加载回显数据
      const loadingEcho = ref<boolean>(false);
      //下发 selectOptions,xxxBiz组件接收
      provide('selectOptions', selectOptions);
      //下发 selectValues,xxxBiz组件接收
      provide('selectValues', selectValues);
      //下发 loadingEcho,xxxBiz组件接收
      provide('loadingEcho', loadingEcho);

      const tag = ref(false);
      const attrs = useAttrs();

      /**
       * 监听组件值
       */
      watchEffect(() => {
        props.value && initValue();
        // 查询条件重置的时候 界面显示未清空
        if (!props.value) {
          selectValues.value = [];
        }
      });

      /**
       * 监听selectValues变化
       */
      watch(selectValues, () => {
        if (selectValues) {
          state.value = selectValues.value;
        }
      });

      //update-begin---author:wangshuai ---date:20230703  for：【QQYUN-5685】5、离职人员可以选自己------------
      const excludeUserIdList = ref<any>([]);
      
      /**
       * 需要监听一下excludeUserIdList，否则modal获取不到
       */ 
      watch(()=>props.excludeUserIdList,(data)=>{
        excludeUserIdList.value = data;
      },{ immediate: true })
      //update-end---author:wangshuai ---date:20230703  for：【QQYUN-5685】5、离职人员可以选自己------------
      
      /**
       * 打卡弹出框
       */
      function handleOpen() {
        tag.value = true;
        openModal(true, {
          isUpdate: false,
        });
      }

      /**
       * 将字符串值转化为数组
       */
      function initValue() {
        let value = props.value ? props.value : [];
        if (value && typeof value === 'string' && value != 'null' && value != 'undefined') {
          state.value = value.split(',');
          selectValues.value = value.split(',');
        } else {
          // 【VUEN-857】兼容数组（行编辑的用法问题）
          selectValues.value = value;
        }
      }

      /**
       * 设置下拉框的值
       */
      function setValue(options, values) {
        selectOptions.value = options;
        //emitData.value = values.join(",");
        state.value = values;
        selectValues.value = values;
        emit('update:value', values.join(','));
      }
      const getBindValue = Object.assign({}, unref(props), unref(attrs));

      //update-begin---author:wangshuai ---date:20230711  for：换成异步组件加载，否则会影响到其他页面描述------------
      /**
       * 下拉框值改变回调事件
       * @param values
       */
      function handleChange(values) {
        emit('update:value', values);
      }
      //update-end---author:wangshuai ---date:20230711  for：换成异步组件加载，否则会影响到其他页面描述------------
      
      return {
        state,
        attrs,
        selectOptions,
        getBindValue,
        selectValues,
        loadingEcho,
        tag,
        regModal,
        setValue,
        handleOpen,
        excludeUserIdList,
        handleChange,
      };
    },
  });
</script>
<style lang="less" scoped>
  .j-select-row {
    @width: 82px;

    .left {
      width: calc(100% - @width - 8px);
    }

    .right {
      width: @width;
    }

    .full {
      width: 100%;
    }

    :deep(.ant-select-search__field) {
      display: none !important;
    }
  }
</style>
