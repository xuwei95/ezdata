import type { App } from 'vue';
import { registerJVxeTable } from '/@/components/jeecg/JVxeTable';
import { registerJVxeCustom } from '/@/components/JVxeCustom';

// // 注册全局聊天表情包
// import { Picker } from 'emoji-mart-vue-fast/src';
// 注册全局dayjs
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import customParseFormat from 'dayjs/plugin/customParseFormat';
import { createAsyncComponent } from '/@/utils/factory/createAsyncComponent';

export async function registerThirdComp(app: App) {
  //---------------------------------------------------------------------
  // 注册 JVxeTable 组件
  registerJVxeTable(app);
  // 注册 JVxeTable 自定义组件
  await registerJVxeCustom();
  //---------------------------------------------------------------------
  // 注册全局聊天表情包
  //app.component('Picker', Picker);
  app.component(
    'Picker',
    createAsyncComponent(() => {
      return new Promise((resolve, rejected) => {
        import('emoji-mart-vue-fast/src')
          .then((res) => {
            const { Picker } = res;
            resolve(Picker);
          })
          .catch((err) => {
            rejected(err);
          });
      });
    })
  );
  //---------------------------------------------------------------------
  // 注册全局dayjs
  dayjs.locale('zh-cn');
  dayjs.extend(relativeTime);
  dayjs.extend(customParseFormat);
  app.config.globalProperties.$dayjs = dayjs
  app.provide('$dayjs', dayjs)
  //---------------------------------------------------------------------
}
