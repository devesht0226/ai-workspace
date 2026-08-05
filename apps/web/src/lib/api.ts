export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type UserPublic = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  email_verified?: boolean;
  avatar_url?: string | null;
  created_at: string;
};

export type DashboardSummary = {
  counts: Record<string, number>;
  usage_by_type: Record<string, number>;
  model_usage?: Record<string, number>;
  token_usage?: { input: number; output: number; total: number };
  storage_bytes?: number;
  unread_notifications?: number;
  recent_activity: Array<{
    id: string;
    event_type: string;
    model_name: string | null;
    created_at: string | null;
  }>;
  recent_documents: Array<{ id: string; filename: string; status: string }>;
  recent_chats: Array<{ id: string; title: string; updated_at: string }>;
  recent_agent_runs?: Array<{
    id: string;
    task: string;
    status: string;
    created_at: string | null;
  }>;
  recent_meetings?: Array<{ id: string; title: string; status: string }>;
  settings: {
    email: string;
    full_name: string | null;
    role: string;
    avatar_url?: string | null;
  };
};

export type ChatSession = {
  id: string;
  title: string;
  model_name: string;
  provider: string;
  created_at: string;
  updated_at: string;
};

export type ChatMessage = {
  id: string;
  role: string;
  content: string;
  created_at: string;
};

export type ChatDetail = ChatSession & {
  messages: ChatMessage[];
};

export type DocumentItem = {
  id: string;
  filename: string;
  content_type: string;
  status: string;
  page_count: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
};

export type Citation = {
  document_id: string;
  filename: string;
  chunk_id: string;
  page_number: number | null;
  snippet: string;
  score: number | null;
};

export type RagResponse = {
  answer: string;
  citations: Citation[];
  eval_metrics?: Record<string, number> | null;
};

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const ACCESS_KEY = "aiw_access";
const REFRESH_KEY = "aiw_refresh";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(tokens: TokenResponse): void {
  localStorage.setItem(ACCESS_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthError";
  }
}

let refreshInFlight: Promise<boolean> | null = null;

async function tryRefreshTokens(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    const refresh = getRefreshToken();
    if (!refresh) return false;
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!response.ok) {
        clearTokens();
        return false;
      }
      const tokens = (await response.json()) as TokenResponse;
      setTokens(tokens);
      return true;
    } catch {
      clearTokens();
      return false;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  auth = true,
  retried = false,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  if (auth) {
    const token = getAccessToken();
    if (token) headers.set("Authorization", `Bearer ${token}`);
  }
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch {
    throw new Error(
      "Cannot reach the API. Start it with: uvicorn app.main:app --reload --port 8000",
    );
  }
  if (response.status === 401 && auth && !retried) {
    const ok = await tryRefreshTokens();
    if (ok) return apiFetch<T>(path, options, auth, true);
    clearTokens();
    throw new AuthError("Your session expired. Please sign in again.");
  }
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      message = data?.error?.message ?? message;
    } catch {
      /* ignore */
    }
    if (response.status === 401) {
      clearTokens();
      throw new AuthError(message);
    }
    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  register: (body: {
    email: string;
    password: string;
    full_name?: string;
  }) =>
    apiFetch<UserPublic>(
      "/api/v1/auth/register",
      { method: "POST", body: JSON.stringify(body) },
      false,
    ),
  login: (body: { email: string; password: string }) =>
    apiFetch<TokenResponse>(
      "/api/v1/auth/login",
      { method: "POST", body: JSON.stringify(body) },
      false,
    ),
  verifyEmail: (token: string) =>
    apiFetch<UserPublic>(
      "/api/v1/auth/verify-email",
      { method: "POST", body: JSON.stringify({ token }) },
      false,
    ),
  requestPasswordReset: (email: string) =>
    apiFetch<{ status: string }>(
      "/api/v1/auth/password-reset/request",
      { method: "POST", body: JSON.stringify({ email }) },
      false,
    ),
  confirmPasswordReset: (token: string, new_password: string) =>
    apiFetch<UserPublic>(
      "/api/v1/auth/password-reset/confirm",
      { method: "POST", body: JSON.stringify({ token, new_password }) },
      false,
    ),
  me: () => apiFetch<UserPublic>("/api/v1/users/me"),
  updateProfile: (full_name: string) =>
    apiFetch<UserPublic>("/api/v1/users/me", {
      method: "PATCH",
      body: JSON.stringify({ full_name }),
    }),
  listChats: () => apiFetch<ChatSession[]>("/api/v1/chats"),
  createChat: (title?: string) =>
    apiFetch<ChatSession>("/api/v1/chats", {
      method: "POST",
      body: JSON.stringify({ title }),
    }),
  getChat: (id: string) => apiFetch<ChatDetail>(`/api/v1/chats/${id}`),
  deleteChat: (id: string) =>
    apiFetch<void>(`/api/v1/chats/${id}`, { method: "DELETE" }),
  exportChat: async (id: string) => {
    const token = getAccessToken();
    const response = await fetch(`${API_BASE_URL}/api/v1/chats/${id}/export`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) throw new Error("Chat export failed");
    return response.text();
  },
  exportMyData: () =>
    apiFetch<Record<string, unknown>>("/api/v1/users/me/export"),
  sendMessage: async (
    id: string,
    content: string,
    onToken: (token: string) => void,
  ) => {
    const doFetch = async () => {
      const token = getAccessToken();
      return fetch(`${API_BASE_URL}/api/v1/chats/${id}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content, stream: true }),
      });
    };
    let response = await doFetch();
    if (response.status === 401) {
      const ok = await tryRefreshTokens();
      if (!ok) {
        clearTokens();
        throw new AuthError("Your session expired. Please sign in again.");
      }
      response = await doFetch();
    }
    if (!response.ok || !response.body) {
      throw new Error("Chat stream failed");
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const payload = JSON.parse(line.slice(5).trim()) as {
          event: string;
          data: string | { content: string };
        };
        if (payload.event === "token" && typeof payload.data === "string") {
          onToken(payload.data);
        }
        if (payload.event === "error") {
          const msg =
            typeof payload.data === "string"
              ? payload.data
              : "Chat failed — check API keys on the server.";
          throw new Error(msg);
        }
      }
    }
  },
  listDocuments: () => apiFetch<DocumentItem[]>("/api/v1/documents"),
  uploadDocument: async (file: File, collectionId?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (collectionId) form.append("collection_id", collectionId);
    return apiFetch<DocumentItem>("/api/v1/documents", {
      method: "POST",
      body: form,
    });
  },
  deleteDocument: (id: string) =>
    apiFetch<void>(`/api/v1/documents/${id}`, { method: "DELETE" }),
  queryDocument: (id: string, question: string) =>
    apiFetch<RagResponse>(`/api/v1/documents/${id}/query`, {
      method: "POST",
      body: JSON.stringify({ question, top_k: 5 }),
    }),
  ragQuery: (question: string, documentId?: string) =>
    apiFetch<RagResponse>("/api/v1/rag/query", {
      method: "POST",
      body: JSON.stringify({
        question,
        top_k: 5,
        document_id: documentId ?? null,
      }),
    }),
  sqlSchema: () => apiFetch<Record<string, unknown>>("/api/v1/sql/schema"),
  sqlGenerate: (question: string) =>
    apiFetch<{ sql: string }>("/api/v1/sql/generate", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  sqlExplain: (sql: string) =>
    apiFetch<{ explanation: string }>("/api/v1/sql/explain", {
      method: "POST",
      body: JSON.stringify({ sql }),
    }),
  sqlOptimize: (sql: string) =>
    apiFetch<{ suggestions: string[] }>("/api/v1/sql/optimize", {
      method: "POST",
      body: JSON.stringify({ sql }),
    }),
  sqlExecute: (sql: string) =>
    apiFetch<{
      columns: string[];
      rows: Record<string, unknown>[];
      row_count: number;
      sql: string;
    }>("/api/v1/sql/execute", {
      method: "POST",
      body: JSON.stringify({ sql }),
    }),
  codeReviews: () => apiFetch<Array<Record<string, unknown>>>("/api/v1/code/reviews"),
  createCodeReview: async (file: File, title?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    return apiFetch<Record<string, unknown>>("/api/v1/code/reviews", {
      method: "POST",
      body: form,
    });
  },
  analyzeResume: async (file: File, jobDescription?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (jobDescription) form.append("job_description", jobDescription);
    return apiFetch<Record<string, unknown>>("/api/v1/resumes/analyze", {
      method: "POST",
      body: form,
    });
  },
  listResumes: () => apiFetch<Array<Record<string, unknown>>>("/api/v1/resumes"),
  createMeeting: async (opts: {
    file?: File;
    title?: string;
    transcript?: string;
  }) => {
    const form = new FormData();
    if (opts.file) form.append("file", opts.file);
    if (opts.title) form.append("title", opts.title);
    if (opts.transcript) form.append("transcript", opts.transcript);
    return apiFetch<Record<string, unknown>>("/api/v1/meetings", {
      method: "POST",
      body: form,
    });
  },
  listMeetings: () => apiFetch<Array<Record<string, unknown>>>("/api/v1/meetings"),
  runAgents: (task: string) =>
    apiFetch<Record<string, unknown>>("/api/v1/agents/runs", {
      method: "POST",
      body: JSON.stringify({ task }),
    }),
  listAgentRuns: () =>
    apiFetch<Array<Record<string, unknown>>>("/api/v1/agents/runs"),
  dashboard: () => apiFetch<DashboardSummary>("/api/v1/dashboard/summary"),
  listTraces: () =>
    apiFetch<{ traces: Array<Record<string, unknown>> }>("/api/v1/traces"),
  getTrace: (id: string) => apiFetch<Record<string, unknown>>(`/api/v1/traces/${id}`),
  listRagEvals: () =>
    apiFetch<{ evals: Array<Record<string, unknown>> }>("/api/v1/eval/rag"),
  runRagEval: (body: {
    question: string;
    answer: string;
    contexts: string[];
    retrieved_ids: string[];
    citations?: Array<Record<string, unknown>>;
  }) =>
    apiFetch<Record<string, unknown>>("/api/v1/eval/rag", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  scoreRag: (body: {
    question: string;
    answer: string;
    contexts: string[];
    retrieved_ids: string[];
    citations?: Array<Record<string, unknown>>;
  }) =>
    apiFetch<Record<string, unknown>>("/api/v1/eval/rag/score", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  submitFeedback: (body: {
    target_type: string;
    rating: number;
    target_id?: string;
    answer_snapshot?: string;
    comment?: string;
  }) =>
    apiFetch<Record<string, unknown>>("/api/v1/feedback", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  feedbackSummary: () => apiFetch<Record<string, unknown>>("/api/v1/feedback/summary"),
  listPrompts: (name?: string) =>
    apiFetch<{ prompts: Array<Record<string, unknown>> }>(
      name ? `/api/v1/prompts?name=${encodeURIComponent(name)}` : "/api/v1/prompts",
    ),
  createPrompt: (body: {
    name: string;
    content: string;
    model_family?: string;
  }) =>
    apiFetch<Record<string, unknown>>("/api/v1/prompts", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  runBenchmark: (question: string) =>
    apiFetch<Record<string, unknown>>("/api/v1/benchmarks", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
  listBenchmarks: () =>
    apiFetch<{ benchmarks: Array<Record<string, unknown>> }>("/api/v1/benchmarks"),
  renameChat: (id: string, title: string) =>
    apiFetch<ChatSession>(`/api/v1/chats/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    }),
  listOrgs: () =>
    apiFetch<{ organizations: Array<Record<string, unknown>> }>("/api/v1/orgs"),
  createOrg: (name: string) =>
    apiFetch<Record<string, unknown>>("/api/v1/orgs", {
      method: "POST",
      body: JSON.stringify({ name }),
    }),
  listOrgMembers: (orgId: string) =>
    apiFetch<{ members: Array<Record<string, unknown>> }>(`/api/v1/orgs/${orgId}/members`),
  inviteOrgMember: (orgId: string, email: string) =>
    apiFetch<Record<string, unknown>>(`/api/v1/orgs/${orgId}/members`, {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  listNotifications: () =>
    apiFetch<{
      notifications: Array<Record<string, unknown>>;
      unread: number;
    }>("/api/v1/notifications"),
  markNotificationRead: (id: string) =>
    apiFetch<Record<string, unknown>>(`/api/v1/notifications/${id}/read`, {
      method: "POST",
    }),
  markAllNotificationsRead: () =>
    apiFetch<{ marked: number }>("/api/v1/notifications/read-all", {
      method: "POST",
    }),
  changePassword: (current_password: string, new_password: string) =>
    apiFetch<{ status: string }>("/api/v1/users/me/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password, new_password }),
    }),
  listSessions: () =>
    apiFetch<{ sessions: Array<Record<string, unknown>> }>("/api/v1/users/me/sessions"),
  revokeSession: (id: string) =>
    apiFetch<void>(`/api/v1/users/me/sessions/${id}`, { method: "DELETE" }),
  logoutAll: () =>
    apiFetch<{ revoked: number }>("/api/v1/auth/logout-all", { method: "POST" }),
  deleteAccount: () =>
    apiFetch<{ status: string }>("/api/v1/users/me", { method: "DELETE" }),
  adminUsers: () => apiFetch<UserPublic[]>("/api/v1/admin/users"),
  adminStats: () => apiFetch<Record<string, unknown>>("/api/v1/admin/stats"),
  adminActivate: (id: string) =>
    apiFetch<UserPublic>(`/api/v1/admin/users/${id}/activate`, { method: "POST" }),
  adminDeactivate: (id: string) =>
    apiFetch<UserPublic>(`/api/v1/admin/users/${id}/deactivate`, { method: "POST" }),
  adminPromote: (id: string) =>
    apiFetch<UserPublic>(`/api/v1/admin/users/${id}/promote`, { method: "POST" }),
  listCollections: () =>
    apiFetch<Array<Record<string, unknown>>>("/api/v1/document-collections"),
  createCollection: (name: string, description?: string) =>
    apiFetch<Record<string, unknown>>("/api/v1/document-collections", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    }),
  sqlEr: () => apiFetch<Record<string, unknown>>("/api/v1/sql/er"),
};
