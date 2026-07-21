<template>
  <!-- 全站 locale 联动:element-plus + ant-design-vue 随语言切换(vxe 走命令式,见 lang/index.js) -->
  <el-config-provider :locale="elLocale" :size="size">
    <a-config-provider :locale="antdLocale">
      <router-view />
    </a-config-provider>
  </el-config-provider>
</template>

<script setup>
import { ElConfigProvider } from 'element-plus'
import elZhCn from 'element-plus/es/locale/lang/zh-cn'
import elEn from 'element-plus/es/locale/lang/en'
import { ConfigProvider as AConfigProvider } from 'ant-design-vue'
import antdZhCN from 'ant-design-vue/es/locale/zh_CN'
import antdEnUS from 'ant-design-vue/es/locale/en_US'

import useAppStore from '@/store/modules/app'
import useSettingsStore from '@/store/modules/settings'
import { handleThemeStyle } from '@/utils/theme'

const appStore = useAppStore()
const size = computed(() => appStore.size)
const isEn = computed(() => appStore.language === 'en')
const elLocale = computed(() => (isEn.value ? elEn : elZhCn))
const antdLocale = computed(() => (isEn.value ? antdEnUS : antdZhCN))

onMounted(() => {
  nextTick(() => {
    // 初始化主题样式
    handleThemeStyle(useSettingsStore().theme)
  })
})
</script>
