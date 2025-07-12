<template>
  <div class="chatWrap">
    <div class="content">
      <div class="main">
        <div id="scrollRef" ref="scrollRef" class="scrollArea">
          <template v-if="chatData.length">
            <div class="chatContentArea">
              <chatMessage
                v-for="(item, index) of chatData"
                ref="chatMessageRefs"
                :key="index"
                :date-time="item.dateTime"
                :text="item.text"
                :table_data="item.table_data"
                :html_data="item.html_data"
                :chat_flow="item.chat_flow"
                :inversion="item.inversion"
                :error="item.error"
                :loading="item.loading"
              />
            </div>
            <div v-if="loading" class="stopArea">
              <a-button type="primary" danger @click="handleStop" class="stopBtn">
                <svg
                  t="1706148514627"
                  class="icon"
                  viewBox="0 0 1024 1024"
                  version="1.1"
                  xmlns="http://www.w3.org/2000/svg"
                  p-id="5214"
                  width="18"
                  height="18"
                >
                  <path
                    d="M512 967.111111c-250.311111 0-455.111111-204.8-455.111111-455.111111s204.8-455.111111 455.111111-455.111111 455.111111 204.8 455.111111 455.111111-204.8 455.111111-455.111111 455.111111z m0-56.888889c221.866667 0 398.222222-176.355556 398.222222-398.222222s-176.355556-398.222222-398.222222-398.222222-398.222222 176.355556-398.222222 398.222222 176.355556 398.222222 398.222222 398.222222z"
                    fill="currentColor"
                    p-id="5215"
                  />
                  <path d="M341.333333 341.333333h341.333334v341.333334H341.333333z" fill="currentColor" p-id="5216" />
                </svg>
                <span>停止响应</span>
              </a-button>
            </div>
          </template>
          <template v-else>
            <div class="emptyArea">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                aria-hidden="true"
                role="img"
                class="mr-2 text-3xl iconify iconify--ri"
                width="1em"
                height="1em"
                viewBox="0 0 24 24"
              >
                <path
                  fill="currentColor"
                  d="M16 16a3 3 0 1 1 0 6a3 3 0 0 1 0-6M6 12a4 4 0 1 1 0 8a4 4 0 0 1 0-8m8.5-10a5.5 5.5 0 1 1 0 11a5.5 5.5 0 0 1 0-11"
                />
              </svg>
              <span>新建聊天</span>
            </div>
          </template>
        </div>
      </div>
      <div class="footer">
        <a-button type="text" class="delBtn" @click="handleDelSession">
          <svg
            t="1706504908534"
            class="icon"
            viewBox="0 0 1024 1024"
            version="1.1"
            xmlns="http://www.w3.org/2000/svg"
            p-id="1584"
            width="18"
            height="18"
          >
            <path
              d="M816.872727 158.254545h-181.527272V139.636364c0-39.563636-30.254545-69.818182-69.818182-69.818182h-107.054546c-39.563636 0-69.818182 30.254545-69.818182 69.818182v18.618181H207.127273c-48.872727 0-90.763636 41.890909-90.763637 93.09091s41.890909 90.763636 90.763637 90.763636h609.745454c51.2 0 90.763636-41.890909 90.763637-90.763636 0-51.2-41.890909-93.090909-90.763637-93.09091zM435.2 139.636364c0-13.963636 9.309091-23.272727 23.272727-23.272728h107.054546c13.963636 0 23.272727 9.309091 23.272727 23.272728v18.618181h-153.6V139.636364z m381.672727 155.927272H207.127273c-25.6 0-44.218182-20.945455-44.218182-44.218181 0-25.6 20.945455-44.218182 44.218182-44.218182h609.745454c25.6 0 44.218182 20.945455 44.218182 44.218182 0 23.272727-20.945455 44.218182-44.218182 44.218181zM835.490909 407.272727h-121.018182c-13.963636 0-23.272727 9.309091-23.272727 23.272728s9.309091 23.272727 23.272727 23.272727h97.745455V837.818182c0 39.563636-30.254545 69.818182-69.818182 69.818182h-37.236364V602.763636c0-13.963636-9.309091-23.272727-23.272727-23.272727s-23.272727 9.309091-23.272727 23.272727V907.636364h-118.690909V602.763636c0-13.963636-9.309091-23.272727-23.272728-23.272727s-23.272727 9.309091-23.272727 23.272727V907.636364H372.363636V602.763636c0-13.963636-9.309091-23.272727-23.272727-23.272727s-23.272727 9.309091-23.272727 23.272727V907.636364h-34.909091c-39.563636 0-69.818182-30.254545-69.818182-69.818182V453.818182H558.545455c13.963636 0 23.272727-9.309091 23.272727-23.272727s-9.309091-23.272727-23.272727-23.272728H197.818182c-13.963636 0-23.272727 9.309091-23.272727 23.272728V837.818182c0 65.163636 51.2 116.363636 116.363636 116.363636h451.490909c65.163636 0 116.363636-51.2 116.363636-116.363636V430.545455c0-13.963636-11.636364-23.272727-23.272727-23.272728z"
              fill="currentColor"
              p-id="1585"
            />
          </svg>
        </a-button>
<!--        <a-button type="text" class="contextBtn" :class="[usingContext && 'enabled']" @click="handleUsingContext">-->
<!--          <svg-->
<!--            xmlns="http://www.w3.org/2000/svg"-->
<!--            xmlns:xlink="http://www.w3.org/1999/xlink"-->
<!--            aria-hidden="true"-->
<!--            role="img"-->
<!--            class="iconify iconify&#45;&#45;ri"-->
<!--            width="20"-->
<!--            height="20"-->
<!--            viewBox="0 0 24 24"-->
<!--          >-->
<!--            <path-->
<!--              fill="currentColor"-->
<!--              d="M12 2c5.523 0 10 4.477 10 10s-4.477 10-10 10a9.956 9.956 0 0 1-4.708-1.175L2 22l1.176-5.29A9.956 9.956 0 0 1 2 12C2 6.477 6.477 2 12 2m0 2a8 8 0 0 0-8 8c0 1.335.326 2.618.94 3.766l.35.654l-.656 2.946l2.948-.654l.653.349A7.955 7.955 0 0 0 12 20a8 8 0 1 0 0-16m1 3v5h4v2h-6V7z"-->
<!--            />-->
<!--          </svg>-->
<!--        </a-button>-->
        <a-button type="text" class="configBtn" @click="configVisible = true">
          <svg
            t="1723358891149"
            class="icon"
            viewBox="0 0 1024 1024"
            version="1.1"
            xmlns="http://www.w3.org/2000/svg"
            p-id="4746"
            width="20"
            height="20"
          >
            <path
              d="M508.472 383.852c67.346 0 122.15 54.805 122.15 122.15s-54.804 122.15-122.15 122.15-122.15-54.805-122.15-122.15 54.805-122.15 122.15-122.15m0-54.289c-97.448 0-176.439 78.99-176.439 176.44s78.99 176.438 176.44 176.438 176.438-78.99 176.438-176.439-78.99-176.439-176.439-176.439m436.186 284.16c7.758-33.082 11.71-67.147 11.71-101.722 0-34.575-3.952-68.64-11.71-101.722-3.425-14.602-18.038-23.664-32.64-20.24-14.603 3.425-23.665 18.039-20.24 32.641 6.806 29.024 10.276 58.927 10.276 89.321s-3.47 60.297-10.276 89.32c-3.425 14.603 5.637 29.217 20.24 32.641 14.602 3.425 29.215-5.637 32.64-20.24z m-32.086 20.848c1.718 0 3.155 0.026 4.466 0.083 14.985 0.652 27.66-10.967 28.312-25.952 0.651-14.984-10.968-27.66-25.952-28.311a155.244 155.244 0 0 0-6.826-0.134c-14.999 0-27.157 12.158-27.157 27.157 0 14.998 12.158 27.157 27.157 27.157z m-88.67 163.374c-11.086-17.03-17.072-36.87-17.072-57.632 0-58.4 47.342-105.742 105.742-105.742 14.998 0 27.157-12.159 27.157-27.157 0-14.999-12.159-27.158-27.157-27.158-88.397 0-160.057 71.66-160.057 160.057 0 31.37 9.088 61.489 25.87 87.265 8.183 12.57 25.006 16.126 37.576 7.942 12.57-8.183 16.125-25.006 7.942-37.575z m-183.785 139.66c67.576-20.297 129.146-56.495 179.854-105.271 10.809-10.398 11.143-27.59 0.745-38.4s-27.59-11.142-38.4-0.744c-44.525 42.83-98.555 74.595-157.823 92.395-14.364 4.314-22.512 19.457-18.197 33.821 4.314 14.365 19.456 22.512 33.821 18.198z m-223.82-14.449c17.308-36.785 54.332-60.762 95.704-60.762 41.38 0 78.426 23.984 95.731 60.762 6.386 13.572 22.564 19.397 36.135 13.012 13.572-6.386 19.397-22.564 13.012-36.135C630.696 844.386 574.615 808.08 512 808.08c-62.61 0-118.666 36.302-144.85 91.953-6.386 13.57-0.56 29.75 13.01 36.135 13.572 6.385 29.75 0.56 36.136-13.012zM205.25 833.495c50.49 48.178 111.615 83.952 178.655 104.107 14.364 4.318 29.508-3.825 33.826-18.189 4.319-14.363-3.825-29.508-18.188-33.826-58.81-17.68-112.458-49.078-156.796-91.387-10.851-10.354-28.041-9.952-38.396 0.9s-9.952 28.04 0.9 38.395zM113.276 634.57c58.4 0 105.742 47.342 105.742 105.742 0 21.123-6.193 41.291-17.634 58.497-8.304 12.49-4.912 29.347 7.577 37.652 12.49 8.304 29.347 4.912 37.652-7.577 17.32-26.047 26.72-56.662 26.72-88.572 0-88.397-71.66-160.056-160.057-160.056-14.998 0-27.157 12.159-27.157 27.157s12.159 27.157 27.157 27.157z m-5.974 0.15c1.83-0.101 3.809-0.15 5.974-0.15 14.999 0 27.158-12.159 27.158-27.157 0-14.999-12.16-27.158-27.158-27.158-3.112 0-6.073 0.073-8.954 0.231-14.976 0.823-26.45 13.63-25.627 28.607 0.823 14.976 13.63 26.45 28.607 25.626zM79.37 410.202c-7.77 33.163-11.736 67.251-11.736 101.798S71.6 580.636 79.37 613.8c3.422 14.603 18.034 23.667 32.637 20.246 14.603-3.422 23.667-18.034 20.246-32.637-6.822-29.115-10.305-59.046-10.305-89.407 0-30.361 3.483-60.292 10.305-89.407 3.422-14.603-5.643-29.215-20.246-32.637-14.603-3.421-29.215 5.643-32.637 20.246z m33.906-20.772c-2.165 0-4.144-0.049-5.974-0.15-14.977-0.822-27.784 10.651-28.607 25.627-0.823 14.976 10.65 27.784 25.627 28.607 2.88 0.158 5.842 0.23 8.954 0.23 14.999 0 27.158-12.158 27.158-27.157 0-14.998-12.16-27.157-27.158-27.157z m88.108-164.239c11.443 17.208 17.634 37.377 17.634 58.524 0 58.393-47.335 105.715-105.742 105.715-14.998 0-27.157 12.159-27.157 27.157 0 14.999 12.159 27.158 27.157 27.158 88.401 0 160.057-71.636 160.057-160.03 0-31.933-9.398-62.548-26.72-88.598-8.305-12.49-25.162-15.882-37.652-7.577s-15.881 25.162-7.577 37.651zM383.905 86.4c-67.04 20.155-128.166 55.93-178.655 104.107-10.85 10.355-11.253 27.545-0.899 38.396 10.355 10.851 27.545 11.254 38.396 0.9 44.338-42.31 97.986-73.708 156.796-91.388 14.363-4.318 22.507-19.463 18.188-33.826-4.318-14.364-19.462-22.507-33.826-18.189z m223.827 14.446c-17.303 36.775-54.348 60.762-95.704 60.762-41.396 0-78.421-23.974-95.73-60.762-6.386-13.572-22.565-19.397-36.136-13.011-13.571 6.385-19.397 22.564-13.01 36.135 26.186 55.654 82.244 91.952 144.877 91.952 62.59 0 118.67-36.31 144.85-91.952 6.385-13.572 0.56-29.75-13.011-36.135-13.572-6.386-29.75-0.56-36.136 13.01z m212.233 90.817c-50.705-48.745-112.27-84.94-179.838-105.262-14.363-4.32-29.508 3.822-33.828 18.185s3.822 29.508 18.185 33.828c59.273 17.827 113.31 49.596 157.839 92.404 10.812 10.395 28.004 10.056 38.399-0.757s10.055-28.004-0.757-38.398z m92.607 197.768c-58.407 0-105.742-47.322-105.742-105.715 0-20.786 5.985-40.627 17.073-57.658 8.183-12.57 4.627-29.393-7.942-37.576-12.57-8.184-29.393-4.628-37.576 7.942-16.784 25.78-25.87 55.9-25.87 87.292 0 88.394 71.656 160.03 160.057 160.03 14.998 0 27.157-12.159 27.157-27.158 0-14.998-12.159-27.157-27.157-27.157z m4.466-0.083c-1.31 0.057-2.748 0.083-4.466 0.083-14.999 0-27.157 12.159-27.157 27.158 0 14.998 12.158 27.157 27.157 27.157 2.451 0 4.652-0.04 6.825-0.134 14.985-0.652 26.604-13.327 25.952-28.312-0.651-14.984-13.326-26.603-28.31-25.952z"
              p-id="4747"
            />
          </svg>
        </a-button>
        <a-textarea
          ref="inputRef"
          v-model:value="prompt"
          :autoSize="{ minRows: 1, maxRows: 6 }"
          :placeholder="placeholder"
          @press-enter="handleEnter"
          autofocus
        />
        <a-button
          @click="
            () => {
              handleSubmit();
            }
          "
          :disabled="loading"
          type="primary"
          class="sendBtn"
        >
          <svg
            t="1706147858151"
            class="icon"
            viewBox="0 0 1024 1024"
            version="1.1"
            xmlns="http://www.w3.org/2000/svg"
            p-id="4237"
            width="1em"
            height="1em"
          >
            <path
              d="M865.28 202.5472c-17.1008-15.2576-41.0624-19.6608-62.5664-11.5712L177.7664 427.1104c-23.2448 8.8064-38.5024 29.696-39.6288 54.5792-1.1264 24.8832 11.9808 47.104 34.4064 58.0608l97.5872 47.7184c4.5056 2.2528 8.0896 6.0416 9.9328 10.6496l65.4336 161.1776c7.7824 19.1488 24.4736 32.9728 44.7488 37.0688 20.2752 4.096 41.0624-2.1504 55.6032-16.7936l36.352-36.352c6.4512-6.4512 16.5888-7.8848 24.576-3.3792l156.5696 88.8832c9.4208 5.3248 19.8656 8.0896 30.3104 8.0896 8.192 0 16.4864-1.6384 24.2688-5.0176 17.8176-7.68 30.72-22.8352 35.4304-41.6768l130.7648-527.1552c5.5296-22.016-1.7408-45.2608-18.8416-60.416z m-20.8896 50.7904L713.5232 780.4928c-1.536 6.2464-5.8368 11.3664-11.776 13.9264s-12.5952 2.1504-18.2272-1.024L526.9504 704.512c-9.4208-5.3248-19.8656-7.9872-30.208-7.9872-15.9744 0-31.744 6.144-43.52 17.92l-36.352 36.352c-3.8912 3.8912-8.9088 5.9392-14.2336 6.0416l55.6032-152.1664c0.512-1.3312 1.2288-2.56 2.2528-3.6864l240.3328-246.1696c8.2944-8.4992-2.048-21.9136-12.3904-16.0768L301.6704 559.8208c-4.096-3.584-8.704-6.656-13.6192-9.1136L190.464 502.9888c-11.264-5.5296-11.5712-16.1792-11.4688-19.3536 0.1024-3.1744 1.536-13.824 13.2096-18.2272L817.152 229.2736c10.4448-3.9936 18.0224 1.3312 20.8896 3.8912 2.8672 2.4576 9.0112 9.3184 6.3488 20.1728z"
              p-id="4238"
              fill="currentColor"
            />
          </svg>
        </a-button>
      </div>
    </div>
    <!-- Modal 组件 -->
    <a-modal v-model:visible="configVisible" title="对话配置" @ok="handleConfigOk">
      <ChatConfigForm v-model="chatConfigFormState" />
    </a-modal>
  </div>
</template>

<script setup lang="ts">
  import type { Ref } from 'vue';
  import { computed, ref, createVNode, onUnmounted, onMounted } from 'vue';
  import { useScroll } from '../hooks/useScroll';
  import { EventSourcePolyfill } from 'event-source-polyfill';
  import { ConfigEnum } from '/@/enums/httpEnum';
  import { getToken } from '/@/utils/auth';
  import { getAppEnvConfig } from '/@/utils/env';
  import chatMessage from './chatMessage.vue';
  import { DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons-vue';
  import { Modal } from 'ant-design-vue';
  import '../style/github-markdown.less';
  import '../style/highlight.less';
  import '../style/style.less';
  import ChatConfigForm from './ChatConfigForm.vue';

  const props = defineProps(['chatData', 'uuid', 'dataSource', 'chatConfig']);
  const { scrollRef, scrollToBottom, scrollToBottomIfAtBottom } = useScroll();
  const prompt = ref<string>('');
  const loading = ref<boolean>(false);
  const inputRef = ref<Ref | null>(null);
  // 当前模式下, 发送消息会携带之前的聊天记录
  const usingContext = ref<any>(true);
  const uuid = computed(() => {
    return props.uuid;
  });
  const configVisible = ref(false);
  const chatConfigFormState = ref(props.chatConfig);
  const emit = defineEmits(['updateChatConfig']);
  let evtSource: any = null;
  const { VITE_GLOB_API_URL } = getAppEnvConfig();
  const conversationList = computed(() => props.chatData.filter((item) => !item.inversion && !!item.conversationOptions));
  const placeholder = computed(() => {
    return '来说点什么吧...（Shift + Enter = 换行）';
  });
  const chatMessageRefs = ref([]); // 用于存储所有 ChatMessage 组件的引用
  function handleEnter(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }
  function handleSubmit() {
    onConversation();
  }
  async function onConversation() {
    let message = prompt.value;
    if (loading.value) return;
    if (!message || message.trim() === '') return;

    loading.value = true;
    prompt.value = '';

    if (props.chatData.length == 0) {
      const findItem = props.dataSource.history.find((item) => item.uuid === uuid.value);
      if (findItem && findItem.title == '新建聊天') {
        findItem.title = message;
      }
    }
    addChat(uuid.value, {
      dateTime: new Date().toLocaleString(),
      text: message,
      inversion: true,
      error: false,
      conversationOptions: null,
      requestOptions: { prompt: message, options: null },
    });
    scrollToBottom();

    let options: any = {};
    const lastContext = conversationList.value[conversationList.value.length - 1]?.conversationOptions;
    if (lastContext && usingContext.value) options = { ...lastContext };
    addChat(uuid.value, {
      dateTime: new Date().toLocaleString(),
      text: '思考中...',
      loading: true,
      inversion: false,
      error: false,
      conversationOptions: null,
      requestOptions: { prompt: message, options: { ...options } },
    });
    scrollToBottom();

    const initEventSource = () => {
      let lastText = '';
      let table_data = [];
      let html_data = '';
      let chat_flow = [];
      if (typeof EventSource !== 'undefined') {
        const token = getToken();
        evtSource = new EventSourcePolyfill(
          `${VITE_GLOB_API_URL}/llm/chat?message=${message}${options.parentMessageId ? '&topicId=' + options.parentMessageId : ''}${
            chatConfigFormState.value ? '&chatConfig=' + JSON.stringify(chatConfigFormState.value) : ''
          }`,
          {
            withCredentials: true,
            headers: {
              Authorization: 'Bearer ' + token,
            },
          }
        ); // 后端接口，要配置允许跨域属性
        // 与事件源的连接刚打开时触发
        evtSource.onopen = function (e) {
          console.log(e);
        };
        // 当从事件源接收到数据时触发
        evtSource.onmessage = function (e) {
          const data = e.data;
          // console.log(e);
          if (data === '[DONE]') {
            updateChatSome(uuid, props.chatData.length - 1, { loading: false });
            const lastMessage = chatMessageRefs.value[chatMessageRefs.value.length - 1];
            setTimeout(() => {
              lastMessage.handleData();
            }, 100);
            scrollToBottom();
            handleStop();
            evtSource.close(); // 关闭连接
          } else {
            try {
              const _data = JSON.parse(data);
              const content = _data.content;
              const _type = _data.type;
              if (content != undefined) {
                if (_type == 'text') {
                  // 纯文本，直接添加
                  lastText += content;
                } else if (_type == 'data') {
                  // 表格数据
                  table_data = content;
                } else if (_type == 'html') {
                  // html数据
                  html_data = content;
                } else if (_type == 'flow') {
                  // 处理流程
                  chat_flow.push(content);
                }
                console.log(11111, chat_flow);
                updateChat(uuid.value, props.chatData.length - 1, {
                  dateTime: new Date().toLocaleString(),
                  text: lastText,
                  table_data: table_data,
                  html_data: html_data,
                  chat_flow: chat_flow,
                  inversion: false,
                  error: false,
                  loading: true,
                  conversationOptions:
                    e.lastEventId == '[ERR]'
                      ? null
                      : {
                          conversationId: data.conversationId,
                          parentMessageId: e.lastEventId,
                        },
                  requestOptions: { prompt: message, options: { ...options } },
                });
                scrollToBottom();
              } else {
                updateChatSome(uuid.value, props.chatData.length - 1, { loading: false });
                scrollToBottom();
                handleStop();
              }
            } catch (error) {
              updateChatSome(uuid.value, props.chatData.length - 1, { loading: false });
              scrollToBottom();
              handleStop();
              evtSource.close(); // 关闭连接
            }
          }
        };
        // 与事件源的连接无法打开时触发
        evtSource.onerror = function (e) {
          // console.log(e);
          if (e.error?.message || e.statusText) {
            updateChat(uuid.value, props.chatData.length - 1, {
              dateTime: new Date().toLocaleString(),
              text: e.error?.message ?? e.statusText,
              inversion: false,
              error: false,
              loading: true,
              conversationOptions: null,
              requestOptions: { prompt: message, options: { ...options } },
            });
            scrollToBottom();
          }
          evtSource.close(); // 关闭连接
          updateChatSome(uuid.value, props.chatData.length - 1, { loading: false });
          handleStop();
        };
      } else {
        console.log('当前浏览器不支持使用EventSource接收服务器推送事件!');
      }
    };
    initEventSource();
  }
  onUnmounted(() => {
    evtSource?.close();
    updateChatSome(uuid.value, props.chatData.length - 1, { loading: false });
  });
  const addChat = (uuid, data) => {
    props.chatData.push({ ...data });
  };
  const updateChat = (uuid, index, data) => {
    props.chatData.splice(index, 1, data);
  };
  const updateChatSome = (uuid, index, data) => {
    props.chatData[index] = { ...props.chatData[index], ...data };
  };
  const handleConfigOk = () => {
    emit('updateChatConfig', chatConfigFormState.value);
    configVisible.value = false; // 隐藏 Modal
  };
  // 清空会话
  const handleDelSession = () => {
    Modal.confirm({
      title: '清空会话',
      icon: createVNode(ExclamationCircleOutlined),
      content: '是否清空会话?',
      closable: true,
      okText: '确定',
      cancelText: '取消',
      async onOk() {
        try {
          return await new Promise<void>((resolve) => {
            props.chatData.length = 0;
            resolve();
          });
        } catch {
          return console.log('Oops errors!');
        }
      },
    });
  };
  // 停止响应
  const handleStop = () => {
    if (loading.value) {
      loading.value = false;
    }
    if (evtSource) {
      evtSource?.close();
      updateChatSome(uuid, props.chatData.length - 1, { loading: false });
    }
  };
  // // 是否使用上下文
  // const handleUsingContext = () => {
  //   usingContext.value = !usingContext.value;
  //   if (usingContext.value) {
  //     message.success('当前模式下, 发送消息会携带之前的聊天记录');
  //   } else {
  //     message.warning('当前模式下, 发送消息不会携带之前的聊天记录');
  //   }
  // };
  onMounted(() => {
    scrollToBottom();
  });
</script>

<style lang="less" scoped>
  .chatWrap {
    width: 100%;
    height: 100%;
    padding: 20px;
    .content {
      height: 100%;
      width: 100%;
      background: #fff;
      display: flex;
      flex-direction: column;
    }
  }
  .main {
    flex: 1;
    min-height: 0;
    .scrollArea {
      overflow-y: auto;
      height: 100%;
    }
    .chatContentArea {
      padding: 10px;
    }
  }
  .emptyArea {
    display: flex;
    justify-content: center;
    align-items: center;
    color: #d4d4d4;
  }
  .stopArea {
    display: flex;
    justify-content: center;
    padding: 10px 0;
    .stopBtn {
      display: flex;
      justify-content: center;
      align-items: center;
      svg {
        margin-right: 5px;
      }
    }
  }
  .footer {
    display: flex;
    align-items: center;
    padding: 6px 16px;
    .ant-input {
      margin: 0 16px;
    }
    .ant-input,
    .ant-btn {
      height: 36px;
    }
    textarea.ant-input {
      padding-top: 6px;
      padding-bottom: 6px;
    }
    .contextBtn,
    .delBtn {
      padding: 0;
      width: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .delBtn {
      margin-right: 8px;
    }
    .configBtn {
      padding: 0;
      width: 40px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .configBtn {
      margin-right: 8px;
    }
    .contextBtn {
      color: #a8071a;
      &.enabled {
        color: @primary-color;
      }
      font-size: 18px;
    }
    .sendBtn {
      padding: 0 10px;
      font-size: 22px;
      display: flex;
      align-items: center;
    }
  }
</style>
