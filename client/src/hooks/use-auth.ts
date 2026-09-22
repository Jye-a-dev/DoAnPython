"use client";

import { create } from "zustand";
import { apiClient } from "@/lib/api-client";
import { AuthResponse, User } from "@/types";

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  login: (email: string, role_id?: number, full_name?: string) => Promise<void>;
  loginWithGoogle: (idToken: string) => Promise<void>;
  fetchMe: () => Promise<User | null>;
  logout: () => Promise<void>;
  initializeAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  isAdmin: false,
  isLoading: true,

  initializeAuth: async () => {
    if (typeof window === "undefined") {
      set({ isLoading: false });
      return;
    }

    const token = localStorage.getItem("access_token");
    const cachedUser = localStorage.getItem("auth_user");

    if (token) {
      let initialUser: User | null = null;
      if (cachedUser) {
        try {
          initialUser = JSON.parse(cachedUser);
        } catch {
          initialUser = null;
        }
      }

      set({
        token,
        user: initialUser,
        isAuthenticated: true,
        isAdmin: initialUser?.role_id === 1,
        isLoading: true,
      });

      try {
        await get().fetchMe();
      } catch {
        // fetchMe failure handled inside fetchMe
      } finally {
        set({ isLoading: false });
      }
    } else {
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isAdmin: false,
        isLoading: false,
      });
    }

    // Subscribe to global unauthorized broadcast
    window.addEventListener("auth:unauthorized", () => {
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isAdmin: false,
      });
    });
  },

  fetchMe: async () => {
    try {
      const response = await apiClient.get<User>("/auth/me");
      const user = response.data;
      localStorage.setItem("auth_user", JSON.stringify(user));
      set({
        user,
        isAuthenticated: true,
        isAdmin: user.role_id === 1,
      });
      return user;
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("auth_user");
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isAdmin: false,
      });
      return null;
    }
  },

  login: async (email: string, role_id: number = 2, full_name?: string) => {
    set({ isLoading: true });
    try {
      const response = await apiClient.post<AuthResponse>("/auth/login", {
        email,
        role_id,
        full_name,
      });
      const { access_token, user } = response.data;
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("auth_user", JSON.stringify(user));
      set({
        token: access_token,
        user,
        isAuthenticated: true,
        isAdmin: user.role_id === 1,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  loginWithGoogle: async (idToken: string) => {
    set({ isLoading: true });
    try {
      const response = await apiClient.post<AuthResponse>("/auth/google", {
        id_token: idToken,
      });
      const { access_token, user } = response.data;
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("auth_user", JSON.stringify(user));
      set({
        token: access_token,
        user,
        isAuthenticated: true,
        isAdmin: user.role_id === 1,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      // Ignored if server session already expired
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("auth_user");
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isAdmin: false,
      });
    }
  },
}));

