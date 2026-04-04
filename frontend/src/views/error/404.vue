<script setup lang="ts">
import { useRouter } from "vue-router";
const router = useRouter();
</script>

<template>
  <div class="error-page">
    <div class="error-code">404</div>
    <div class="error-title">页面不存在</div>
    <div class="error-desc">你访问的页面不存在，请检查地址是否正确</div>
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