"use client";

import { useState, useEffect } from "react";
import { Mic, Moon, Sun } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

// Landing page components
import Navbar from "@/components/shared/Navbar";
import HeroSection from "@/components/landing/HeroSection";
import FeaturesSection from "@/components/landing/FeaturesSection";
import PricingSection from "@/components/landing/PricingSection";
import AuthModal from "@/components/auth/AuthModal";

// Dashboard components
import Sidebar from "@/components/dashboard/Sidebar";
import GenerateTab from "@/components/dashboard/GenerateTab";
import HistoryTab from "@/components/dashboard/HistoryTab";
import KnowledgeTab from "@/components/dashboard/KnowledgeTab";
import CreditsTab from "@/components/dashboard/CreditsTab";
import SettingsTab from "@/components/dashboard/SettingsTab";
import AdminPanel from "@/components/dashboard/AdminPanel";

// ============================================================
// Main Page Component
// ============================================================

export default function Home() {
  // 自定义 Hook 把认证相关的多个 state 和事件处理函数集中起来，页面只负责组合 UI。
  const auth = useAuth();
  const [darkMode, setDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState("generate");

  useEffect(() => {
    // effect 处理“副作用”：这里直接操作浏览器 document，而不是返回 JSX。
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  // 条件渲染：同一个路由根据 user 是否存在，显示落地页或登录后的控制台。
  if (!auth.user) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-950">
        <Navbar
          darkMode={darkMode}
          setDarkMode={setDarkMode}
          openLogin={auth.openLogin}
          openRegister={auth.openRegister}
        />
        <HeroSection openLogin={auth.openLogin} openRegister={auth.openRegister} />
        <FeaturesSection />
        <PricingSection openRegister={auth.openRegister} />

        {/* Footer */}
        <footer className="py-12 px-6 border-t border-gray-200 dark:border-gray-800">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded bg-indigo-600 flex items-center justify-center">
                <Mic className="w-3 h-3 text-white" />
              </div>
              <span className="font-bold text-gray-900 dark:text-white">PodCraft</span>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400">© 2026 PodCraft. All rights reserved.</p>
          </div>
        </footer>

        <AuthModal
          showAuth={auth.showAuth}
          authMode={auth.authMode}
          authForm={auth.authForm}
          authLoading={auth.authLoading}
          authError={auth.authError}
          setShowAuth={auth.setShowAuth}
          setAuthMode={auth.setAuthMode}
          setAuthForm={auth.setAuthForm}
          handleAuth={auth.handleAuth}
        />
      </div>
    );
  }

  // ---- Dashboard (logged in) ----
  const handleTabChange = (tab: string) => {
    // Tabs like history/credits/admin load data on mount via useEffect in their components
    setActiveTab(tab);
  };

  return (
    <div className="min-h-screen flex bg-gray-50 dark:bg-gray-950">
      <Sidebar
        user={auth.user}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onTabChange={handleTabChange}
        handleLogout={auth.handleLogout}
      />

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6 md:p-10 max-w-5xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                {activeTab === "generate" && "生成播客"}
                {activeTab === "history" && "历史记录"}
                {activeTab === "knowledge" && "知识库"}
                {activeTab === "credits" && "积分充值"}
                {activeTab === "settings" && "设置"}
                {activeTab === "admin" && "管理后台"}
              </h1>
            </div>
            <button onClick={() => setDarkMode(!darkMode)}
              className="p-2 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-800 transition">
              {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            </button>
          </div>

          {/* Tab content */}
          {activeTab === "generate" && <GenerateTab onUnauthorized={auth.openLogin} />}
          {activeTab === "history" && <HistoryTab />}
          {activeTab === "knowledge" && <KnowledgeTab />}
          {activeTab === "credits" && <CreditsTab user={auth.user} />}
          {activeTab === "settings" && <SettingsTab darkMode={darkMode} setDarkMode={setDarkMode} />}
          {activeTab === "admin" && auth.user.is_admin && <AdminPanel />}
        </div>
      </main>

      {/* Auth modal (for re-auth on 401) */}
      <AuthModal
        showAuth={auth.showAuth}
        authMode={auth.authMode}
        authForm={auth.authForm}
        authLoading={auth.authLoading}
        authError={auth.authError}
        setShowAuth={auth.setShowAuth}
        setAuthMode={auth.setAuthMode}
        setAuthForm={auth.setAuthForm}
        handleAuth={auth.handleAuth}
      />
    </div>
  );
}
