<template>
    <div class="p-2">
      <BasicModal destroyOnClose @register="registerModal" :canFullscreen="false" width="600px" :title="title" @ok="handleOk" @cancel="handleCancel">
        <div class="flex header">
          <a-input
            @pressEnter="loadDataModelData"
            class="header-search"
            size="small"
            v-model:value="searchText"
            placeholder="请输入数据模型名称，回车搜索"
          ></a-input>
        </div>
        <a-row :span="24">
          <a-col :span="12" v-for="item in appDataModelOption" @click="handleSelect(item)">
            <a-card :style="item.checked ? { border: '1px solid #3370ff' } : {}" hoverable class="checkbox-card" :body-style="{ width: '100%' }">
              <div style="display: flex; width: 100%; justify-content: space-between">
                <div>
                  <img class="checkbox-img" :src="datamodel" />
                  <span class="checkbox-name">{{ item.name }}</span>
                </div>
                <a-checkbox v-model:checked="item.checked" @click.stop class="quantum-checker" @change="(e)=>handleChange(e,item)"> </a-checkbox>
              </div>
            </a-card>
          </a-col>
        </a-row>
        <div v-if="datamodelIds.length > 0" class="use-select">
          已选择 {{ datamodelIds.length }} 数据模型
          <span style="margin-left: 8px; color: #3d79fb; cursor: pointer" @click="handleClearClick">清空</span>
        </div>
        <Pagination
          v-if="appDataModelOption.length > 0"
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
    import { list } from '/@/views/dataManage/dataModel/datamodel.api';
    import dataImg from '/@/views/llm/aiapp/img/datamodel.png';
    import { cloneDeep } from 'lodash-es';
  
    export default {
      name: 'AiAppAddDataModelModal',
      components: {
        Pagination,
        BasicModal,
      },
      emits: ['success', 'register'],
      setup(props, { emit }) {
        const title = ref<string>('添加关联数据模型');
  
        // 暂时使用知识库图标作为数据模型图标
        const datamodel = dataImg;
  
        //app数据模型
        const appDataModelOption = ref<any>([]);
        //应用类型
        const datamodelIds = ref<any>([]);
        //应用数据
        const datamodelData = ref<any>([]);
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
          datamodelIds.value = data.datamodelIds ? cloneDeep(data.datamodelIds.split(',')) : [];
          datamodelData.value = data.datamodelDataList ? cloneDeep(data.datamodelDataList) : [];
          setModalProps({ minHeight: 500, bodyStyle: { padding: '10px' } });
          loadDataModelData();
        });
  
        /**
         * 保存
         */
        async function handleOk() {
          console.log("数据模型确定选中的值",datamodelData.value);
          emit('success', datamodelIds.value, datamodelData.value);
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
          let id = item.id;
          const target = appDataModelOption.value.find((item) => item.id === id);
          if (target) {
            target.checked = !target.checked;
          }
          //存放选中的数据模型的id
          if (!datamodelIds.value || datamodelIds.value.length == 0) {
            datamodelIds.value.push(id);
            datamodelData.value.push(item);
            console.log("数据模型勾选或取消勾选复选框的值",datamodelData.value);
            return;
          }
          let findIndex = datamodelIds.value.findIndex((item) => item === id);
          if (findIndex === -1) {
            datamodelIds.value.push(id);
            datamodelData.value.push(item);
          } else {
            datamodelIds.value.splice(findIndex, 1);
            datamodelData.value.splice(findIndex, 1);
          }
          console.log("数据模型勾选或取消勾选复选框的值",datamodelData.value);
        }
  
        /**
         * 加载数据模型
         */
        function loadDataModelData() {
          let params = {
            name: searchText.value,
            page: pageNo.value,
            pagesize: pageSize.value,
          };
          list(params).then((res) => {
            if (res.records && res.records.length > 0) {
              let records = res.records;
              if (datamodelIds.value.length > 0) {
                for (const item of records) {
                  if (datamodelIds.value.includes(item.id)) {
                    item.checked = true;
                  }
                }
                appDataModelOption.value = records;
              } else {
                appDataModelOption.value = records;
              }
              total.value = res.total;
            } else {
              appDataModelOption.value = [];
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
          loadDataModelData();
        }
  
        /**
         * 清空选中状态
         */
        function handleClearClick() {
          datamodelIds.value = [];
          datamodelData.value = [];
          appDataModelOption.value.forEach((item) => {
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
            datamodelIds.value.push(item.id);
            datamodelData.value.push(item);
          } else {
            let findIndex = datamodelIds.value.findIndex((val) => val === item.id);
            if (findIndex != -1) {
              datamodelIds.value.splice(findIndex, 1);
              datamodelData.value.splice(findIndex, 1);
            }
          }
        }
  
        return {
          registerModal,
          title,
          handleOk,
          handleCancel,
          appDataModelOption,
          datamodelIds,
          handleSelect,
          pageNo,
          pageSize,
          pageSizeOptions,
          total,
          handlePageChange,
          datamodel,
          searchText,
          loadDataModelData,
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