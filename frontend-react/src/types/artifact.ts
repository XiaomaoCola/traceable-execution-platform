// 附件相关类型，对应后端 schemas/artifact.py。
// 附件（Artifact）是工单下上传的文件，如路由器配置文件。

export interface Artifact {
  id: number
  filename: string
  artifact_type: string | null
  description: string | null
  content_type: string | null
  size_bytes: number
  sha256_hash: string
  ticket_id: number
  run_id: number | null
  uploaded_by_id: number
  is_deleted: boolean
  created_at: string
}
