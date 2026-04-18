// 工单相关 API：增删改查 + 审批。
// 对应后端 /api/v1/tickets/* 路由。

import { request } from './request'
import type { Ticket, TicketCreate } from '../types'

export const ticketsApi = {
  list: () => request<Ticket[]>('/tickets'),

  get: (id: number) => request<Ticket>(`/tickets/${id}`),

  create: (data: TicketCreate) =>
    request<Ticket>('/tickets', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: number, data: Partial<TicketCreate & { status: string }>) =>
    request<Ticket>(`/tickets/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // 只有管理员可以调用，后端会校验权限并返回 403
  approve: (id: number) =>
    request<Ticket>(`/tickets/${id}/approve`, {
      method: 'POST',
      body: JSON.stringify({ approved: true }),
    }),
}
