<template>
  <!-- 矩阵模式:栅格拖拽/挤压(grid-layout-plus) -->
  <GridLayout
    v-if="mode !== 'free'"
    :layout="layout"
    :col-num="cols"
    :row-height="RH"
    :is-draggable="editable"
    :is-resizable="editable"
    :margin="[8, 8]"
    :vertical-compact="true"
    :use-css-transforms="true"
    @layout-updated="onLayoutUpdated"
  >
    <GridItem v-for="item in layout" :key="item.i" :x="item.x" :y="item.y" :w="item.w" :h="item.h" :i="item.i">
      <div class="dg-item" :class="{ editable, selected: editable && item.i === selectedId }"
        @click="editable && $emit('select-comp', item.i)" @dblclick="editable && $emit('edit-comp', item.i)">
        <div v-if="editable" class="dg-bar">
          <span class="dg-title">{{ compTitle(map[item.i]) }}</span>
          <span class="dg-bar-ops">
            <el-button link size="small" type="primary" icon="Setting" :title="$t('配置')" @click.stop="$emit('edit-comp', item.i)" />
            <el-button link size="small" type="danger" icon="Delete" :title="$t('删除')" @click.stop="$emit('remove-comp', item.i)" />
          </span>
        </div>
        <div class="dg-body">
          <DashComponent v-if="map[item.i]" :comp="map[item.i]" :params="chartParams" :height="itemH(item)" :silent="!editable" />
        </div>
      </div>
    </GridItem>
  </GridLayout>

  <!-- 自由模式(大屏):固定设计尺寸 + 整体等比缩放(对齐 DataEase);editable 时可拖动/缩放 -->
  <div v-else ref="freeVp" class="dg-free-vp">
    <div class="dg-free-holder" :style="{ width: canvasW * scale + 'px', height: canvasH * scale + 'px' }">
      <div class="dg-free" :style="{ width: canvasW + 'px', height: canvasH + 'px', background: canvas.background || '#0b1a2b', transform: `scale(${scale})`, transformOrigin: 'top left' }">
        <div v-for="c in components" :key="c.id" class="dg-abs" :class="{ editable, selected: editable && c.id === selectedId }"
          :style="{ left: (c.pos && c.pos.x || 0) + 'px', top: (c.pos && c.pos.y || 0) + 'px', width: (c.pos && c.pos.w || 300) + 'px', height: (c.pos && c.pos.h || 200) + 'px', zIndex: (c.pos && c.pos.z) || 1 }"
          @mousedown="editable && startDrag($event, c)" @click.stop="editable && $emit('select-comp', c.id)" @dblclick.stop="editable && $emit('edit-comp', c.id)">
          <DashComponent :comp="c" :params="chartParams" :height="((c.pos && c.pos.h) || 200) - 4" :dark="isDark" :silent="!editable" />
          <template v-if="editable">
            <span class="dg-ops">
              <el-button link type="primary" icon="Setting" :title="$t('配置')" @mousedown.stop @click.stop="$emit('edit-comp', c.id)" />
              <el-button link type="danger" icon="Delete" :title="$t('删除')" @mousedown.stop @click.stop="$emit('remove-comp', c.id)" />
            </span>
            <span class="dg-resizer" @mousedown.stop.prevent="startResize($event, c)" @click.stop />
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup name="DashCanvas">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { GridLayout, GridItem } from 'grid-layout-plus'
import DashComponent from './DashComponent.vue'

const props = defineProps({
  components: { type: Array, default: () => [] },
  canvas: { type: Object, default: () => ({ mode: 'matrix', cols: 24 }) },
  editable: { type: Boolean, default: false },
  selectedId: { type: String, default: '' },
  rowHeight: { type: Number, default: 40 },
  chartParams: { type: Object, default: null }, // 全局筛选值(联动,P2)
})
const emit = defineEmits(['update:components', 'select-comp', 'remove-comp', 'edit-comp'])

const mode = computed(() => props.canvas.mode || 'matrix')
const cols = computed(() => props.canvas.cols || 24)
const canvasW = computed(() => props.canvas.width || 1920)
const canvasH = computed(() => props.canvas.height || 1080)
// 自由模式(大屏)且背景为深色时,图表走透明底 + 明色轴/文字
function isLightColor(c) {
  const m = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec((c || '').trim())
  if (!m) return false // 非 hex(默认深色大屏)按深色处理
  let h = m[1]; if (h.length === 3) h = h.split('').map((x) => x + x).join('')
  const r = parseInt(h.slice(0, 2), 16), g = parseInt(h.slice(2, 4), 16), b = parseInt(h.slice(4, 6), 16)
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.6
}
const isDark = computed(() => mode.value === 'free' && !isLightColor(props.canvas.background || '#0b1a2b'))
const RH = computed(() => props.rowHeight)
const map = computed(() => Object.fromEntries((props.components || []).map((c) => [c.id, c])))

// ---- 大屏整体等比缩放(ResizeObserver 按容器算,编辑器/预览/纯图页统一)----
const freeVp = ref(null)
const scale = ref(1)
let ro = null
function calcScale() {
  if (mode.value !== 'free' || !freeVp.value) return
  const vpW = freeVp.value.clientWidth, vpH = freeVp.value.clientHeight
  if (!vpW || !vpH) return
  scale.value = Math.min(vpW / canvasW.value, vpH / canvasH.value) || 1
}
onMounted(() => {
  ro = new ResizeObserver(() => calcScale())
  if (freeVp.value) ro.observe(freeVp.value)
  calcScale()
})
onBeforeUnmount(() => { if (ro) ro.disconnect() })
watch([mode, canvasW, canvasH], () => calcScale())

// ---- 自由模式:拖动 / 缩放(位移除以 scale 修正)----
function startDrag(e, c) {
  if (e.target.classList && e.target.classList.contains('dg-resizer')) return
  emit('select-comp', c.id)
  const sx = e.clientX, sy = e.clientY
  const ox = (c.pos && c.pos.x) || 0, oy = (c.pos && c.pos.y) || 0
  const onMove = (ev) => {
    c.pos = { ...(c.pos || {}), x: Math.round(ox + (ev.clientX - sx) / scale.value), y: Math.round(oy + (ev.clientY - sy) / scale.value) }
  }
  const onUp = () => { document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); emit('update:components', [...props.components]) }
  document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp)
}
function startResize(e, c) {
  emit('select-comp', c.id)
  const sx = e.clientX, sy = e.clientY
  const ow = (c.pos && c.pos.w) || 300, oh = (c.pos && c.pos.h) || 200
  const onMove = (ev) => {
    c.pos = { ...(c.pos || {}), w: Math.max(80, Math.round(ow + (ev.clientX - sx) / scale.value)), h: Math.max(60, Math.round(oh + (ev.clientY - sy) / scale.value)) }
  }
  const onUp = () => { document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp); emit('update:components', [...props.components]) }
  document.addEventListener('mousemove', onMove); document.addEventListener('mouseup', onUp)
}

// ---- 矩阵栅格布局(与 components.pos 同步)----
const layout = ref([])
function sync() {
  layout.value = (props.components || []).map((c) => ({
    i: c.id, x: (c.pos && c.pos.x) || 0, y: (c.pos && c.pos.y) || 0,
    w: (c.pos && c.pos.w) || 8, h: (c.pos && c.pos.h) || 6,
  }))
}
watch(() => props.components, sync, { immediate: true })

// 拖拽/缩放后:把栅格位置写回 components.pos 并回传。仅当位置真的变化时才 emit(防自循环)。
function onLayoutUpdated(newLayout) {
  const byId = Object.fromEntries((newLayout || layout.value).map((l) => [l.i, l]))
  let changed = false
  const updated = (props.components || []).map((c) => {
    const l = byId[c.id]
    if (!l) return c
    const p = c.pos || {}
    if (p.x === l.x && p.y === l.y && p.w === l.w && p.h === l.h) return c
    changed = true
    return { ...c, pos: { ...p, x: l.x, y: l.y, w: l.w, h: l.h } }
  })
  if (changed) emit('update:components', updated)
}

function itemH(item) {
  return Math.max(60, item.h * RH.value - (props.editable ? 34 : 10))
}
function compTitle(c) {
  if (!c) return ''
  return (c.props && c.props.title) || { chart: '图表', text: '文本', image: '图片', filter: '筛选', tab: 'Tab' }[c.type] || c.type
}
</script>

<style scoped>
.dg-item { width: 100%; height: 100%; display: flex; flex-direction: column; border: 1px solid #ebeef5; border-radius: 6px; background: #fff; box-sizing: border-box; overflow: hidden; }
.dg-item.editable { cursor: move; }
.dg-item.selected { border-color: var(--el-color-primary); box-shadow: 0 0 0 2px var(--el-color-primary-light-5); }
.dg-bar { display: flex; align-items: center; justify-content: space-between; padding: 2px 6px; height: 26px; border-bottom: 1px solid #f0f2f5; background: #fafcff; font-size: 12px; }
.dg-title { color: #606266; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.dg-body { flex: 1; min-height: 0; }

/* 矩阵:让 grid 自带的缩放手柄更明显(hover 显示右下角三角) */
:deep(.vgl-item__resizer) { opacity: 0; }
.dg-item:hover ~ :deep(.vgl-item__resizer), :deep(.vgl-item:hover .vgl-item__resizer) { opacity: 1; }
/* 矩阵:拖动时的落位占位符 —— 默认是刺眼的红色,改成柔和的半透明主色虚框 */
:deep(.vgl-item--placeholder) { background: var(--el-color-primary) !important; opacity: 0.12 !important; border: 1px dashed var(--el-color-primary); border-radius: 6px; }

/* 自由模式(大屏):safe center —— 缩放画布放不下时上对齐(不裁掉顶部),放得下时居中 */
.dg-free-vp { width: 100%; height: 100%; display: flex; align-items: safe center; justify-content: safe center; overflow: auto; padding: 8px; box-sizing: border-box; }
.dg-free-holder { position: relative; flex: none; }
.dg-free { position: relative; overflow: hidden; }
.dg-abs { position: absolute; overflow: hidden; }
.dg-abs.editable { cursor: move; outline: 1px dashed rgba(255, 255, 255, 0.25); }
.dg-abs.selected { outline: 2px solid var(--el-color-primary); z-index: 999 !important; }
.dg-bar-ops { display: flex; align-items: center; gap: 2px; }
.dg-ops { position: absolute; top: 2px; right: 4px; z-index: 3; display: flex; gap: 2px; opacity: 0; background: rgba(0,0,0,.25); border-radius: 4px; padding: 0 2px; }
.dg-abs:hover .dg-ops, .dg-abs.selected .dg-ops { opacity: 1; }
.dg-resizer { position: absolute; right: 0; bottom: 0; width: 14px; height: 14px; cursor: nwse-resize; z-index: 4;
  background: linear-gradient(135deg, transparent 50%, var(--el-color-primary) 50%); opacity: 0; }
.dg-abs:hover .dg-resizer, .dg-abs.selected .dg-resizer { opacity: 1; }
</style>
