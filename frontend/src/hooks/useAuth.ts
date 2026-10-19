"use client";

import { useState, useEffect } from "react";
import type { User } from "@/lib/types";

/**
 * Custom hook that encapsulates all authentication state and logic.
 *
 * Manages: user session, login/register flow, logout,
 * and auto-loading the user from a persisted token on mount.
 */
export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authForm, setAuthForm] = useState({ username: "", email: "", password: "" });

  // Auto-load user from persisted token on mount
  useEffect(() => {
    // localStorage 只存在于浏览器；因此访问它必须放在 client component 的 effect 中。
    const token = localStorage.getItem("token");
    if (token) {
      // 不直接信任本地缓存的 user，刷新页面后用 token 向后端重新确认身份。
      fetch("/api/auth/me", { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.ok ? r.json() : null)
        .then(u => { if (u) setUser(u); })
        .catch(() => {});
    }
  }, []);

  const handleAuth = async () => {
    setAuthLoading(true);
    setAuthError("");
    try {
      // 三元表达式：根据 mode 选择不同 URL 和 JSON 请求体。
      const endpoint = authMode === "login" ? "/api/auth/login" : "/api/auth/register";
      const body = authMode === "login"
        ? { email: authForm.email, password: authForm.password }
        : { username: authForm.username, email: authForm.email, password: authForm.password };

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();

      if (!res.ok) {
        setAuthError(data.detail || "操作失败");
        return;
      }

      // 此演示将 token 放 localStorage，易用但要防 XSS；生产系统可考虑 HttpOnly Cookie。
      localStorage.setItem("token", data.access_token);
      setUser(data.user);
      setShowAuth(false);
      setAuthForm({ username: "", email: "", password: "" });
    } catch {
      setAuthError("网络错误");
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  const openLogin = () => {
    setAuthMode("login");
    setShowAuth(true);
  };

  const openRegister = () => {
    setAuthMode("register");
    setShowAuth(true);
  };

  return {
    user,
    setUser,
    showAuth,
    setShowAuth,
    authMode,
    setAuthMode,
    authLoading,
    authError,
    authForm,
    setAuthForm,
    handleAuth,
    handleLogout,
    openLogin,
    openRegister,
  };
}
