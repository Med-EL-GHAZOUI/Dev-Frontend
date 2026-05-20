// lib/api.ts — Client API centralisé pour ForecastIQ
// Toutes les requêtes vers le backend Flask passent par ici.

export type UserRole = "user" | "manager" | "admin";

export type User = {
  id?: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active?: boolean;
};

type RequestOptions = {
  method?: string;
  body?: unknown;
  isForm?: boolean;
};

type ApiError = Error & {
  status?: number;
  data?: unknown;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:3001";

// ---- Gestion du token JWT (localStorage) ----
const TOKEN_KEY = "forecastiq_token";
const USER_KEY = "forecastiq_user";

export function saveAuth(token: string, user: User) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  try {
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function clearAuth() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

// ---- Wrapper fetch ----
async function request<T = any>(path: string, { method = "GET", body, isForm = false }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  let payload: BodyInit | undefined;
  if (body && !isForm) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  } else {
    payload = body as BodyInit | undefined;
  }

  const res = await fetch(`${API_BASE}${path}`, { method, headers, body: payload });

  if (res.status === 401 && typeof window !== "undefined") {
    clearAuth();
  }

  let data: any = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!res.ok) {
    const message = (data && data.error) || `Erreur ${res.status}`;
    const err: ApiError = new Error(message);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

// ---- API ----
export const api = {
  register: (email: string, password: string, full_name: string) =>
    request<{ token: string; user: User }>("/api/auth/register", { method: "POST", body: { email, password, full_name } }),

  login: (email: string, password: string) =>
    request<{ token: string; user: User }>("/api/auth/login", { method: "POST", body: { email, password } }),

  me: () => request<{ user: User }>("/api/auth/me"),

  logout: () => request("/api/auth/logout", { method: "POST" }),

  changePassword: (old_password: string, new_password: string) =>
    request("/api/auth/change-password", {
      method: "POST",
      body: { old_password, new_password },
    }),

  listDatasets: () => request("/api/datasets"),

  getDataset: (id: number | string) => request(`/api/datasets/${id}`),

  previewDataset: (id: number | string) => request(`/api/datasets/${id}/preview`),

  uploadDataset: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request("/api/datasets/upload", { method: "POST", body: form, isForm: true });
  },

  updateMapping: (id: number | string | null, mapping: unknown) =>
    request(`/api/datasets/${id}/mapping`, { method: "PUT", body: mapping }),

  deleteDataset: (id: number | string) => request(`/api/datasets/${id}`, { method: "DELETE" }),

  getDashboard: (id: number | string, { granularity = "monthly", horizon = 6, category }: { granularity?: string; horizon?: number; category?: string } = {}) => {
    const params = new URLSearchParams({ granularity, horizon: String(horizon) });
    if (category) params.set("category", category);
    return request(`/api/datasets/${id}/dashboard?${params}`);
  },

  runForecast: (dataset_id: number | string, opts = {}) =>
    request("/api/forecasts/run", { method: "POST", body: { dataset_id, ...opts } }),

  getForecast: (id: number | string) => request(`/api/forecasts/${id}`),

  listForecasts: (datasetId: number | string) => request(`/api/datasets/${datasetId}/forecasts`),

  health: () => request("/api/health"),
};

export { API_BASE };


