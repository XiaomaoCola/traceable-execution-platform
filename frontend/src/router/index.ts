import { createRouter, createWebHistory } from "vue-router";
import type { RouteRecordRaw } from "vue-router";

// ─── 不需要登录的页面 ────────────────────────────────────────────
const publicRoutes: RouteRecordRaw[] = [
  { path: "/login", name: "Login", component: () => import("@/views/Login.vue") },
  { path: "/403",   name: "Forbidden",   component: () => import("@/views/error/403.vue") },
  { path: "/500",   name: "ServerError", component: () => import("@/views/error/500.vue") },
  { path: "/:pathMatch(.*)*", name: "NotFound", component: () => import("@/views/error/404.vue") },
];

// ─── 需要登录的页面（嵌套在主布局下）────────────────────────────
const protectedChildren: RouteRecordRaw[] = [
  { path: "dashboard",      name: "Dashboard",     component: () => import("@/views/Dashboard.vue") },
  { path: "tickets",        name: "Tickets",       component: () => import("@/views/tickets/Index.vue") },
  { path: "tickets/create", name: "TicketsCreate", component: () => import("@/views/tickets/Create.vue") },
  { path: "tickets/:id",    name: "TicketDetail",  component: () => import("@/views/tickets/Detail.vue") },
  { path: "assets",         name: "Assets",        component: () => import("@/views/assets/Index.vue") },
  { path: "assets/create",  name: "AssetsCreate",  component: () => import("@/views/assets/Create.vue") },
  { path: "assets/:id",     name: "AssetDetail",   component: () => import("@/views/assets/Detail.vue") },
  { path: "runs",           name: "Runs",          component: () => import("@/views/runs/Index.vue") },
  { path: "runs/create",    name: "RunCreate",     component: () => import("@/views/runs/Create.vue"), meta: { requiresAdmin: true } },
  { path: "runs/:id",       name: "RunDetail",     component: () => import("@/views/runs/Detail.vue") },
  { path: "chat",           name: "Chat",          component: () => import("@/views/chat/Index.vue") },
];

// ─── 路由主体 ────────────────────────────────────────────────────
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    {
      path: "/",
      component: () => import("@/layout/index.vue"),
      meta: { requiresAuth: true },
      children: protectedChildren,
    },
    ...publicRoutes,
  ],
});

// ─── 路由守卫：登录 & 权限拦截 ───────────────────────────────────
router.beforeEach((to, _, next) => {
  const token = localStorage.getItem("token");

  // 未登录时访问需要认证的页面，跳转到登录页
  if (to.meta.requiresAuth && !token) {
    next("/login");
    return;
  }

  // 访问需要管理员权限的页面，验证用户身份
  if (to.meta.requiresAdmin) {
    const userInfo = JSON.parse(localStorage.getItem("userInfo") || "{}");
    if (!userInfo?.is_admin) {
      next("/403");
      return;
    }
  }

  next();
});

export default router;