// 认证相关 API：登录、注册、获取当前用户。
// 对应后端 /api/v1/auth/* 路由。

import { request } from './request'
import type { User } from '../types'

export const authApi = {
  login: (username: string, password: string) =>
    request<{ access_token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  register: (username: string, email: string, password: string, fullName?: string) =>
    request<User>('/auth/register', {
      method: 'POST',
      // full_name 为空时传 null，和后端 schema 保持一致
      body: JSON.stringify({ username, email, password, full_name: fullName || null }),
    }),

  me: () => request<User>('/auth/me'),
}
