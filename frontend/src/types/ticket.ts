export interface Ticket {
  id: number;
  title: string;
  description: string;
  asset_id: number;
  status: string;
  created_by_id: number;
  approved_by_id: number;
  created_at: string;
  updated_at: string;
}

export const TICKET_STATUS_MAP: Record<string, { label: string; type: string }> = {
  draft:     { label: "草稿",   type: "info" },
  submitted: { label: "待审批", type: "warning" },
  approved:  { label: "已通过", type: "success" },
  running:   { label: "执行中", type: "primary" },
  done:      { label: "已完成", type: "success" },
  failed:    { label: "失败",   type: "danger" },
  closed:    { label: "已关闭", type: "info" }
};

export const TICKET_STATUS_OPTIONS = Object.entries(TICKET_STATUS_MAP).map(
  ([value, { label }]) => ({ label, value })
);