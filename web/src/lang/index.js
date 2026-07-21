/**
 * i18n 入口(vue-i18n@9,组合式)。
 *
 * 语言策略:**中文即 key** —— 源码里直接 `$t('保存')`;
 *  - `zh-CN` 无需维护映射(查不到 key 时按 fallback 回退 key 本身,即显示中文);
 *  - `en` 维护 { 中文源文案: English }(见 ./en.js)。
 * 好处:未迁移/漏翻的文案自动显示中文,可逐屏灰度,无需一次性铺满整站。
 * 注意:作 key 的中文文案里**不要含英文句点 `.`**(vue-i18n 会当成路径分隔)。
 *
 * 三套 UI 库联动:element-plus / ant-design-vue 由各自 ConfigProvider 响应式处理(见 App.vue);
 * vxe-table 走命令式 setLanguage(此处注册英文包 + 暴露切换函数)。
 */
import { createI18n } from 'vue-i18n'
import Cookies from 'js-cookie'
import { VxeUI } from 'vxe-pc-ui'
import vxeEnUS from 'vxe-pc-ui/lib/language/en-US'

import en from './en'

export const LANGUAGE_KEY = 'language'
export const LANGUAGES = [
  { value: 'zh-CN', label: '简体中文' },
  { value: 'en', label: 'English' },
]

export function getLanguage() {
  const lang = Cookies.get(LANGUAGE_KEY)
  return LANGUAGES.some((l) => l.value === lang) ? lang : 'zh-CN'
}

const i18n = createI18n({
  legacy: false,
  globalInjection: true, // 模板里可直接用 $t;JS 里用 i18n.global.t
  locale: getLanguage(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': {}, // 中文即 key,无需映射
    en,
  },
  missingWarn: false,
  fallbackWarn: false,
})

// 注册 vxe 英文包(zh-CN 为 vxe 默认,无需注册)
try {
  VxeUI.setI18n && VxeUI.setI18n('en-US', vxeEnUS)
} catch (e) {
  /* 版本差异忽略,vxe 退回默认语言,不阻断 */
}

/** 切换 vxe-table 语言(本站 locale → vxe 语言码)。 */
export function setVxeLanguage(lang) {
  try {
    VxeUI.setLanguage(lang === 'en' ? 'en-US' : 'zh-CN')
  } catch (e) {
    /* 忽略 */
  }
}

/** 应用某语言:设 i18n + vxe。element-plus/antd 由 ConfigProvider 跟随 i18n.locale。 */
export function applyLanguage(lang) {
  i18n.global.locale.value = lang
  setVxeLanguage(lang)
}

// 初始化 vxe 语言与当前一致
setVxeLanguage(getLanguage())

/** 供 JS(非模板)中翻译使用。 */
export function t(key, ...args) {
  return i18n.global.t(key, ...args)
}

export default i18n
