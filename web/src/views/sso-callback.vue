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

onMounted(() => {
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
  // 只写入 token 后进首页,getInfo + 动态路由生成交给全局守卫(permission.js),与账密登录一致。
  // 切勿在此提前调用 getInfo:那会填充 userStore.roles,导致守卫(roles.length===0 才生成路由)
  // 误判“路由已生成”而跳过 generateRoutes,结果菜单/侧边栏全空。
  setToken(token);
  userStore.token = token;
  router.replace("/");
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
