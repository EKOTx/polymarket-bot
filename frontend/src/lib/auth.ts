/**
 * Auth store — simple localStorage-based JWT management.
 * Zustand store gives us reactive auth state across components.
 */

import { create } from "zustand";
import { authApi, UserResponse } from "./api";

interface AuthState {
  token: string | null;
  user: UserResponse | null;
  isLoading: boolean;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name?: string) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export const useAuth = create<AuthState>((set) => ({
  token: getStoredToken(),
  user: null,
  isLoading: false,

  login: async (email, password) => {
    const data = await authApi.login(email, password);
    localStorage.setItem("access_token", data.access_token);
    const user = await authApi.me();
    set({ token: data.access_token, user });
  },

  register: async (email, password, full_name) => {
    const data = await authApi.register(email, password, full_name);
    localStorage.setItem("access_token", data.access_token);
    const user = await authApi.me();
    set({ token: data.access_token, user });
  },

  logout: () => {
    localStorage.removeItem("access_token");
    set({ token: null, user: null });
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  },

  loadUser: async () => {
    const token = getStoredToken();
    if (!token) return;
    set({ isLoading: true });
    try {
      const user = await authApi.me();
      set({ token, user, isLoading: false });
    } catch {
      localStorage.removeItem("access_token");
      set({ token: null, user: null, isLoading: false });
    }
  },
}));
