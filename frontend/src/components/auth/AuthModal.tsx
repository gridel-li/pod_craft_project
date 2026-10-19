"use client";

import { motion } from "framer-motion";
import { Loader2, X } from "lucide-react";

interface AuthModalProps {
  showAuth: boolean;
  authMode: "login" | "register";
  authForm: { username: string; email: string; password: string };
  authLoading: boolean;
  authError: string;
  setShowAuth: (v: boolean) => void;
  setAuthMode: (v: "login" | "register") => void;
  setAuthForm: React.Dispatch<React.SetStateAction<{ username: string; email: string; password: string }>>;
  handleAuth: () => void;
}

export default function AuthModal({
  showAuth, authMode, authForm, authLoading, authError,
  setShowAuth, setAuthMode, setAuthForm, handleAuth,
}: AuthModalProps) {
  if (!showAuth) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md p-8 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 shadow-xl">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{authMode === "login" ? "登录" : "注册"}</h2>
          <button onClick={() => setShowAuth(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="space-y-4">
          {authMode === "register" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">用户名</label>
              <input type="text" value={authForm.username} onChange={e => setAuthForm(f => ({ ...f, username: e.target.value }))}
                placeholder="你的名字"
                className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500" />
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">邮箱</label>
            <input type="email" value={authForm.email} onChange={e => setAuthForm(f => ({ ...f, email: e.target.value }))}
              placeholder="your@email.com"
              className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">密码</label>
            <input type="password" value={authForm.password} onChange={e => setAuthForm(f => ({ ...f, password: e.target.value }))}
              placeholder="至少 6 位"
              className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500" />
          </div>
          {authError && <p className="text-sm text-red-500">{authError}</p>}
          <button onClick={handleAuth} disabled={authLoading}
            className="w-full py-3 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
            {authLoading ? <Loader2 className="w-4 h-4 inline mr-2 animate-spin" /> : null}
            {authMode === "login" ? "登录" : "注册"}
          </button>
          <p className="text-center text-sm text-gray-500 dark:text-gray-400">
            {authMode === "login" ? "没有账号？" : "已有账号？"}
            <button onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}
              className="text-indigo-600 hover:underline ml-1">
              {authMode === "login" ? "注册" : "登录"}
            </button>
          </p>
        </div>
      </motion.div>
    </div>
  );
}
