<template>
  <el-dropdown trigger="click" @command="handleSetLanguage">
    <div class="lang-icon--style">
      <svg-icon class-name="lang-icon" icon-class="language" />
    </div>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          v-for="item of languages"
          :key="item.value"
          :disabled="language === item.value"
          :command="item.value"
        >
          {{ item.label }}
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import useAppStore from '@/store/modules/app'
import { LANGUAGES } from '@/lang'

const appStore = useAppStore()
const languages = LANGUAGES
const language = computed(() => appStore.language)

function handleSetLanguage(lang) {
  if (lang === appStore.language) return
  appStore.setLanguage(lang)
}
</script>

<style lang="scss" scoped>
.lang-icon--style {
  font-size: 18px;
  line-height: 50px;
  padding-right: 7px;
  cursor: pointer;
}
</style>
