<template>
  <div class="chat" :class="[inversion === 'user' ? 'self' : 'chatgpt']" v-if="shouldShow">
    <div class="avatar">
      <img v-if="inversion === 'user'" :src="avatar()" />
      <img v-else :src="getAiImg()" />
    </div>
    <div class="content">
      <p class="date">
        <span v-if="inversion === 'ai'" style="margin-right: 10px">{{ appData.name || 'AI助手' }}</span>
        <span>{{ dateTime }}</span>
      </p>

      <!-- ===== AI 消息 ===== -->
      <template v-if="inversion === 'ai'">

        <!-- events 模式：step 和 markdown 按顺序交错渲染 -->
        <template v-if="hasEvents">
          <div class="ev-wrap">
            <template v-for="(ev, idx) in events" :key="idx">

              <!-- Thinking 折叠卡片 -->
              <div v-if="ev.type === 'thinking'" class="ev-thinking">
                <div class="ev-thinking-hd" @click="toggleStep(idx)">
                  <svg class="ev-thinking-icon" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/>
                  </svg>
                  <span class="ev-thinking-title">{{ expandedSteps[idx] ? '思考过程' : '思考过程' }}</span>
                  <span v-if="loading && idx === events.length - 1" class="ev-thinking-dot"></span>
                  <svg viewBox="0 0 1024 1024" width="11" height="11" fill="currentColor"
                    :class="['ev-step-arrow', expandedSteps[idx] ? 'ev-step-arrow-up' : '']">
                    <path d="M884 256h-75c-5.1 0-9.9 2.5-12.9 6.6L512 654.2 227.9 262.6c-3-4.1-7.8-6.6-12.9-6.6h-75c-6.5 0-10.3 7.4-6.5 12.7l352.6 486.1c12.8 17.6 39 17.6 51.7 0l352.6-486.1c3.9-5.3.1-12.7-6.4-12.7z"/>
                  </svg>
                </div>
                <div v-show="expandedSteps[idx]" class="ev-thinking-body">
                  <chatText v-if="ev.content" :text="ev.content"></chatText>
                </div>
              </div>

              <!-- Step 折叠卡片 -->
              <div v-if="ev.type === 'step'" class="ev-step">
                <div class="ev-step-hd" @click="toggleStep(idx)">
                  <svg class="ev-step-check" viewBox="0 0 1024 1024" width="13" height="13" fill="currentColor">
                    <path d="M912 190h-69.9c-9.8 0-19.1 4.5-25.1 12.2L404.7 724.5 207 474a32 32 0 00-25.1-12.2H112c-6.7 0-10.4 7.7-6.3 12.9l273.9 347c12.8 16.2 37.4 16.2 50.3 0l488.4-618.9c4.1-5.1.4-12.8-6.3-12.8z"/>
                  </svg>
                  <span class="ev-step-title">{{ ev.step.title }}</span>
                  <span class="ev-step-time" v-if="ev.step.time">{{ ev.step.time }}</span>
                  <svg viewBox="0 0 1024 1024" width="11" height="11" fill="currentColor"
                    :class="['ev-step-arrow', expandedSteps[idx] ? 'ev-step-arrow-up' : '']">
                    <path d="M884 256h-75c-5.1 0-9.9 2.5-12.9 6.6L512 654.2 227.9 262.6c-3-4.1-7.8-6.6-12.9-6.6h-75c-6.5 0-10.3 7.4-6.5 12.7l352.6 486.1c12.8 17.6 39 17.6 51.7 0l352.6-486.1c3.9-5.3.1-12.7-6.4-12.7z"/>
                  </svg>
                </div>
                <div v-show="expandedSteps[idx]" class="ev-step-body">
                  <chatText v-if="ev.step.content" :text="ev.step.content"></chatText>
                  <span v-else class="ev-step-empty">暂无详细信息</span>
                </div>
              </div>

              <!-- Text / Card 渲染 -->
              <div v-else-if="ev.type === 'text'" class="ev-text">
                <div v-if="isCardText(ev.content)" class="card">
                  <a-row>
                    <a-col v-for="ci in parseCardText(ev.content)" :xl="6" :lg="8" :md="10" :sm="24" style="flex:1">
                      <a-card class="ai-card" @click="aiCardHandleClick(ci.linkUrl)">
                        <div class="ai-card-title">{{ ci.productName }}</div>
                        <div class="ai-card-img"><img :src="ci.productImage" /></div>
                        <span class="ai-card-desc">{{ ci.descr }}</span>
                      </a-card>
                    </a-col>
                  </a-row>
                </div>
                <chatText v-else
                  :text="ev.content"
                  :inversion="inversion"
                  :error="error"
                  :loading="loading && idx === events.length - 1"
                  :referenceKnowledge="idx === events.length - 1 ? referenceKnowledge : []">
                </chatText>
              </div>

            </template>

            <!-- events 末尾仍在加载（最后一条是 step，等待后续 message） -->
            <div v-if="loading && events[events.length - 1]?.type === 'step'" class="retrieval">
              {{ retrievalText || '思考中...' }}
            </div>
          </div><!-- /ev-wrap -->
        </template>

        <!-- 无 events：兼容旧历史记录 / 纯加载占位 -->
        <template v-else>
          <div v-if="retrievalText && loading" class="retrieval">{{ retrievalText }}</div>
          <div v-if="isCard" class="card">
            <a-row>
              <a-col v-for="ci in getCardList()" :xl="6" :lg="8" :md="10" :sm="24" style="flex:1">
                <a-card class="ai-card" @click="aiCardHandleClick(ci.linkUrl)">
                  <div class="ai-card-title">{{ ci.productName }}</div>
                  <div class="ai-card-img"><img :src="ci.productImage" /></div>
                  <span class="ai-card-desc">{{ ci.descr }}</span>
                </a-card>
              </a-col>
            </a-row>
          </div>
          <div class="msgArea" v-if="!isCard">
            <chatText :text="text" :inversion="inversion" :error="error" :loading="loading" :referenceKnowledge="referenceKnowledge"></chatText>
          </div>
        </template>

        <!-- 数据表格 -->
        <div v-if="showTable" style="width: 100%">
          <JVxeTable ref="tableRef" toolbar :column-config="{ resizable: true }" :maxHeight="400" :toolbarConfig="{ btn: [] }" :columns="columns" :dataSource="dataSource">
            <template #toolbarSuffix>
              <a-button @click="outputData" style="float: right" preIcon="ant-design:export-outlined">导出数据</a-button>
            </template>
          </JVxeTable>
        </div>

        <!-- HTML 图表 -->
        <div class="html-body" v-if="props.html && props.html !== ''">
          <a-button @click="outputChart" style="float: right; margin-bottom: 8px;" preIcon="ant-design:export-outlined">导出图表</a-button>
          <iframe :key="props.html" :srcdoc="props.html" width="100%" height="100%" frameborder="0"></iframe>
        </div>

        <!-- 预设问题 -->
        <div v-if="presetQuestion" v-for="item in presetQuestion" class="question" @click="presetQuestionClick(item.descr)">
          <span>{{ item.descr }}</span>
        </div>
      </template>

      <!-- ===== 用户消息 ===== -->
      <template v-else>
        <div v-if="images && images.length > 0" class="images">
          <div v-for="(item, index) in images" :key="index" class="image" @click="handlePreview(item)">
            <img :src="getImageUrl(item)" />
          </div>
        </div>
        <div class="msgArea">
          <chatText :text="text" :inversion="inversion" :error="error" :loading="loading" :referenceKnowledge="referenceKnowledge"></chatText>
        </div>
        <div v-if="presetQuestion" v-for="item in presetQuestion" class="question" @click="presetQuestionClick(item.descr)">
          <span>{{ item.descr }}</span>
        </div>
      </template>

    </div>
  </div>
</template>

<script setup lang="ts">
  import chatText from './chatText.vue';
  import defaultAvatar from "@/assets/images/ai/avatar.jpg";
  import { useUserStore } from '/@/store/modules/user';
  import defaultImg from '../img/ailogo.png';
  import { getFileAccessHttpUrl } from '/@/utils/common/compUtils';
  import { createImgPreview } from "@/components/Preview";
  import { computed, defineExpose, onMounted, ref, watch } from "vue";
  import { useMethods } from '@/hooks/system/useMethods';
  import { JVxeTypes, JVxeColumn, JVxeTableInstance } from '/@/components/jeecg/JVxeTable/types';

  const props = defineProps(['dateTime', 'text', 'inversion', 'error', 'loading', 'appData', 'presetQuestion', 'images', 'retrievalText', 'referenceKnowledge', 'html', 'tableData', 'events']);

  // 调试：监听 events 变化
  watch(() => props.events, (newVal) => {
    console.log('chatMessage events 变化:', newVal);
  }, { deep: true, immediate: true });

  // ---- 数据表格 ----
  const tableRef = ref<JVxeTableInstance>();
  const showTable = computed(() => Boolean(props.tableData && (props.tableData as any[]).length > 0));
  const columns = ref<JVxeColumn[]>([]);
  const dataSource = ref<any[]>([]);
  const { handleExportExcel } = useMethods();

  async function outputData() {
    handleExportExcel('数据导出_' + Date.now() + '.xlsx', dataSource.value);
  }

  function handleTableData() {
    const data_li = props.tableData as any[];
    if (data_li && data_li.length > 0) {
      columns.value = Object.keys(data_li[0]).map((field_key) => ({
        title: field_key,
        key: field_key,
        type: JVxeTypes.normal,
        width: 200,
      }));
      dataSource.value = data_li;
    }
  }

  async function outputChart() {
    const data = new Blob([props.html], { type: 'text/html' });
    const url = URL.createObjectURL(data);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', '图表导出_' + Date.now() + '.html');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  onMounted(() => { handleTableData(); });
  defineExpose({ handleData: handleTableData });
  watch(() => props.tableData, () => { handleTableData(); }, { deep: true });

  // ---- events 渲染 ----
  const hasEvents = computed(() => {
    const result = Boolean(props.events && props.events.length > 0);
    console.log('hasEvents 计算:', { events: props.events, result });
    return result;
  });

  // step 详情折叠状态（key: event index）
  const expandedSteps = ref<Record<number, boolean>>({});
  const toggleStep = (idx: number) => {
    expandedSteps.value = { ...expandedSteps.value, [idx]: !expandedSteps.value[idx] };
  };

  // loading 时自动展开最后一个 thinking block
  watch(() => props.events, (evs) => {
    if (!evs || !props.loading) return;
    const lastIdx = evs.length - 1;
    if (lastIdx >= 0 && evs[lastIdx].type === 'thinking') {
      expandedSteps.value = { ...expandedSteps.value, [lastIdx]: true };
    }
  }, { deep: true });

  const isCardText = (content: string) => Boolean(content && String(content).indexOf('::card::') !== -1);
  const parseCardText = (content: string) => {
    try { return JSON.parse(String(content).replace('::card::', '').replace(/\s+/g, '')); }
    catch (e) { return []; }
  };

  // ---- 旧格式 card 兼容 ----
  const isCard = computed(() => Boolean(props.text && String(props.text).indexOf('::card::') !== -1));
  const getCardList = () => {
    try { return JSON.parse(String(props.text).replace('::card::', '').replace(/\s+/g, '')); }
    catch (e) { return []; }
  };
  const aiCardHandleClick = (url: string) => { window.open(url, '_blank'); };

  const getText = computed(() => {
    if (props.text) return String(props.text).trim();
    // 只有在无 events 模式才看 retrievalText
    if (!hasEvents.value && props.retrievalText) return String(props.retrievalText).trim();
    return '';
  });

  const shouldShow = computed(() => {
    if (props.inversion === 'user') {
      return Boolean(props.text || (props.images && props.images.length > 0) || (props.presetQuestion && props.presetQuestion.length > 0));
    }
    // 有 events 时，只要有 events 或正在 loading 就显示
    if (hasEvents.value) {
      console.log('shouldShow: hasEvents=true');
      return true;
    }
    // 无 events 时，沿用原逻辑
    const result = (
      props.loading ||
      getText.value ||
      (props.presetQuestion && props.presetQuestion.length > 0) ||
      showTable.value ||
      Boolean(props.html)
    );
    console.log('shouldShow: 无 events 模式', { loading: props.loading, text: getText.value, result });
    return result;
  });

  const { userInfo } = useUserStore();
  const avatar = () => getFileAccessHttpUrl(userInfo?.avatar) || defaultAvatar;
  const getAiImg = () => getFileAccessHttpUrl(props.appData?.icon) || defaultImg;

  const emit = defineEmits(['send']);
  const presetQuestionClick = (descr) => emit('send', descr);

  function getImageUrl(item) {
    if (item?.base64Data) return item.base64Data;
    return getFileAccessHttpUrl(item?.url || item);
  }

  function handlePreview(url) {
    createImgPreview({ imageList: [getImageUrl(url)], defaultWidth: 700, rememberState: true });
  }
</script>

<style lang="less" scoped>
  .chat {
    display: flex;
    margin-bottom: 1.5rem;
    &.self {
      flex-direction: row-reverse;
      .avatar { margin-right: 0; margin-left: 10px; }
      .msgArea { flex-direction: row-reverse; }
      .date { text-align: right; }
    }
  }
  .avatar {
    flex: none;
    margin-right: 10px;
    img { width: 34px; height: 34px; border-radius: 50%; overflow: hidden; }
  }
  .content {
    width: 90%;
    .date { color: #b4bbc4; font-size: 0.75rem; margin-bottom: 10px; }
    .msgArea { display: flex; }
  }
  .question {
    margin-top: 10px;
    border-radius: 0.375rem;
    padding: 0.5rem 0.75rem;
    background-color: #ffffff;
    font-size: 0.875rem;
    line-height: 1.25rem;
    cursor: pointer;
    border: 1px solid #f0f0f0;
    box-shadow: 0 2px 4px #e6e6e6;
  }
  .images {
    margin-bottom: 10px;
    flex-wrap: wrap;
    display: flex;
    gap: 10px;
    justify-content: end;
    .image {
      width: 120px; height: 80px; cursor: pointer;
      img { width: 100%; height: 100%; object-fit: cover; border-radius: 4px; }
    }
  }
  .retrieval {
    background-color: #f4f6f8;
    font-size: 0.875rem;
    line-height: 1.25rem;
    border-radius: 0.375rem;
    padding: 0.5rem 0.75rem;
    margin-bottom: 6px;
  }
  .retrieval:after {
    animation: blink 1s steps(5, start) infinite;
    color: #000; content: '_'; font-weight: 700; margin-left: 3px; vertical-align: baseline;
  }
  .card { width: 100%; }
  .ai-card {
    width: 98%; height: 100%; cursor: pointer;
    .ai-card-title {
      width: 100%; line-height: 20px; white-space: pre-line; overflow: hidden;
      display: -webkit-box; text-overflow: ellipsis; -webkit-box-orient: vertical;
      font-weight: 600; font-size: 18px; text-align: left; color: #191919; -webkit-line-clamp: 1;
    }
    .ai-card-img { margin-top: 10px; border-radius: 8px; display: flex; width: 100%; }
    .ai-card-desc {
      margin-top: 10px; width: 100%; font-size: 14px; font-weight: 400; line-height: 20px;
      white-space: pre-line; -webkit-box-orient: vertical; overflow: hidden; display: -webkit-box;
      text-overflow: ellipsis; text-align: left; color: #666; -webkit-line-clamp: 3;
    }
  }
  .html-body {
    width: 100%; max-width: 900px; min-height: 400px; height: auto; overflow: visible; margin-top: 10px;
    iframe {
      min-height: 400px; height: 600px; display: block;
      border: 1px solid #e8e8e8; border-radius: 4px; background: #fff;
    }
  }

  /* ===== events 包裹容器 ===== */
  .ev-wrap {
    display: block;
    width: 100%;
  }

  /* ===== thinking 折叠卡片 ===== */
  .ev-thinking {
    display: block;
    margin-bottom: 3px;
    border: 1px solid #e0d9f5;
    border-radius: 6px;
    overflow: hidden;
    background: #f5f3ff;
  }
  .ev-thinking-hd {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 6px 12px;
    cursor: pointer;
    user-select: none;
    &:hover { background: #ede9fc; }
  }
  .ev-thinking-icon { color: #7c3aed; flex-shrink: 0; }
  .ev-thinking-title {
    flex: 1;
    font-size: 12px;
    font-weight: 400;
    color: #6d28d9;
  }
  .ev-thinking-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #7c3aed;
    animation: blink 1s steps(2, start) infinite;
    flex-shrink: 0;
  }
  .ev-thinking-body {
    padding: 8px 14px;
    border-top: 1px solid #ede9fc;
    font-size: 12px;
    color: #5b21b6;
    background: #faf9ff;
    max-height: 300px;
    overflow-y: auto;
    :deep(.markdown-body) {
      background: transparent;
      font-size: 12px;
      padding: 0;
      color: #5b21b6;
    }
  }

  /* ===== 单个 step 折叠卡片 ===== */
  .ev-step {
    display: block;
    margin-bottom: 3px;
    border: 1px solid #e5e9ef;
    border-radius: 6px;
    overflow: hidden;
    background: #f7f8fa;
  }
  .ev-step-hd {
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 6px 12px;
    cursor: pointer;
    user-select: none;
    &:hover { background: #edf0f5; }
  }
  .ev-step-check {
    color: #10b981;
    flex-shrink: 0;
  }
  .ev-step-title {
    flex: 1;
    font-size: 12px;
    font-weight: 400;
    color: #64748b;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .ev-step-time {
    font-size: 11px;
    color: #94a3b8;
    flex-shrink: 0;
  }
  .ev-step-arrow {
    color: #94a3b8;
    transition: transform 0.2s;
    flex-shrink: 0;
    &.ev-step-arrow-up { transform: rotate(180deg); }
  }
  .ev-step-body {
    padding: 8px 14px;
    border-top: 1px solid #eef0f4;
    font-size: 12px;
    color: #64748b;
    background: #fafbfc;
    :deep(.markdown-body) {
      background: transparent;
      font-size: 12px;
      padding: 0;
    }
  }
  .ev-step-empty {
    color: #94a3b8;
    font-size: 12px;
    font-style: italic;
  }
  .ev-text {
    margin-top: 0;
    :deep(.textWrap) {
      margin-left: 0 !important;
      margin-top: 0 !important;
    }
  }

  @media (max-width: 600px) { .content { width: 100%; } }
</style>
