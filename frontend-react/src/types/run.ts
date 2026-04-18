// 执行记录相关类型，对应后端 schemas/run.py 和 models/run.py。

// proof = 只验证不变更；action = 真实执行
export type RunType = 'proof' | 'action'
export type RunStatus = 'pending' | 'running' | 'done' | 'failed'

export interface Run {
  id: number
  run_type: RunType
  status: RunStatus
  ticket_id: number
  executed_by_id: number
  script_id: string | null
  result_summary: string | null
  exit_code: number | null
  inputs_manifest: Record<string, unknown> | null
  outputs_manifest: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

// RunDetail 在 Run 基础上多了日志字段，只在详情页用到
export interface RunDetail extends Run {
  stdout_log: string | null
  stderr_log: string | null
}
