import type {
  AuthResponse,
  GitHubExchangeRequest,
  LoginRequest,
  RegisterRequest,
  Repository,
  RepositoryCreateRequest,
  RepositoryListResponse,
  Review,
  ReviewListResponse,
  OllamaHealthResponse,
  ReportFormat,
  ReviewSearchResponse,
  TokenResponse,
  User,
  UserSettingsResponse,
  UserSettingsUpdate,
} from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export const ACCESS_TOKEN_KEY = "reviewer_access_token";
export const REFRESH_TOKEN_KEY = "reviewer_refresh_token";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type RequestOptions = RequestInit & {
  auth?: boolean;
};

let accessTokenProvider: (() => string | null) | null = null;

export function setAccessTokenProvider(provider: () => string | null): void {
  accessTokenProvider = provider;
}

function getStoredAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { auth = false, headers, ...rest } = options;
  const url = `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;

  const requestHeaders = new Headers(headers);
  requestHeaders.set("Content-Type", "application/json");

  if (auth) {
    const token = accessTokenProvider?.() ?? getStoredAccessToken();
    if (token) {
      requestHeaders.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(url, {
    ...rest,
    headers: requestHeaders,
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new ApiError(body.detail ?? response.statusText, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export interface HealthResponse {
  status: string;
}

export const apiClient = {
  getHealth: () => request<HealthResponse>("/api/v1/health"),

  getOllamaHealth: () => request<OllamaHealthResponse>("/api/v1/health/ollama"),

  getMySettings: () => request<UserSettingsResponse>("/api/v1/settings/me", { auth: true }),

  updateMySettings: (data: UserSettingsUpdate) =>
    request<UserSettingsResponse>("/api/v1/settings/me", {
      method: "PUT",
      auth: true,
      body: JSON.stringify(data),
    }),

  getMyOllamaHealth: () =>
    request<OllamaHealthResponse>("/api/v1/settings/me/ollama-health", {
      auth: true,
    }),

  register: (data: RegisterRequest) =>
    request<AuthResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: LoginRequest) =>
    request<AuthResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  exchangeGitHubCode: (data: GitHubExchangeRequest) =>
    request<AuthResponse>("/api/v1/auth/github/exchange", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  refresh: (refreshToken: string) =>
    request<TokenResponse>("/api/v1/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),

  getMe: () => request<User>("/api/v1/auth/me", { auth: true }),

  listRepositories: () =>
    request<RepositoryListResponse>("/api/v1/repositories", { auth: true }),

  cloneRepository: (data: RepositoryCreateRequest) =>
    request<Repository>("/api/v1/repositories", {
      method: "POST",
      auth: true,
      body: JSON.stringify(data),
    }),

  getRepository: (id: string) =>
    request<Repository>(`/api/v1/repositories/${id}`, { auth: true }),

  deleteRepository: (id: string) =>
    request<void>(`/api/v1/repositories/${id}`, {
      method: "DELETE",
      auth: true,
    }),

  analyzeRepository: (id: string) =>
    request<Review>(`/api/v1/repositories/${id}/analyze`, {
      method: "POST",
      auth: true,
    }),

  aiReviewRepository: (id: string) =>
    request<Review>(`/api/v1/repositories/${id}/ai-review`, {
      method: "POST",
      auth: true,
    }),

  getLatestReview: (repositoryId: string, reviewType?: Review["review_type"]) =>
    request<Review>(
      `/api/v1/repositories/${repositoryId}/reviews/latest${
        reviewType ? `?review_type=${reviewType}` : ""
      }`,
      {
        auth: true,
      },
    ),

  getReview: (reviewId: string) =>
    request<Review>(`/api/v1/reviews/${reviewId}`, { auth: true }),

  listReviews: (repositoryId: string) =>
    request<ReviewListResponse>(`/api/v1/repositories/${repositoryId}/reviews`, {
      auth: true,
    }),

  searchReviews: (params: {
    q?: string;
    review_type?: Review["review_type"];
    severity?: string;
    offset?: number;
    limit?: number;
  }) => {
    const search = new URLSearchParams();
    if (params.q) search.set("q", params.q);
    if (params.review_type) search.set("review_type", params.review_type);
    if (params.severity) search.set("severity", params.severity);
    if (params.offset !== undefined) search.set("offset", String(params.offset));
    if (params.limit !== undefined) search.set("limit", String(params.limit));
    const query = search.toString();
    return request<ReviewSearchResponse>(
      `/api/v1/reviews${query ? `?${query}` : ""}`,
      { auth: true },
    );
  },

  fetchReviewReport: async (
    reviewId: string,
    format: ReportFormat,
    download = false,
  ): Promise<string> => {
    const search = new URLSearchParams({ format });
    if (download) search.set("download", "true");
    const token = accessTokenProvider?.() ?? getStoredAccessToken();
    const response = await fetch(
      `${API_BASE_URL}/api/v1/reviews/${reviewId}/report?${search.toString()}`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      },
    );
    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as { detail?: string };
      throw new ApiError(body.detail ?? response.statusText, response.status);
    }
    return response.text();
  },
};

export { API_BASE_URL };
