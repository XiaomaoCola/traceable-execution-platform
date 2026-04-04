export interface Run {
  id: number;
  run_type: string;
  script_id: string;
  execution_context: Record<string, any>;
  status: string;
  ticket_id: number;
  executed_by_id: number;
  validator_version: string;
  rules_version: string;
  inputs_manifest: Record<string, any>;
  outputs_manifest: Record<string, any>;
  result_summary: string;
  exit_code: number;
  created_at: string;
  updated_at: string;
  stdout_log?: string;
  stderr_log?: string;
}

export const RUN_STATUS_MAP: Record<string, { label: string; type: string }> = {
  pending:  { label: "等待中", type: "info" },
  running:  { label: "执行中", type: "primary" },
  done:     { label: "已完成", type: "success" },
  failed:   { label: "失败",   type: "danger" }
};