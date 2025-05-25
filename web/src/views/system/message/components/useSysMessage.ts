import { ref, reactive } from 'vue';
import { defHttp } from '/@/utils/http/axios';
import { getDictItemsByCode } from '/@/utils/dict/index';
import { useRouter, useRoute } from 'vue-router';
import { useAppStore } from '/@/store/modules/app';
import { useTabs } from '/@/hooks/web/useTabs';

/**
 * 列表接口
 * @param params
 */
const queryMessageList = (params) => {
  const url = '/sys/notice/listByUser';
  return defHttp.get({ url, params });
};

/**
 * 获取消息列表数据
 */
export function useSysMessage() {
  const rangeDateArray = getDictItemsByCode('rangeDate');
  console.log('+++++++++++++++++++++');
  console.log('rangeDateArray', rangeDateArray);
  console.log('+++++++++++++++++++++');

  const messageList = ref<any[]>([]);
  const pageNo = ref(1);
  const pageSize = 10;
  const searchParams = reactive({
    fromUser: '',
    rangeDateKey: '',
    rangeDate: [],
    starFlag: '',
  });

  function getQueryParams() {
    const { fromUser, rangeDateKey, rangeDate, starFlag } = searchParams;
    const params = {
      fromUser,
      starFlag,
      rangeDateKey,
      beginDate: '',
      endDate: '',
      page: pageNo.value,
      pagesize: pageSize,
    };
    if (rangeDateKey == 'zdy') {
      params.beginDate = rangeDate[0] + ' 00:00:00';
      params.endDate = rangeDate[1] + ' 23:59:59';
    }
    return params;
  }

  // 数据是否加载完了
  const loadEndStatus = ref(false);

  //请求数据
  async function loadData() {
    if (loadEndStatus.value === true) {
      return;
    }
    const params = getQueryParams();
    const data = await queryMessageList(params);
    console.log('获取结果', data);
    if (!data || data.length <= 0) {
      loadEndStatus.value = true;
      return;
    }
    if (data.length < pageSize) {
      loadEndStatus.value = true;
    }
    pageNo.value = pageNo.value + 1;
    const temp: any[] = messageList.value;
    temp.push(...data);
    messageList.value = temp;
  }

  //重置
  function reset() {
    messageList.value = [];
    pageNo.value = 1;
    loadEndStatus.value = false;
  }

  //标星
  function updateStarMessage(item) {
    const url = '/sys/notice/send/edit';
    let starFlag = '1';
    if (item.star_flag == starFlag) {
      starFlag = '0';
    }
    const params = {
      star_flag: starFlag,
      send_id: item.send_id,
    };
    defHttp.put({ url, params });
  }

  const loadingMoreStatus = ref(false);
  async function onLoadMore() {
    loadingMoreStatus.value = true;
    await loadData();
    loadingMoreStatus.value = false;
  }

  function noRead(item) {
    if (item.read_flag === 1) {
      return false;
    }
    return true;
  }

  // 消息类型
  function getMsgCategory(item) {
    if (item.busType == 'email') {
      return '邮件提醒:';
    } else if (item.busType == 'bpm') {
      return '流程催办:';
    } else if (item.busType == 'bpm_task') {
      return '流程任务:';
    } else if (item.msg_category == '2') {
      return '系统消息:';
    } else if (item.msg_category == '1') {
      return '通知公告:';
    }
    return '';
  }

  return {
    messageList,
    reset,
    loadData,
    loadEndStatus,
    searchParams,
    updateStarMessage,
    onLoadMore,
    noRead,
    getMsgCategory,
  };
}

/**
 * 用于消息跳转
 */
export function useMessageHref(emit) {
  const messageHrefArray: any[] = getDictItemsByCode('messageHref');
  const router = useRouter();
  const appStore = useAppStore();
  const rt = useRoute();
  const { close: closeTab, closeSameRoute } = useTabs();
  // const defaultPath = '/monitor/mynews';
  //const bpmPath = '/task/handle/'

  async function goPage(record, openModalFun?) {
    if (!record.busType) {
      if (!openModalFun) {
        // 从首页的消息通知跳转
        await goPageFromOuter(record);
      } else {
        // 从消息页面列表点击详情查看 直接打开modal
        openModalFun();
      }
    } else {
      await goPageWithBusType(record);
    }
    /*    busId: "1562035005173587970"
    busType: "email"
    openPage: "modules/eoa/email/modals/EoaEmailInForm"
    openType: "component"*/
  }

  /**
   * 根据busType不同跳转不同页面
   * @param record
   */
  async function goPageWithBusType(record) {
    const { busType, busId, msgAbstract } = record;
    const temp = messageHrefArray.filter((item) => item.value === busType);
    if (!temp || temp.length == 0) {
      console.error('当前业务类型不识别', busType);
      return;
    }
    let path = temp[0].text;
    path = path.replace('{DETAIL_ID}', busId);
    //固定参数 detailId 用于查询表单数据
    const query = {
      detailId: busId,
    };
    // 额外参数处理
    if (msgAbstract) {
      try {
        const json = JSON.parse(msgAbstract);
        Object.keys(json).map((k) => {
          query[k] = json[k];
        });
      } catch (e) {
        console.error('msgAbstract参数不是JSON格式', msgAbstract);
      }
    }
    // 跳转路由
    appStore.setMessageHrefParams(query);
    if (rt.path.indexOf(path) >= 0) {
      await closeTab();
      await router.replace({ path: path, query: { time: new Date().getTime() } });
    } else {
      closeSameRoute(path);
      await router.push({ path: path });
    }
  }

  /**
   * 从首页的消息通知跳转消息列表打开modal
   * @param record
   */
  async function goPageFromOuter(record) {
    //没有定义业务类型 直接跳转我的消息页面
    emit('detail', record);
  }

  return {
    goPage,
  };
}
