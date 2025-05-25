<template>
  <div class="md:flex">
    <template v-for="(item, index) in growCardList" :key="item.title">
      <Card
        size="small"
        :loading="loading"
        :title="item.title"
        class="md:w-1/4 w-full !md:mt-0 !mt-4"
        :class="[index + 1 < 4 && '!md:mr-4']"
        :canExpan="false"
      >
        <template #extra>
          <Tag :color="item.color">{{ item.action }}</Tag>
        </template>

        <div class="py-4 px-4 flex justify-between">
          <CountTo prefix="" :startVal="1" :endVal="item.value" class="text-2xl" />
          <Icon :icon="item.icon" :size="40" />
        </div>
      </Card>
    </template>
  </div>
</template>
<script lang="ts" setup>
  import { ref } from 'vue';
  import { CountTo } from '/@/components/CountTo/index';
  import { Tag, Card } from 'ant-design-vue';
  import { Icon } from '/@/components/Icon';
  import { getDashboardInfo } from '/@/views/dashboard/Analysis/api';
  const loading = ref(false);
  const growCardList = ref([
    {
      title: '任务执行数',
      icon: 'taREDACTEDcount|svg',
      value: 0,
      color: 'green',
      action: '今日',
    },
    {
      title: '接口访问量',
      icon: 'interface-count|svg',
      value: 0,
      color: 'blue',
      action: '今日',
    },
    {
      title: '系统访问量',
      icon: 'visit-count|svg',
      value: 0,
      color: 'purple',
      action: '今日',
    },
    {
      title: '数据模型数',
      icon: 'model-count|svg',
      value: 0,
      color: 'orange',
      action: '总数',
    },
  ]);
  function initDashboard() {
    loading.value = true;
    getDashboardInfo({}).then((res) => {
      growCardList.value = res.data;
      loading.value = false;
    });
  }
  initDashboard();
  // const growCardList =
</script>
