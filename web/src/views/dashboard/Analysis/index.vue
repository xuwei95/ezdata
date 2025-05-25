<template>
  <IndexInfo v-if="indexStyle === 4"></IndexInfo>
<!--  <IndexDef v-if="indexStyle === 0"></IndexDef>-->
<!--  <IndexChart v-if="indexStyle === 1"></IndexChart>-->
<!--  <IndexBdc v-if="indexStyle == 2"></IndexBdc>-->
<!--  <IndexTask v-if="indexStyle == 3"></IndexTask>-->
<!--  <div style="width: 100%; text-align: right; margin-top: 20px">-->
<!--    请选择首页样式：-->
<!--    <a-radio-group v-model:value="indexStyle">-->
<!--      <a-radio :value="0">默认</a-radio>-->
<!--      <a-radio :value="1">销量统计</a-radio>-->
<!--      <a-radio :value="2">业务统计</a-radio>-->
<!--      <a-radio :value="3">我的任务</a-radio>-->
<!--    </a-radio-group>-->
<!--  </div>-->
</template>
<script lang="ts" setup>
  import { ref } from 'vue';
  import IndexInfo from './homePage/IndexInfo.vue';
  // import IndexDef from './homePage/IndexDef.vue';
  // import IndexChart from './homePage/IndexChart.vue';
  // import IndexBdc from './homePage/IndexBdc.vue';
  // import IndexTask from './homePage/IndexTask.vue';
  const indexStyle = ref(4);
</script>
