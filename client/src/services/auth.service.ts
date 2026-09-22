import { apiClient } from "@/lib/api-client";
import type { AuthResponse, User } from "@/types";

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string;
}

export interface LoginPayload {
  email: string;
  password?: string;
  role_id?: number;
  full_name?: string;
}

export const authService = {
  getMe: () =>
    apiClient.get<User>("/auth/me"),

  register: (payload: RegisterPayload) =>
    apiClient.post<AuthResponse>("/auth/register", payload),

  login: (payload: LoginPayload) =>
    apiClient.post<AuthResponse>("/auth/login", payload),

  loginWithGoogle: (idToken: string) =>
    apiClient.post<AuthResponse>("/auth/google", { id_token: idToken }),

  logout: () =>
    apiClient.post("/auth/logout"),
};
