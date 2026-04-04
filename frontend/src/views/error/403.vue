<script setup lang="ts">
import { useRouter } from "vue-router";
const router = useRouter();
</script>

<template>
  <div class="error-page">
    <div class="error-code">403</div>
    <div class="error-title">无权限访问</div>
    <div class="error-desc">你没有权限访问此页面，请联系管理员</div>
    <el-button type="primary" @click="router.push('/dashboard')">返回首页</el-button>
  </div>
</template>

<style scoped>
.error-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  background: #f0f2f5;
}
.error-code { font-size: 120px; font-weight: 700; color: #d9d9d9; line-height: 1; }
.error-title { font-size: 24px; font-weight: 600; color: #333; }
.error-desc { font-size: 14px; color: #999; }
</style>