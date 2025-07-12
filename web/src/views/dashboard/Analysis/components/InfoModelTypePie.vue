<template>
  <Card title="数据模型统计" :loading="loading">
    <div ref="chartRef" :style="{ height, width }"></div>
  </Card>
</template>
<script lang="ts" setup>
  import { Ref, ref } from 'vue';
  import { Card } from 'ant-design-vue';
  import { useECharts } from '/@/hooks/web/useECharts';
  import { getDataModelTypeInfo } from '/@/views/dashboard/Analysis/api';
  const loading = ref(false);
  const props = defineProps({
    width: {
      type: String as PropType<string>,
      default: '100%',
    },
    height: {
      type: String as PropType<string>,
      default: '300px',
    },
  });
  const chartRef = ref<HTMLDivElement | null>(null);
  const { setOptions } = useECharts(chartRef as Ref<HTMLDivElement>);
  const type_data = ref([]);
  function initData() {
    loading.value = true;
    getDataModelTypeInfo({}).then((res) => {
      type_data.value = res.data;
      console.log(type_data.value);
      setOptions({
        tooltip: {
          trigger: 'item',
        },
        series: [
          {
            name: '数据模型统计',
            type: 'pie',
            radius: '80%',
            center: ['50%', '50%'],
            data: type_data.value,
            roseType: 'radius',
            animationType: 'scale',
            animationEasing: 'exponentialInOut',
            animationDelay: function () {
              return Math.random() * 400;
            },
          },
        ],
      });
      loading.value = false;
    });
  }
  initData();
</script>
