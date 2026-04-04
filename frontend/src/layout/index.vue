<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "@/stores/user";
import { House, Tickets, Box, List, Fold, Expand, ChatDotRound } from "@element-plus/icons-vue";


const router = useRouter();
const route = useRoute();
const userStore = useUserStore();
const collapsed = ref(false);

const isAdmin = computed(() => userStore.userInfo?.is_admin);

const logout = () => {
  userStore.logout();
  router.push("/login");
};
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside :width="collapsed ? '64px' : '220px'" style="transition: width 0.3s">
      <div class="logo">
        <span v-if="!collapsed">⚡ Traceable</span>
        <span v-else>⚡</span>
      </div>
      <el-menu
        :default-active="route.path"
        :collapse="collapsed"
        :collapse-transition="false"
        router
        background-color="#001529"
        text-color="#ffffffa6"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><House /></el-icon>
          <template #title>首页</template>
        </el-menu-item>

        <el-sub-menu index="tickets">
          <template #title>
            <el-icon><Tickets /></el-icon>
            <span>工单管理</span>
          </template>
          <el-menu-item index="/tickets">工单列表</el-menu-item>
          <el-menu-item index="/tickets/create">创建工单</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="assets">
          <template #title>
            <el-icon><Box /></el-icon>
            <span>资产管理</span>
          </template>
          <el-menu-item index="/assets">资产列表</el-menu-item>
          <el-menu-item index="/assets/create">创建资产</el-menu-item>
        </el-sub-menu>

        <el-sub-menu index="runs">
          <template #title>
            <el-icon><List /></el-icon>
            <span>运行记录</span>
          </template>
          <el-menu-item index="/runs">运行列表</el-menu-item>
          <!-- 只有管理员能看到创建运行 -->
          <el-menu-item v-if="isAdmin" index="/runs/create">创建运行</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <template #title>AI 对话</template>
        </el-menu-item>
        
      </el-menu>
    </el-aside>

    <el-container>
      <el-header>
        <div class="header-left">
          <el-button link :icon="collapsed ? Expand : Fold" @click="collapsed = !collapsed" size="large" />
        </div>
        <div class="header-right">
          <el-tag v-if="isAdmin" type="danger" size="small">管理员</el-tag>
          <span>{{ userStore.userInfo?.full_name || userStore.userInfo?.username }}</span>
          <el-button link @click="logout">退出登录</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.el-aside { background-color: #001529; overflow: hidden; }
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  font-weight: 700;
  border-bottom: 1px solid #ffffff15;
  white-space: nowrap;
  overflow: hidden;
}
.el-header {
  background: white;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.header-left, .header-right { display: flex; align-items: center; gap: 16px; }
.el-main { background: #f0f2f5; padding: 24px; }
</style>