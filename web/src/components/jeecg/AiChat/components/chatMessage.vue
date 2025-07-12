<template>
  <div class="chat" :class="[inversion ? 'self' : 'chatgpt']">
    <div class="avatar">
      <img v-if="inversion" :src="avatar()" />
      <svg v-else xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" aria-hidden="true" width="1em" height="1em">
        <path
          d="M29.71,13.09A8.09,8.09,0,0,0,20.34,2.68a8.08,8.08,0,0,0-13.7,2.9A8.08,8.08,0,0,0,2.3,18.9,8,8,0,0,0,3,25.45a8.08,8.08,0,0,0,8.69,3.87,8,8,0,0,0,6,2.68,8.09,8.09,0,0,0,7.7-5.61,8,8,0,0,0,5.33-3.86A8.09,8.09,0,0,0,29.71,13.09Zm-12,16.82a6,6,0,0,1-3.84-1.39l.19-.11,6.37-3.68a1,1,0,0,0,.53-.91v-9l2.69,1.56a.08.08,0,0,1,.05.07v7.44A6,6,0,0,1,17.68,29.91ZM4.8,24.41a6,6,0,0,1-.71-4l.19.11,6.37,3.68a1,1,0,0,0,1,0l7.79-4.49V22.8a.09.09,0,0,1,0,.08L13,26.6A6,6,0,0,1,4.8,24.41ZM3.12,10.53A6,6,0,0,1,6.28,7.9v7.57a1,1,0,0,0,.51.9l7.75,4.47L11.85,22.4a.14.14,0,0,1-.09,0L5.32,18.68a6,6,0,0,1-2.2-8.18Zm22.13,5.14-7.78-4.52L20.16,9.6a.08.08,0,0,1,.09,0l6.44,3.72a6,6,0,0,1-.9,10.81V16.56A1.06,1.06,0,0,0,25.25,15.67Zm2.68-4-.19-.12-6.36-3.7a1,1,0,0,0-1.05,0l-7.78,4.49V9.2a.09.09,0,0,1,0-.09L19,5.4a6,6,0,0,1,8.91,6.21ZM11.08,17.15,8.38,15.6a.14.14,0,0,1-.05-.08V8.1a6,6,0,0,1,9.84-4.61L18,3.6,11.61,7.28a1,1,0,0,0-.53.91ZM12.54,14,16,12l3.47,2v4L16,20l-3.47-2Z"
          fill="currentColor"
        />
      </svg>
    </div>
    <div class="content">
      <p class="date">{{ dateTime }}</p>
      <div class="msgArea">
        <div v-if="chat_flow && chat_flow.length > 0">
          <a-dropdown trigger="click">
            <a-button type="primary" @click="showCollapse(chat_flow.length - 1)">
              <span v-if="loading">
                <a-icon type="loading-outlined" :spin="true" />
              </span>
              {{ chat_flow[chat_flow.length - 1].title }}
              <a-icon type="down" />
            </a-button>
          </a-dropdown>
          <a-collapse v-model:activeKey="activeKeys" v-if="showCollapsePanel">
            <a-collapse-panel v-for="(item, index) in chat_flow" :key="index" :header="item.time + '  ' + item.title" :panelKey="index.toString()">
              <chatText :text="item.content"></chatText>
            </a-collapse-panel>
          </a-collapse>
        </div>
        <chatText :text="text" :inversion="inversion" :error="error" :loading="loading"></chatText>
        <div v-if="showTable" style="width: 100%">
          <JVxeTable ref="tableRef" toolbar resizable maxHeight="400" :toolbarConfig="{ btn: [] }" :columns="columns" :dataSource="dataSource">
            <template #toolbarSuffix>
              <a-button @click="outputData" style="float: right" preIcon="ant-design:export-outlined">导出数据</a-button>
            </template>
          </JVxeTable>
        </div>
        <div class="html-body" v-if="htmlText !== ''" style="width: 800px">
          <a-button @click="outputChart" style="float: right" preIcon="ant-design:export-outlined">导出图表</a-button>
          <iframe :srcdoc="htmlText" width="100%" height="100%"></iframe>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { defineExpose, onMounted, ref } from 'vue';
  import chatText from './chatText.vue';
  import defaultAvatar from '../assets/avatar.jpg';
  import { useUserStore } from '/@/store/modules/user';
  const props = defineProps(['dateTime', 'text', 'table_data', 'html_data', 'chat_flow', 'inversion', 'error', 'loading']);
  const { userInfo } = useUserStore();
  const avatar = () => {
    return userInfo?.avatar || defaultAvatar;
  };
  import { JVxeTypes, JVxeColumn, JVxeTableInstance } from '/@/components/jeecg/JVxeTable/types';
  import { useMethods } from '@/hooks/system/useMethods';
  // 数据表格相关配置
  const tableRef = ref<JVxeTableInstance>();
  const showTable = ref(false);
  const columns = ref<JVxeColumn[]>([]); // 字段列表
  const dataSource = ref<any[]>([]); // 数据列表
  // html渲染相关配置
  const htmlText = ref('');
  // 流程展示
  const activeKeys = ref([]);
  const showCollapsePanel = ref(false);
  const showCollapse = (index) => {
    showCollapsePanel.value = !showCollapsePanel.value;
    console.log(22222, index);
    activeKeys.value = [index.toString()];
  };
  // 数据表格 导出excel
  const { handleExportExcel } = useMethods();
  async function outputData() {
    console.log(dataSource.value);
    handleExportExcel('数据导出_' + Date.now() + '.xlsx', dataSource.value);
  }
  function handleTableData() {
    const data_li = props.table_data;
    if (data_li && data_li.length > 0) {
      columns.value = [];
      const fields = Object.keys(data_li[0]);
      console.log(fields);
      for (let i in fields) {
        const field_key = fields[i];
        columns.value.push({
          title: field_key,
          key: field_key,
          type: JVxeTypes.normal,
          width: 200,
        });
      }
      dataSource.value = data_li;
      showTable.value = true;
    }
  }
  // 渲染html图表
  function handleHtmlData() {
    const html_text = props.html_data;
    if (html_text && html_text !== '') {
      htmlText.value = html_text;
    }
  }
  // 渲染表格或html
  function handleData() {
    handleTableData();
    handleHtmlData();
  }
  async function outputChart() {
    const output_name = '图表导出_' + Date.now() + '.html';
    const data = new Blob([htmlText.value], { type: 'text/html' });
    const url = URL.createObjectURL(data);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', output_name);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  onMounted(() => {
    handleData();
  });
  defineExpose({
    handleData,
  });
</script>

<style lang="less" scoped>
  .chat {
    display: flex;
    margin-bottom: 1.5rem;
    &.self {
      flex-direction: row-reverse;
      .avatar {
        margin-right: 0;
        margin-left: 10px;
      }
      .msgArea {
        flex-direction: row-reverse;
      }
      .date {
        text-align: right;
      }
    }
  }
  .avatar {
    flex: none;
    margin-right: 10px;
    img {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      overflow: hidden;
    }
    svg {
      font-size: 28px;
    }
  }
  .content {
    .date {
      color: #b4bbc4;
      font-size: 0.75rem;
      margin-bottom: 10px;
    }
    .msgArea {
      //display: flex;
    }
  }
  .html-body {
    height: 500px;
    overflow: scroll;
  }
</style>
