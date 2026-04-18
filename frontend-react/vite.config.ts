// Vite 构建配置。
// 核心作用：把前端 /api/* 请求转发到后端 8000 端口，
// 避免浏览器跨域拦截（开发环境专用，生产环境由 nginx 处理）。

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // 所有以 /api 开头的请求都转发到后端
      // 例：前端请求 /api/v1/auth/login → 实际发到 http://localhost:8000/api/v1/auth/login
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
