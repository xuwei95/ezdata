<template>
  <a-list item-layout="horizontal" :data-source="messageList">
    <template #loadMore>
      <div
        v-if="messageList && messageList.length > 0 && !loadEndStatus && !loadingMoreStatus"
        :style="{ textAlign: 'center', marginTop: '12px', height: '32px', lineHeight: '32px' }"
      >
        <a-button @click="onLoadMore">加载更多</a-button>
      </div>
      <div
        v-if="messageList && messageList.length > 0 && loadEndStatus"
        :style="{ textAlign: 'center', marginTop: '12px', height: '32px', lineHeight: '32px' }"
      >
        没有更多了
      </div>
    </template>

    <template #renderItem="{ item }">
      <a-list-item>
        <template #actions>
          <a-rate :value="item.star_flag == '1' ? 1 : 0" :count="1" @click="clickStar(item)" style="cursor: pointer" disabled />
        </template>

        <a-list-item-meta :description="item.create_time">
          <template #title>
            <div style="position: relative">
              <!--   <span style="display: inline-block; position: absolute; left: -16px">
                <exclamation-outlined v-if="noRead(item)" title="未读消息" style="color: red" />
              </span>-->

              <span>{{ getMsgCategory(item) }}</span>
              <span v-if="item.bus_type == 'bpm'" class="bpm-cuiban-content" v-html="item.msgContent"> </span>
              <a-tooltip v-else>
                <template #title>
                  <div v-html="item.msg_content"></div>
                </template>
                {{ item.title }}
              </a-tooltip>

              <a @click="showMessageDetail(item)" style="margin-left: 16px">查看详情</a>
            </div>
          </template>
          <template #avatar>
            <template v-if="item.bus_type == 'email'">
              <a-badge dot v-if="noRead(item)" class="msg-no-read">
                <a-avatar style="background: #79919d"><mail-outlined style="font-size: 16px" title="未读消息" /></a-avatar>
              </a-badge>
              <a-avatar v-else style="background: #79919d"><mail-outlined style="font-size: 16px" /></a-avatar>
            </template>

            <template v-else-if="item.bus_type == 'bpm_task'">
              <a-badge dot v-if="noRead(item)" class="msg-no-read">
                <a-avatar style="background: #79919d"><interaction-outlined style="font-size: 16px" title="未读消息" /></a-avatar>
              </a-badge>
              <a-avatar v-else style="background: #79919d"><interaction-outlined style="font-size: 16px" /></a-avatar>
            </template>

            <template v-else-if="item.bus_type == 'bpm'">
              <a-badge dot v-if="noRead(item)" class="msg-no-read">
                <a-avatar style="background: #79919d"><alert-outlined style="font-size: 16px" title="未读消息" /></a-avatar>
              </a-badge>
              <a-avatar v-else style="background: #79919d"><alert-outlined style="font-size: 16px" /></a-avatar>
            </template>

            <template v-else>
              <a-badge dot v-if="noRead(item)" class="msg-no-read">
                <a-avatar style="background: #79919d"><bell-filled style="font-size: 16px" title="未读消息" /></a-avatar>
              </a-badge>
              <a-avatar v-else style="background: #79919d"><bell-filled style="font-size: 16px" /></a-avatar>
            </template>
          </template>
        </a-list-item-meta>
      </a-list-item>
    </template>
  </a-list>
</template>

<script>
  import {
    FilterOutlined,
    CloseOutlined,
    BellFilled,
    ExclamationOutlined,
    MailOutlined,
    InteractionOutlined,
    AlertOutlined,
  } from '@ant-design/icons-vue';
  import { useSysMessage, useMessageHref } from './useSysMessage';

  export default {
    name: 'SysMessageList',
    components: {
      FilterOutlined,
      CloseOutlined,
      BellFilled,
      ExclamationOutlined,
      MailOutlined,
      InteractionOutlined,
      AlertOutlined,
    },
    props: {
      star: {
        type: Boolean,
        default: false,
      },
    },
    emits: ['close', 'detail'],
    setup(props, { emit }) {
      const { messageList, loadEndStatus, loadingMoreStatus, onLoadMore, noRead, getMsgCategory, searchParams, reset, loadData, updateStarMessage } =
        useSysMessage();

      function reload(params) {
        let { fromUser, rangeDateKey, rangeDate } = params;
        searchParams.fromUser = fromUser || '';
        searchParams.rangeDateKey = rangeDateKey || '';
        searchParams.rangeDate = rangeDate || [];
        if (props.star === true) {
          searchParams.starFlag = '1';
        } else {
          searchParams.starFlag = '';
        }
        reset();
        loadData();
      }

      function clickStar(item) {
        console.log(item);
        updateStarMessage(item);
        if (item.star_flag === '1') {
          item.star_flag = '0';
        } else {
          item.star_flag = '1';
        }
      }

      const { goPage } = useMessageHref(emit);

      function showMessageDetail(record) {
        record.read_flag = 1;
        console.log('ck666', record);
        goPage(record);
        emit('close', record.send_id);
      }

      return {
        messageList,
        loadEndStatus,
        loadingMoreStatus,
        onLoadMore,
        noRead,
        getMsgCategory,
        reload,
        clickStar,
        showMessageDetail,
      };
    },
  };
</script>

<style scoped lang="less">
  .msg-no-read {
    ::v-deep .ant-badge-dot {
      top: 5px;
      right: 3px;
    }
  }
  ::v-deep .bpm-cuiban-content p {
    display: inherit;
    margin-bottom: 0;
    margin-top: 0;
  }
</style>
