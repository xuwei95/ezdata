import Cookies from 'js-cookie'
import { LANGUAGE_KEY, getLanguage, applyLanguage } from '@/lang'

const useAppStore = defineStore(
  'app',
  {
    state: () => ({
      sidebar: {
        opened: Cookies.get('sidebarStatus') ? !!+Cookies.get('sidebarStatus') : true,
        withoutAnimation: false,
        hide: false
      },
      device: 'desktop',
      size: Cookies.get('size') || 'default',
      language: getLanguage()
    }),
    actions: {
      toggleSideBar(withoutAnimation) {
        if (this.sidebar.hide) {
          return false;
        }
        this.sidebar.opened = !this.sidebar.opened
        this.sidebar.withoutAnimation = withoutAnimation
        if (this.sidebar.opened) {
          Cookies.set('sidebarStatus', 1)
        } else {
          Cookies.set('sidebarStatus', 0)
        }
      },
      closeSideBar({ withoutAnimation }) {
        Cookies.set('sidebarStatus', 0)
        this.sidebar.opened = false
        this.sidebar.withoutAnimation = withoutAnimation
      },
      toggleDevice(device) {
        this.device = device
      },
      setSize(size) {
        this.size = size;
        Cookies.set('size', size)
      },
      setLanguage(language) {
        this.language = language
        Cookies.set(LANGUAGE_KEY, language)
        applyLanguage(language) // 同步 vue-i18n + vxe;element-plus/antd 由 App.vue ConfigProvider 响应
      },
      toggleSideBarHide(status) {
        this.sidebar.hide = status
      }
    }
  })

export default useAppStore
