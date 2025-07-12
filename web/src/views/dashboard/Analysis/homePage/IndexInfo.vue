<template>
  <div class="p-4">
    <InfoCard class="enter-y" />
    <InfoAnalysis class="!my-4 enter-y" />
    <div class="md:flex enter-y">
      <InfoInterfacePie class="md:w-1/3 !md:mx-4 !md:my-0 !my-4 w-full" />
      <InfoTaskStatusPie class="md:w-1/3 !md:mx-4 !md:my-0 !my-4 w-full" />
      <InfoModelTypePie class="md:w-1/3 w-full" />
    </div>
  </div>
</template>
<script lang="ts" setup>
  import { ref } from 'vue';
  import InfoCard from '../components/InfoCard.vue';
  import InfoAnalysis from '../components/InfoAnalysis.vue';
  import InfoTaskStatusPie from '../components/InfoTaskStatusPie.vue';
  import InfoInterfacePie from '../components/InfoInterfacePie.vue';
  import InfoModelTypePie from '../components/InfoModelTypePie.vue';

  const loading = ref(true);

  setTimeout(() => {
    loading.value = false;
  }, 500);
</script>
