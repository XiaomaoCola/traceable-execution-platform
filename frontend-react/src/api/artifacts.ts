// 附件相关 API：列表、上传、下载。
// 文件上传需要 FormData，无法走通用 request()，单独处理。

import { request, BASE_URL } from './request'
import type { Artifact } from '../types'

export const artifactsApi = {
  listByTicket: (ticketId: number) =>
    request<Artifact[]>(`/artifacts/ticket/${ticketId}`),

  get: (id: number) => request<Artifact>(`/artifacts/${id}`),

  upload: async (
    ticketId: number,
    file: File,
    artifactType?: string,
    description?: string,
  ): Promise<{ artifact: Artifact; message: string }> => {
    const token = localStorage.getItem('access_token')
    const formData = new FormData()
    formData.append('file', file)
    if (artifactType) formData.append('artifact_type', artifactType)
    if (description) formData.append('description', description)

    // ticket_id 通过 query string 传递（后端接口设计如此）
    const res = await fetch(`${BASE_URL}/artifacts?ticket_id=${ticketId}`, {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: '上传失败' }))
      throw new Error(err.detail || '上传失败')
    }

    return res.json()
  },

  // 返回下载链接供 <a href> 直接使用，不走 fetch
  downloadUrl: (id: number) => `${BASE_URL}/artifacts/${id}/download`,
}
