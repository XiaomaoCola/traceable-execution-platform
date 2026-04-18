// Workflow 相关 API：触发 LLM 分析任务。
// 对应后端 /api/v1/workflows/* 路由。

import { request } from './request'

export interface RouterConfigAnalysisResult {
  status: string
  analysis: string | null
  analysis_artifact_id: number | null
  config_filename: string | null
  error: string | null
}

export const workflowsApi = {
  // 对指定工单下的路由器配置文件触发 LLM 分析
  analyzeRouterConfig: (ticketId: number, artifactId: number) =>
    request<RouterConfigAnalysisResult>(
      `/workflows/tickets/${ticketId}/analyze-router-config`,
      {
        method: 'POST',
        body: JSON.stringify({ artifact_id: artifactId }),
      },
    ),
}
