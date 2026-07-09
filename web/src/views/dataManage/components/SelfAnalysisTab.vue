<template>
  <div class="self-analysis">
    <div class="bar">
      <span class="tip">拖拽字段即可自助分析(PyGWalker)。默认取前 1 万行,超大模型请先在模型层预聚合。</span>
      <el-button size="small" icon="Refresh" :loading="loading" @click="load">重新加载</el-button>
    </div>
    <div ref="wrap" class="frame-wrap" v-loading="loading" element-loading-text="生成分析视图中…">
      <iframe
        v-if="html"
        :srcdoc="html"
        class="pyg-frame"
        :style="{ height: frameH + 'px' }"
        sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
      />
      <el-empty v-else-if="!loading" :description="err || '暂无数据'" />
    </div>
  </div>
</template>

<script setup name="SelfAnalysisTab">
import { ref, watch, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { walkerHtml } from '@/api/dataManage/data'

const props = defineProps({ model: { type: Object, required: true } })

const html = ref('')
const loading = ref(false)
const err = ref('')
const wrap = ref()
const frameH = ref(500)

async function computeH() {
  await nextTick()
  const top = wrap.value ? wrap.value.getBoundingClientRect().top : 240
  frameH.value = Math.max(360, Math.floor(window.innerHeight - top - 16))
}

async function load() {
  if (!props.model || !props.model.id) return
  loading.value = true
  err.value = ''
  html.value = ''
  try {
    const res = await walkerHtml(props.model.id, {})
    html.value = res.data.html || ''
    await computeH()
  } catch (e) {
    err.value = e?.msg || e?.message || '生成失败'
    ElMessage.error(err.value)
  } finally {
    loading.value = false
  }
}

// 切换模型时重载;首次进入也加载
watch(() => props.model && props.model.id, load)
onMounted(() => {
  load()
  window.addEventListener('resize', computeH)
})
</script>

<style scoped>
.self-analysis { display: flex; flex-direction: column; }
.bar { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.bar .tip { font-size: 12px; color: #909399; }
.frame-wrap { flex: 1; min-height: 360px; }
.pyg-frame { width: 100%; border: 1px solid #ebeef5; border-radius: 6px; background: #fff; }
</style>
