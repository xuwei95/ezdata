<template>
  <div ref="chartRef" :style="{ height, width }"></div>
</template>
<script lang="ts" setup>
  import { onMounted, ref, Ref } from 'vue';
  import { useECharts } from '/@/hooks/web/useECharts';
  import { basicProps } from './props';
  import { getTaskInfo } from '/@/views/dashboard/Analysis/api';

  defineProps({
    ...basicProps,
  });
  const x_data = ref([]);
  const task_line = ref([]);
  const chartRef = ref<HTMLDivElement | null>(null);
  const { setOptions } = useECharts(chartRef as Ref<HTMLDivElement>);
  function initChart() {
    getTaskInfo({}).then((res) => {
      x_data.value = res.data.x_data;
      task_line.value = res.data.task_line;
      setOptions({
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            lineStyle: {
              width: 1,
              color: '#019680',
            },
          },
        },
        grid: { left: '1%', right: '1%', top: '2  %', bottom: 0, containLabel: true },
        xAxis: {
          type: 'category',
          data: x_data.value,
        },
        yAxis: {
          type: 'value',
          splitNumber: 4,
        },
        series: [
          {
            name: '任务数',
            data: task_line.value,
            type: 'bar',
            barMaxWidth: 80,
          },
        ],
      });
    });
  }
  onMounted(async () => {
    initChart();
  });
</script>
