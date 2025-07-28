<template>
    <div class="p-2">
      <BasicModal destroyOnClose @register="registerModal" :canFullscreen="false" width="600px" :title="title" @ok="handleOk" @cancel="handleCancel">
        <div class="flex header">
          <a-input
            @pressEnter="loadToolData"
            class="header-search"
            size="small"
            v-model:value="searchText"
            placeholder="请输入工具名称，回车搜索"
          ></a-input>
        </div>
        <a-row :span="24">
          <a-col :span="12" v-for="item in appToolOption" @click="handleSelect(item)">
            <a-card :style="item.checked ? { border: '1px solid #3370ff' } : {}" hoverable class="checkbox-card" :body-style="{ width: '100%' }">
              <div style="display: flex; width: 100%; justify-content: space-between">
                <div>
                  <img class="checkbox-img" :src="tool" />
                  <span class="checkbox-name">{{ item.name }}</span>
                </div>
                <a-checkbox v-model:checked="item.checked" @click.stop class="quantum-checker" @change="(e)=>handleChange(e,item)"> </a-checkbox>
              </div>
            </a-card>
          </a-col>
        </a-row>
        <div v-if="toolIds.length > 0" class="use-select">
          已选择 {{ toolIds.length }} 工具
          <span style="margin-left: 8px; color: #3d79fb; cursor: pointer" @click="handleClearClick">清空</span>
        </div>
        <Pagination
          v-if="appToolOption.length > 0"
          :current="pageNo"
          :page-size="pageSize"
          :page-size-options="pageSizeOptions"
          :total="total"
          :showQuickJumper="true"
          :showSizeChanger="true"
          @change="handlePageChange"
          class="list-footer"
          size="small"
        />
      </BasicModal>
    </div>
  </template>
  
  <script lang="ts">
    import { ref, unref } from 'vue';
    import BasicModal from '@/components/Modal/src/BasicModal.vue';
    import { useModal, useModalInner } from '@/components/Modal';
    import { Pagination } from 'ant-design-vue';
    import { toolList } from '/@/components/jeecg/AiChat/llm.api';
    import knowledge from '/@/views/super/airag/aiknowledge/icon/knowledge.png';
    import { cloneDeep } from 'lodash-es';
  
    export default {
      name: 'AiAppAddToolModal',
      components: {
        Pagination,
        BasicModal,
      },
      emits: ['success', 'register'],
      setup(props, { emit }) {
        const title = ref<string>('添加关联工具');
  
        // 暂时使用知识库图标作为工具图标
        const tool = knowledge;
  
        //app工具
        const appToolOption = ref<any>([]);
        //应用类型
        const toolIds = ref<any>([]);
        //应用数据
        const toolData = ref<any>([]);
        //当前页数
        const pageNo = ref<number>(1);
        //每页条数
        const pageSize = ref<number>(10);
        //总条数
        const total = ref<number>(0);
        //搜索文本
        const searchText = ref<string>('');
        //可选择的页数
        const pageSizeOptions = ref<any>(['10', '20', '30']);
        //注册modal
        const [registerModal, { closeModal, setModalProps }] = useModalInner(async (data) => {
          toolIds.value = data.toolIds ? cloneDeep(data.toolIds.split(',')) : [];
          toolData.value = data.toolDataList ? cloneDeep(data.toolDataList) : [];
          setModalProps({ minHeight: 500, bodyStyle: { padding: '10px' } });
          loadToolData();
        });
  
        /**
         * 保存
         */
        async function handleOk() {
          console.log("工具确定选中的值",toolData.value);
          emit('success', toolIds.value, toolData.value);
          handleCancel();
        }
  
        /**
         * 取消
         */
        function handleCancel() {
          closeModal();
        }
  
        //复选框选中事件
        function handleSelect(item){
          let id = item.value;
          const target = appToolOption.value.find((item) => item.value === id);
          if (target) {
            target.checked = !target.checked;
          }
          //存放选中的工具的id
          if (!toolIds.value || toolIds.value.length == 0) {
            toolIds.value.push(id);
            toolData.value.push(item);
            console.log("工具勾选或取消勾选复选框的值",toolData.value);
            return;
          }
          let findIndex = toolIds.value.findIndex((item) => item === id);
          if (findIndex === -1) {
            toolIds.value.push(id);
            toolData.value.push(item);
          } else {
            toolIds.value.splice(findIndex, 1);
            toolData.value.splice(findIndex, 1);
          }
          console.log("工具勾选或取消勾选复选框的值",toolData.value);
        }
  
        /**
         * 加载工具
         */
        function loadToolData() {
          let params = {
            name: searchText.value,
          };
          toolList(params).then((res) => {
            if (res && res.length > 0) {
              let records = res;
              if (toolIds.value.length > 0) {
                for (const item of records) {
                  if (toolIds.value.includes(item.value)) {
                    item.checked = true;
                  }
                }
                appToolOption.value = records;
              } else {
                appToolOption.value = records;
              }
              total.value = records.length;
            } else {
              appToolOption.value = [];
              total.value = 0;
            }
          });
        }
  
        /**
         * 分页改变事件
         * @param page
         * @param current
         */
        function handlePageChange(page, current) {
          pageNo.value = page;
          pageSize.value = current;
          loadToolData();
        }
  
        /**
         * 清空选中状态
         */
        function handleClearClick() {
          toolIds.value = [];
          toolData.value = [];
          appToolOption.value.forEach((item) => {
            item.checked = false;
          });
        }
  
        /**
         * 复选框选中事件
         *
         * @param e
         * @param item
         */
        function handleChange(e, item) {
          if (e.target.checked) {
            toolIds.value.push(item.value);
            toolData.value.push(item);
          } else {
            let findIndex = toolIds.value.findIndex((val) => val === item.value);
            if (findIndex != -1) {
              toolIds.value.splice(findIndex, 1);
              toolData.value.splice(findIndex, 1);
            }
          }
        }
  
        return {
          registerModal,
          title,
          handleOk,
          handleCancel,
          appToolOption,
          toolIds,
          handleSelect,
          pageNo,
          pageSize,
          pageSizeOptions,
          total,
          handlePageChange,
          tool,
          searchText,
          loadToolData,
          handleClearClick,
          handleChange,
        };
      },
    };
  </script>
  
  <style scoped lang="less">
    .header {
      color: #646a73;
      width: 100%;
      justify-content: space-between;
      margin-bottom: 10px;
      .header-search {
        width: 200px;
      }
    }
    .pointer {
      cursor: pointer;
    }
    .type-title {
      color: #1d2025;
      margin-bottom: 4px;
    }
    .type-desc {
      color: #8f959e;
      font-weight: 400;
    }
    .list-footer {
      position: absolute;
      bottom: 0;
      right: 10px;
    }
    .checkbox-card {
      margin-bottom: 10px;
      margin-right: 10px;
    }
    .checkbox-img {
      width: 30px;
      height: 30px;
    }
    .checkbox-name {
      margin-left: 4px;
    }
    .use-select {
      color: #646a73;
      position: absolute;
      bottom: 0;
      left: 20px;
    }
  </style>