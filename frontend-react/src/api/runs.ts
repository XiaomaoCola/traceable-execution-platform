// 执行记录相关 API：列表、详情、创建。
// 对应后端 /api/v1/runs/* 路由。

import { request } from './request'
import type { Run, RunDetail } from '../types'

export const runsApi = {
  // ticketId 可选，不传则返回当前用户所有 run
  list: (ticketId?: number) =>
    request<Run[]>(`/runs${ticketId != null ? `?ticket_id=${ticketId}` : ''}`),

  // 详情比列表多 stdout_log / stderr_log 两个日志字段
  get: (id: number) => request<RunDetail>(`/runs/${id}`),

  create: (ticketId: number, runType: 'proof' | 'action') =>
    request<Run>('/runs', {
      method: 'POST',
      body: JSON.stringify({ ticket_id: ticketId, run_type: runType }),
    }),
}
