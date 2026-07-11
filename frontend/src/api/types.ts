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
