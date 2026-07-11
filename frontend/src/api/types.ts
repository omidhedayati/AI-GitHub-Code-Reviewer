export interface User {
  id: string;
  email: string;
  full_name: string | null;
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
