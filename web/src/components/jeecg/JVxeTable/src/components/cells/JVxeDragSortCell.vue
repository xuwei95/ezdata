<template>
  <div class="j-vxe-drag-box">
    <a-dropdown :trigger="['click']">
      <span
        ><span class="drag-btn"> <Icon icon="mi:drag" /> </span
      ></span>
      <template #overlay>
        <a-menu>
          <a-menu-item key="0" :disabled="disabledMoveUp" @click="handleRowMoveUp">向上移</a-menu-item>
          <a-menu-item key="1" :disabled="disabledMoveDown" @click="handleRowMoveDown">向下移</a-menu-item>
          <a-menu-divider />
          <a-menu-item key="3" @click="handleRowInsertDown">插入一行</a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>
  </div>
</template>

<script lang="ts">
  import { computed, defineComponent } from 'vue';
  import { Icon } from '/@/components/Icon';
  import { JVxeComponent } from '/@/components/jeecg/JVxeTable/types';
  import { useJVxeComponent, useJVxeCompProps } from '/@/components/jeecg/JVxeTable/hooks';

  export default defineComponent({
    name: 'JVxeDragSortCell',
    components: { Icon },
    props: useJVxeCompProps(),
    setup(props: JVxeComponent.Props) {
      const { rowIndex, fullDataLength, trigger } = useJVxeComponent(props);

      const disabledMoveUp = computed(() => rowIndex.value === 0);
      const disabledMoveDown = computed(() => rowIndex.value === fullDataLength.value - 1);

      /** 向上移 */
      function handleRowMoveUp() {
        if (!disabledMoveUp.value) {
          trigger('rowResort', {
            oldIndex: rowIndex.value,
            newIndex: rowIndex.value - 1,
          });
        }
      }

      /** 向下移 */
      function handleRowMoveDown() {
        if (!disabledMoveDown.value) {
          trigger('rowResort', {
            oldIndex: rowIndex.value,
            newIndex: rowIndex.value + 1,
          });
        }
      }

      /** 插入一行 */
      function handleRowInsertDown() {
        trigger('rowInsertDown', rowIndex.value);
      }

      return {
        disabledMoveUp,
        disabledMoveDown,
        handleRowMoveUp,
        handleRowMoveDown,
        handleRowInsertDown,
      };
    },
    // 【组件增强】注释详见：JVxeComponent.Enhanced
    enhanced: {
      // 【功能开关】
      switches: {
        editRender: false,
      },
    } as JVxeComponent.EnhancedPartial,
  });
</script>

<style lang="less">
  .j-vxe-drag-box {
    .app-iconify {
      cursor: move;
    }
  }

  .vxe-table--fixed-wrapper {
    .j-vxe-drag-box {
      .app-iconify {
        cursor: pointer;
      }
    }
  }
</style>
