export interface User {
  id: string;
  email: string;
  full_name: string | null;
  github_username: string | null;
  avatar_url: string | null;
  auth_provider: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthResponse {
  user: User;
  tokens: TokenResponse;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface GitHubExchangeRequest {
  code: string;
}

export type RepositoryStatus = "pending" | "cloning" | "ready" | "failed";

export interface Repository {
  id: string;
  url: string;
  owner: string;
  name: string;
  default_branch: string | null;
  local_path: string | null;
  status: RepositoryStatus;
  error_message: string | null;
  cloned_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RepositoryListResponse {
  items: Repository[];
  total: number;
}

export interface RepositoryCreateRequest {
  url: string;
  branch?: string;
}

export type ReviewStatus = "pending" | "running" | "completed" | "failed";

export type ReviewType = "static" | "ai" | "hybrid";

export type IssueCategory =
  | "bug"
  | "duplicated_code"
  | "long_method"
  | "bad_naming"
  | "security"
  | "code_smell"
  | "dead_code"
  | "complexity"
  | "missing_documentation"
  | "unused_import";

export type IssueSeverity = "critical" | "high" | "medium" | "low" | "info";

export interface ReviewIssue {
  id: string;
  file_path: string;
  line_start: number;
  line_end: number | null;
  category: IssueCategory;
  severity: IssueSeverity;
  confidence: number;
  rule_id: string;
  title: string;
  explanation: string;
  suggestion: string;
}

export interface FileAnalysisResult {
  id: string;
  file_path: string;
  language: string;
  line_count: number;
  issues_count: number;
  file_score: number;
}

export interface Review {
  id: string;
  repository_id: string;
  user_id: string;
  status: ReviewStatus;
  review_type: ReviewType;
  ai_model: string | null;
  report_markdown: string | null;
  files_analyzed: number;
  issues_count: number;
  overall_score: number;
  summary: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  issues: ReviewIssue[];
  file_results: FileAnalysisResult[];
}

export interface ReviewListResponse {
  items: Review[];
  total: number;
}

export interface ReviewHistoryItem {
  id: string;
  repository_id: string;
  repository_name: string;
  review_type: ReviewType;
  status: ReviewStatus;
  overall_score: number;
  issues_count: number;
  files_analyzed: number;
  summary: string | null;
  ai_model: string | null;
  created_at: string;
}

export interface ReviewSearchResponse {
  items: ReviewHistoryItem[];
  total: number;
  offset: number;
  limit: number;
}

export type ReportFormat = "markdown" | "json" | "summary";

export interface OllamaHealthResponse {
  status: string;
  model: string;
  models_available: string[];
  base_url: string;
  message?: string;
}

export interface UserSettingsOverrides {
  ollama_base_url: string | null;
  ollama_model: string | null;
  ignored_folders: string | null;
  ignored_extensions: string | null;
  max_file_size_bytes: number | null;
}

export interface EffectiveUserSettings {
  ollama_base_url: string;
  ollama_model: string;
  ignored_folders: string;
  ignored_extensions: string;
  max_file_size_bytes: number;
}

export interface UserSettingsResponse {
  overrides: UserSettingsOverrides;
  effective: EffectiveUserSettings;
}

export interface UserSettingsUpdate {
  ollama_base_url?: string | null;
  ollama_model?: string | null;
  ignored_folders?: string | null;
  ignored_extensions?: string | null;
  max_file_size_bytes?: number | null;
}
