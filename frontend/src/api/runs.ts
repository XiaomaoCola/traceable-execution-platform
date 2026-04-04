import request from "@/utils/request";
import type { Run } from "@/types/run";

// 查询参数类型
interface GetRunsParams {
  page?: number;      // 当前页码
  page_size?: number; // 每页条数
  ticket_id?: number; // 按工单 ID 筛选（可选）
  order_by?: string;       // 【新增】
  order?: "asc" | "desc"; // 【新增】
}

// 创建 Run 时需要传入的数据类型
interface CreateRunData {
  run_type: string;                       // 运行类型，如 "manual" / "auto" 等
  script_id: string;                      // 要执行的脚本 ID
  execution_context: Record<string, any>; // 执行上下文，键值对形式的动态参数
  ticket_id: number;                      // 关联的工单 ID
}

// 分页返回结构
interface PaginatedRuns {
  data: Run[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// 获取运行记录列表，支持分页和按工单筛选
export const getRuns = (params?: GetRunsParams) =>
  request.get<PaginatedRuns>("/runs", { params });

// 根据 ID 获取单条运行记录详情
export const getRun = (id: number) =>
  request.get<Run>(`/runs/${id}`);

// 创建一条新的运行记录（即触发一次脚本执行）
export const createRun = (data: CreateRunData) =>
  request.post<Run>("/runs", data);