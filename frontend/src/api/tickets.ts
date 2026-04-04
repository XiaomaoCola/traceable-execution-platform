import request from "@/utils/request";
import type { Ticket } from "@/types/ticket";

// 查询参数类型
interface GetTicketsParams {
  page?: number;
  page_size?: number;
  keyword?: string;       // 【新增】
  status?: string;        // 【新增】
  asset_id?: number;      // 【新增】
  start_date?: string;    // 【新增】
  end_date?: string;      // 【新增】
  order_by?: string;    // 【新增】排序字段
  order?: "asc" | "desc"; // 【新增】排序方向
}

interface PaginatedTickets {
  data: Ticket[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}




// 获取工单列表，支持分页
export const getTickets = (params?: GetTicketsParams) =>
  request.get<PaginatedTickets>("/tickets", { params });

// 根据 ID 获取单个工单详情
export const getTicket = (id: number) =>
  request.get<Ticket>(`/tickets/${id}`);

// 创建新工单
// Partial<Ticket> 表示 Ticket 的所有字段都是可选的（不必填满）
export const createTicket = (data: Partial<Ticket>) =>
  request.post<Ticket>("/tickets", data);

// 更新指定工单（局部更新，只传要改的字段）
export const updateTicket = (id: number, data: Partial<Ticket>) =>
  request.patch<Ticket>(`/tickets/${id}`, data);

// 审批通过指定工单
// 不需要传 body，只需要工单 ID，由后端处理审批逻辑
export const approveTicket = (id: number) =>
  request.post(`/tickets/${id}/approve`);