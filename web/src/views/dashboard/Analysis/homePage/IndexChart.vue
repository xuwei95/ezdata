<template>
  <div class="p-4">
    <ChartGroupCard class="enter-y" :loading="loading" type="chart" />
    <SaleTabCard class="!my-4 enter-y" :loading="loading" />
    <a-row>
      <a-col :span="24">
        <a-card :loading="loading" :bordered="false" title="最近一周访问量统计" :style="{ marginTop: '24px' }">
          <a-row>
            <a-col :span="6">
              <HeadInfo title="今日IP" :content="loginfo.todayIp" icon="environment"></HeadInfo>
            </a-col>
            <a-col :span="6">
              <HeadInfo title="今日访问" :content="loginfo.todayVisitCount" icon="team"></HeadInfo>
            </a-col>
            <a-col :span="6">
              <HeadInfo title="总访问量" :content="loginfo.totalVisitCount" icon="rise"></HeadInfo>
            </a-col>
          </a-row>
          <LineMulti :chartData="lineMultiData" height="50vh" type="line" :option="{ legend: { top: 'bottom' } }"></LineMulti>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>
<script lang="ts" setup>
  import { ref } from 'vue';
  import ChartGroupCard from '../components/ChartGroupCard.vue';
  import SaleTabCard from '../components/SaleTabCard.vue';
  import LineMulti from '/@/components/chart/LineMulti.vue';
  import HeadInfo from '/@/components/chart/HeadInfo.vue';
  import { getLoginfo, getVisitInfo } from '../api.ts';

  const loading = ref(true);

  setTimeout(() => {
    loading.value = false;
  }, 500);

  const loginfo = ref({});
  const lineMultiData = ref([]);

  function initLogInfo() {
    getLoginfo(null).then((res) => {
      if (res.success) {
        Object.keys(res.result).forEach((key) => {
          res.result[key] = res.result[key] + '';
        });
        loginfo.value = res.result;
      }
    });
    getVisitInfo(null).then((res) => {
      if (res.success) {
        lineMultiData.value = [];
        res.result.forEach((item) => {
          lineMultiData.value.push({ name: item.type, type: 'ip', value: item.ip });
          lineMultiData.value.push({ name: item.type, type: 'visit', value: item.visit });
        });
      }
    });
  }

  initLogInfo();
</script>

<style lang="less" scoped>
  .circle-cust {
    position: relative;
    top: 28px;
    left: -100%;
  }

  .extra-wrapper {
    line-height: 55px;
    padding-right: 24px;

    .extra-item {
      display: inline-block;
      margin-right: 24px;

      a {
        margin-left: 24px;
      }
    }
  }

  /* 首页访问量统计 */
  .head-info {
    position: relative;
    text-align: left;
    padding: 0 32px 0 0;
    min-width: 125px;

    &.center {
      text-align: center;
      padding: 0 32px;
    }

    span {
      color: rgba(0, 0, 0, 0.45);
      display: inline-block;
      font-size: 0.95rem;
      line-height: 42px;
      margin-bottom: 4px;
    }

    p {
      line-height: 42px;
      margin: 0;

      a {
        font-weight: 600;
        font-size: 1rem;
      }
    }
  }
</style>
