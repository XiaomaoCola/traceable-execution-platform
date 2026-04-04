import request from "@/utils/request";
import type { Artifact } from "@/types/artifact";

// 分页查询参数
interface GetArtifactsParams {
  page?: number;      // 当前页码
  page_size?: number; // 每页条数
}

// 分页返回结构
interface PaginatedArtifacts {
  data: Artifact[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// 根据工单 ID 获取该工单下的所有附件列表，支持分页
export const getTicketArtifacts = (ticketId: number, params?: GetArtifactsParams) =>
  request.get<PaginatedArtifacts>(`/artifacts/ticket/${ticketId}`, { params });

// 根据附件 ID 获取单个附件的详细信息
export const getArtifact = (id: number) =>
  request.get<Artifact>(`/artifacts/${id}`);

export const uploadArtifact = (ticketId: number, file: File, artifactType?: string, description?: string) => {
  const formData = new FormData();
  formData.append("file", file);
  // 根据有没有参数，动态拼接 URL 查询参数
  return request.post<Artifact>(
    `/artifacts?ticket_id=${ticketId}${artifactType ? `&artifact_type=${artifactType}` : ""}${description ? `&description=${description}` : ""}`,
    formData,
    // 告知服务器这是文件上传请求
    { headers: { "Content-Type": "multipart/form-data" } }
  );
};

// 根据 artifact 的 id，从后端下载对应的文件
export const downloadArtifact = (id: number) =>
  request.get(`/artifacts/${id}/download`, { responseType: "blob" });