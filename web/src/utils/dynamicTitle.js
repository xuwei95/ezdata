import defaultSettings from '@/settings'
import useSettingsStore from '@/store/modules/settings'
import { t } from '@/lang'

/**
 * 动态修改标题
 */
export function useDynamicTitle() {
  const settingsStore = useSettingsStore();
  if (settingsStore.dynamicTitle) {
    // settingsStore.title 来自 route.meta.title(菜单名),过 t() 翻译(中文即 key)
    document.title = t(settingsStore.title) + ' - ' + defaultSettings.title;
  } else {
    document.title = defaultSettings.title;
  }
}