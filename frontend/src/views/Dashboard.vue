<script setup lang="ts">
import { useUserStore } from "@/stores/user";
import { useRouter } from "vue-router";

const userStore = useUserStore();
const router = useRouter();

const logout = () => {
  userStore.logout();
  router.push("/login");
};
</script>

<template>
  <div style="padding: 40px">
    <h1>欢迎，{{ userStore.userInfo?.username ?? "用户" }}！</h1>
    <p>角色：{{ userStore.userInfo?.is_admin ? "管理员" : "普通用户" }}</p>
    <el-button @click="logout">退出登录</el-button>
  </div>
</template>