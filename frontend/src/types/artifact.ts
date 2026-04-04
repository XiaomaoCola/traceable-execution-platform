export interface Artifact {
  id: number;
  filename: string;
  artifact_type: string;
  description: string;
  content_type: string;
  size_bytes: number;
  sha256_hash: string;
  ticket_id: number;
  run_id: number;
  uploaded_by_id: number;
  is_deleted: boolean;
  created_at: string;
}