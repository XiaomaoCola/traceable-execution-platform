import { defineStore } from "pinia";
import { ref } from "vue";
import { login, getMe } from "@/api/auth";
import type { User } from "@/types/user";

export const useUserStore = defineStore("user", () => {

  // ─── 状态 ──────────────────────────────────────────────────────
  
  // 从 localStorage 恢复 token（刷新页面后不会丢失登录态）
  const token = ref(localStorage.getItem("token") || "");

  // 从 localStorage 恢复用户信息，没有则为 null
  const userInfo = ref<User | null>(
    JSON.parse(localStorage.getItem("userInfo") || "null")
  );

  // ─── 操作 ──────────────────────────────────────────────────────

  // 登录：用用户名密码换取 token，再顺带拉取用户信息
  async function loginByUsername(username: string, password: string) {
    const res = await login(username, password);
    token.value = res.data.access_token;
    localStorage.setItem("token", token.value); // 持久化 token
    await fetchUserInfo();
  }

  // 获取当前登录用户的详细信息并缓存到 localStorage
  async function fetchUserInfo() {
    const res = await getMe();
    userInfo.value = res.data;
    localStorage.setItem("userInfo", JSON.stringify(res.data));
  }

  // 登出：清空内存中的状态 + 清除 localStorage 里的缓存
  function logout() {
    token.value = "";
    userInfo.value = null;
    localStorage.removeItem("token");
    localStorage.removeItem("userInfo");
  }

  return { token, userInfo, loginByUsername, fetchUserInfo, logout };
});