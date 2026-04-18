// 工单相关类型，对应后端 schemas/ticket.py 和 models/ticket.py。

// 工单的生命周期状态
export type TicketStatus =
  | 'draft'      // 草稿
  | 'submitted'  // 已提交，等待审批
  | 'approved'   // 已审批，可执行 ActionRun
  | 'running'    // 执行中
  | 'done'       // 完成
  | 'failed'     // 失败
  | 'closed'     // 已关闭

export interface Ticket {
  id: number
  title: string
  description: string | null
  status: TicketStatus
  asset_id: number | null
  created_by_id: number
  approved_by_id: number | null
  created_at: string
  updated_at: string
}

export interface TicketCreate {
  title: string
  description?: string
  asset_id?: number
}
