<template>
  <div class="feedback-container">
    <div class="feedback-content">
      <div class="feedback-header">
        <span class="feedback-icon">⏸️</span>
        <span class="feedback-title">{{ feedbackData.prompt }}</span>
      </div>
      <div v-if="feedbackData.generated_code" class="code-review-box">
        <div class="code-header">生成的代码：</div>
        <pre class="code-content">{{ feedbackData.generated_code }}</pre>
      </div>
      <div v-if="feedbackData.code_exception" class="error-box">
        <div class="error-header">错误代码：</div>
        <pre class="code-content">{{ feedbackData.executed_code }}</pre>
        <div class="error-message">
          <strong>错误信息：</strong>{{ feedbackData.code_exception }}
        </div>
      </div>
      <div class="feedback-form">
        <a-textarea
          v-model:value="feedbackInput"
          :placeholder="feedbackData.review_type === 'code_review' ? '输入 yes/y/ok 执行代码，或输入修改建议...' : '输入 ok 结束流程，或输入修改建议...'"
          :auto-size="{ minRows: 2, maxRows: 4 }"
          class="feedback-textarea"
        />
        <div class="feedback-actions">
          <a-button type="primary" @click="handleSubmit" :loading="submitting">
            提交反馈
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps({
  feedbackData: {
    type: Object,
    required: true
  },
  submitting: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['submit']);

const feedbackInput = ref('');

const handleSubmit = () => {
  emit('submit', feedbackInput.value);
};
</script>

<style scoped lang="less">
.feedback-container {
  margin: 16px 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #ffa500;
}

.feedback-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feedback-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  font-size: 14px;
  color: #333;
}

.feedback-icon {
  font-size: 18px;
}

.feedback-title {
  flex: 1;
}

.code-review-box,
.error-box {
  background: #fff;
  border-radius: 6px;
  padding: 12px;
  border: 1px solid #e0e0e0;
}

.code-header,
.error-header {
  font-weight: 500;
  margin-bottom: 8px;
  color: #555;
}

.code-content {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  overflow-x: auto;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
}

.error-box {
  border-left: 3px solid #ff4d4f;
}

.error-message {
  margin-top: 8px;
  color: #ff4d4f;
  font-size: 13px;
  line-height: 1.5;
}

.feedback-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feedback-textarea {
  min-height: 60px;
}

.feedback-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
