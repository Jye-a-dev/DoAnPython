"use client";

import { create } from "zustand";
import { authService, LoginPayload } from "@/services/auth.service";
import { User } from "@/types";

function syncCookies(token: string | null, roleId?: number | null) {
  if (typeof document === "undefined") return;
  if (token) {
    document.cookie = `auth_token=${token}; path=/; max-age=604800; SameSite=Lax`;
    if (roleId !== undefined && roleId !== null) {
      document.cookie = `auth_role=${roleId}; path=/; max-age=604800; SameSite=Lax`;
    }
  } else {
    document.cookie = "auth_token=; path=/; max-age=0; SameSite=Lax";
    document.cookie = "auth_role=; path=/; max-age=0; SameSite=Lax";
  }
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  register: (email: string, password: string, fullName?: string) => Promise<User>;
  login: (
    email: string,
    passwordOrRoleId?: string | number,
    roleIdOrFullName?: number | string,
    fullName?: string
  ) => Promise<User>;
  loginWithGoogle: (idToken: string) => Promise<User>;
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

      syncCookies(token, initialUser?.role_id);

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
        // Handled inside fetchMe
      } finally {
        set({ isLoading: false });
      }
    } else {
      syncCookies(null);
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
      syncCookies(null);
      localStorage.removeItem("access_token");
      localStorage.removeItem("auth_user");
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isAdmin: false,
        isLoading: false,
      });

      if (typeof window !== "undefined") {
        const path = window.location.pathname;
        if (
          path.startsWith("/admin") ||
          path.startsWith("/profile") ||
          path.startsWith("/orders")
        ) {
          window.location.href = `/login?redirect=${encodeURIComponent(path)}`;
        }
      }
    });
  },

  fetchMe: async () => {
    try {
      const response = await authService.getMe();
      const user = response.data;
      localStorage.setItem("auth_user", JSON.stringify(user));
      const token = localStorage.getItem("access_token");
      syncCookies(token, user.role_id);
      set({
        user,
        isAuthenticated: true,
        isAdmin: user.role_id === 1,
      });
      return user;
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("auth_user");
      syncCookies(null);
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isAdmin: false,
      });
      return null;
    }
  },

  register: async (
    email: string,
    password: string,
    fullName?: string
  ): Promise<User> => {
    set({ isLoading: true });
    try {
      const response = await authService.register({
        email: email.trim().toLowerCase(),
        password,
        full_name: fullName?.trim() || undefined,
      });
      const { access_token, user } = response.data;
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("auth_user", JSON.stringify(user));
      syncCookies(access_token, user.role_id);
      set({
        token: access_token,
        user,
        isAuthenticated: true,
        isAdmin: user.role_id === 1,
        isLoading: false,
      });
      return user;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  login: async (
    email: string,
    passwordOrRoleId?: string | number,
    roleIdOrFullName?: number | string,
    fullName?: string
  ): Promise<User> => {
    set({ isLoading: true });
    try {
      let password: string | undefined;
      let role_id: number | undefined;
      let full_name: string | undefined;

      if (typeof passwordOrRoleId === "number") {
        role_id = passwordOrRoleId;
        if (typeof roleIdOrFullName === "string") {
          full_name = roleIdOrFullName;
        }
      } else if (typeof passwordOrRoleId === "string") {
        password = passwordOrRoleId;
        if (typeof roleIdOrFullName === "number") {
          role_id = roleIdOrFullName;
        }
        if (typeof fullName === "string") {
          full_name = fullName;
        }
      }

      const payload: LoginPayload = {
        email: email.trim().toLowerCase(),
      };
      if (password) payload.password = password;
      if (role_id !== undefined) payload.role_id = role_id;
      if (full_name) payload.full_name = full_name;

      const response = await authService.login(payload);
      const { access_token, user } = response.data;
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("auth_user", JSON.stringify(user));
      syncCookies(access_token, user.role_id);
      set({
        token: access_token,
        user,
        isAuthenticated: true,
        isAdmin: user.role_id === 1,
        isLoading: false,
      });
      return user;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  loginWithGoogle: async (idToken: string): Promise<User> => {
    set({ isLoading: true });
    try {
      const response = await authService.loginWithGoogle(idToken);
      const { access_token, user } = response.data;
      localStorage.setItem("access_token", access_token);
      localStorage.setItem("auth_user", JSON.stringify(user));
      syncCookies(access_token, user.role_id);
      set({
        token: access_token,
        user,
        isAuthenticated: true,
        isAdmin: user.role_id === 1,
        isLoading: false,
      });
      return user;
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    try {
      await authService.logout();
    } catch {
      // Ignored if server session already expired
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("auth_user");
      syncCookies(null);
      set({
        token: null,
        user: null,
        isAuthenticated: false,
        isAdmin: false,
        isLoading: false,
      });

      if (typeof window !== "undefined") {
        const path = window.location.pathname;
        if (
          path.startsWith("/admin") ||
          path.startsWith("/profile") ||
          path.startsWith("/orders")
        ) {
          window.location.href = "/login";
        }
      }
    }
  },
}));