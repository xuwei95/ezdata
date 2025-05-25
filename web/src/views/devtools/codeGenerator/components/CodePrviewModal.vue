<template>
  <BasicModal v-bind="$attrs" @register="registerModal" destroyOnClose defaultFullscreen :title="title" :width="'800px'" @ok="handleSubmit">
    <a-row>
      <a-col :span="6" style="flex: 1">
        <BasicTree ref="treeRef" v-if="codeTree.length" showLine defaultExpandAll :treeData="codeTree" @select="handleSelect" />
      </a-col>
      <a-col :span="18" style="flex: 1">
        <MonacoEditor v-model:value="clickNode.content" :language="clickNode.language" :hightChange="true" style="min-height: 600px; height: 100%" />
      </a-col>
    </a-row>
    <template #insertFooter>
      <a-button type="primary" @click="exportSingle">导出当前文件</a-button>
    </template>
  </BasicModal>
</template>

<script lang="ts" setup>
  import { ref, unref } from 'vue';
  import { BasicModal, useModalInner } from '/@/components/Modal';
  import { BasicTree } from '/@/components/Tree';
  import { generateCode, exportCodeUrl } from '../CodeGenerator.api';
  import { useMessage } from '/@/hooks/web/useMessage';
  import { MonacoEditor } from '/@/components/Form';
  import { defHttp } from "/@/utils/http/axios";
  // Emits声明
  const emit = defineEmits(['register', 'success']);
  const codeTree = ref<any[]>([]);
  const clickNode = ref<object>({});
  const { createMessage } = useMessage();
  //表单赋值
  const [registerModal, { setModalProps, closeModal }] = useModalInner(async (data) => {
    setModalProps({ confirmLoading: false, showCancelBtn: !!data?.showFooter, showOkBtn: !!data?.showFooter });
    try {
      const res_data = await generateCode({ id: data.record.id });
      if (res_data) {
        codeTree.value = res_data;
      } else {
        console.log('error', res_data);
      }
    } catch (error) {
      console.log('error', error);
    }
  });
  //设置标题
  const title = '代码预览';
  function handleSelect(checkedKeys, e) {
    console.log('onSelect', checkedKeys, e);
    if (e.node.type == 'file') {
      clickNode.value = e.node;
      console.log(clickNode.value);
    } else {
      console.log(e);
    }
  }
  //单个导出事件
  async function exportSingle(v) {
    const params = { data: { key: clickNode.value.key, content: clickNode.value.content }, type: 'file' };
    if (!params.data.content) {
      createMessage.warning('当前文件为空！');
      return;
    }
    const data = await defHttp.post({ url: exportCodeUrl, params: params, responseType: 'blob' }, { isTransformResponse: false });
    if (!data) {
      createMessage.warning('文件下载失败');
      return;
    }
    let url = window.URL.createObjectURL(new Blob([data]));
    let link = document.createElement('a');
    link.style.display = 'none';
    link.href = url;
    link.setAttribute('download', clickNode.value.key);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link); //下载完成移除元素
    window.URL.revokeObjectURL(url); //释放掉blob对象
    createMessage.success('导出成功！');
  }
  // 表单提交事件
  async function handleSubmit(v) {
    try {
      setModalProps({ confirmLoading: true });
      //提交表单
      const params = { data: codeTree.value, type: 'zip' };
      const data = await defHttp.post({ url: exportCodeUrl, params: params, responseType: 'blob' }, { isTransformResponse: false });
      if (!data) {
        createMessage.warning('文件下载失败');
        return;
      }
      let url = window.URL.createObjectURL(new Blob([data]));
      let link = document.createElement('a');
      link.style.display = 'none';
      link.href = url;
      link.setAttribute('download', codeTree.value[0].key + '.zip');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link); //下载完成移除元素
      window.URL.revokeObjectURL(url); //释放掉blob对象
      createMessage.success('导出成功！');
      //关闭弹窗
      closeModal();
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
