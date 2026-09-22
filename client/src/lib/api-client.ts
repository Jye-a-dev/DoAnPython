import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/py";
export const BACKEND_SERVER_URL = process.env.NEXT_PUBLIC_SERVER_URL || "http://localhost:3000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
  withCredentials: true,
});

// Request Interceptor: Attach JWT Bearer Token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("access_token");
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error: AxiosError) => Promise.reject(error)
);

// Response Interceptor: 401 Unauthorized handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("auth_user");
        window.dispatchEvent(new CustomEvent("auth:unauthorized"));
      }
    }
    return Promise.reject(error);
  }
);

/**
 * Resolves media URLs returned by backend (SQLite BLOB streaming or static files).
 * Ensures relative endpoints like /api/v1/media/records/... correctly map to Flask server.
 */
export function resolveMediaUrl(path?: string | null): string {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("blob:") || path.startsWith("data:")) {
    return path;
  }
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${BACKEND_SERVER_URL}${cleanPath}`;
}
