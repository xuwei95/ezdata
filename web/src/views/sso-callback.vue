<template>
  <div class="sso-callback">
    <el-result
      v-if="error"
      icon="error"
      title="登录失败"
      :sub-title="error"
    >
      <template #extra>
        <el-button type="primary" @click="goLogin">返回登录</el-button>
      </template>
    </el-result>
    <div v-else class="loading-tip">正在登录...</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import useUserStore from "@/store/modules/user";
import { setToken } from "@/utils/auth";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();
const error = ref("");

function goLogin() {
  router.replace("/login");
}

onMounted(async () => {
  const token = route.query.token;
  const err = route.query.error;
  if (err) {
    error.value = decodeURIComponent(err);
    return;
  }
  if (!token) {
    error.value = "缺少登录凭证";
    return;
  }
  // 写入 token 并拉取用户信息后进入首页(复用账密登录后的会话流程)
  setToken(token);
  userStore.token = token;
  try {
    await userStore.getInfo();
    router.replace("/");
  } catch (e) {
    error.value = "获取用户信息失败，请重试";
  }
});
</script>

<style scoped>
.sso-callback {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
}
.loading-tip {
  font-size: 16px;
  color: #606266;
}
</style>
