export type JobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface RuleDefinition {
  id: string;
  name: string;
  category: string;
  target_folder: string;
  keywords: string[];
  regex_patterns: string[];
  min_confidence: number;
  enabled: boolean;
}

export interface AppSettings {
  output_path: string;
  file_mode: 'copy' | 'move';
  confidence_threshold: number;
  folder_template: string;
  auto_open_explorer: boolean;
  gemini_api_key?: string;
  gemini_model?: string;
  glenn_api_key?: string;
  glenn_model?: string;
  new_provider_api_key?: string;
  new_provider_model?: string;
  ocr_dpi?: number;
}

export interface JobCreatePayload {
  source_path: string;
  output_path?: string;
  file_mode?: 'copy' | 'move';
  confidence_threshold?: number;
  folder_template?: string;
}

export interface FileClassification {
  original_path: string;
  file_name: string;
  doc_type: string;
  owner: string;
  confidence: number;
  destination_path: string;
  status: 'sorted' | 'unsorted' | 'error';
  is_unsorted: boolean;
  error_message?: string;
  matched_keywords: string[];
}

export interface Job {
  id: string;
  source_path: string;
  output_path: string;
  file_mode: string;
  confidence_threshold: number;
  folder_template: string;
  status: JobStatus;
  total_files: number;
  sorted_files: number;
  unsorted_files: number;
  duration_seconds: number;
  created_at: string;
  updated_at: string;
}

export interface DirectoryNode {
  name: string;
  path: string;
  type: 'directory' | 'file';
  size?: number;
  children?: DirectoryNode[];
}

export type LiveJobEvent =
  | { event: 'job_started'; job_id: string; total_files: number; source_path: string; output_path: string }
  | { event: 'file_processed'; job_id: string; processed_count: number; total_files: number; file: FileClassification }
  | { event: 'job_completed'; job_id: string; total_files: number; sorted_files: number; unsorted_files: number; duration_seconds: number }
  | { event: 'job_error'; job_id: string; error: string };
