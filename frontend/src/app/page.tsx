"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Mic, Sparkles, History, BookOpen, Loader2, Trash2, Search, Upload, FileText,
  Zap, ArrowRight, Check, Volume2, Clock, Layers, Bot, Headphones, Shield,
  Moon, Sun, LogOut, Settings, CreditCard, User, ChevronRight, Play, X, Menu
} from "lucide-react";

// ============================================================
// 常量
// ============================================================

const MOODS = [
  { id: "neutral", name: "自然", emoji: "🌿" },
  { id: "excited", name: "兴奋", emoji: "🔥" },
  { id: "calm", name: "平静", emoji: "🌊" },
  { id: "humorous", name: "幽默", emoji: "😄" },
  { id: "serious", name: "严肃", emoji: "📚" },
];

const STYLES = [
  { id: "narrative", name: "叙述" },
  { id: "conversational", name: "对话" },
  { id: "educational", name: "教育" },
  { id: "storytelling", name: "故事" },
];

const VOICES = ["冰糖", "茉莉", "苏打", "白桦", "Mia", "Chloe"];

const FEATURES = [
  { icon: Bot, title: "多 Agent 协作", desc: "心情分析→内容规划→脚本生成→质量审查" },
  { icon: Headphones, title: "高质量语音", desc: "8 种内置语音，中英文支持" },
  { icon: Layers, title: "RAG 知识增强", desc: "上传参考资料，生成更专业的脚本" },
  { icon: Volume2, title: "音频处理", desc: "自动拼接、淡入淡出、BGM 混音" },
  { icon: Clock, title: "实时进度", desc: "生成过程实时显示" },
  { icon: Shield, title: "安全可靠", desc: "数据加密，API Key 安全管理" },
];

const PLANS = [
  { name: "免费版", price: "¥0", credits: 5, features: ["每月 5 次生成", "基础语音", "标准质量"] },
  { name: "专业版", price: "¥49", credits: 50, features: ["每月 50 次生成", "全部语音", "高质量", "RAG 增强"], popular: true },
  { name: "企业版", price: "¥199", credits: 200, features: ["每月 200 次生成", "全部语音", "最高质量", "API 接口"] },
];

// ============================================================
// 类型
// ============================================================

interface User {
  id: string;
  username: string;
  email: string;
  credits: number;
  plan: string;
  is_admin?: boolean;
}

interface Task {
  id: string;
  topic: string;
  mood: string;
  style: string;
  status: string;
  progress: number;
  current_step: string;
  title: string;
  audio_path: string;
  duration_sec: number;
  segments: { type: string; content: string; duration_sec: number }[];
  error_message: string;
  created_at: string;
}

// ============================================================
// 主组件
// ============================================================

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [darkMode, setDarkMode] = useState(false);
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authForm, setAuthForm] = useState({ username: "", email: "", password: "" });
  const [topic, setTopic] = useState("");
  const [mood, setMood] = useState("neutral");
  const [style, setStyle] = useState("narrative");
  const [voice, setVoice] = useState("冰糖");
  const [duration, setDuration] = useState(5);
  const [generating, setGenerating] = useState(false);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [docTitle, setDocTitle] = useState("");
  const [docContent, setDocContent] = useState("");
  const [docSource, setDocSource] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState("generate");
  const [adminUsers, setAdminUsers] = useState<any[]>([]);
  const [adminStats, setAdminStats] = useState<any>(null);
  const [rechargeUserId, setRechargeUserId] = useState("");
  const [rechargeAmount, setRechargeAmount] = useState(10);
  const [creditLogs, setCreditLogs] = useState<any[]>([]);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
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

  const authHeaders = (): Record<string, string> => {
    const token = localStorage.getItem("token");
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return headers;
  };

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setGenerating(true);
    setCurrentTask(null);
    try {
      const res = await fetch("/api/podcasts/generate", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ topic, mood, style, duration_min: duration, voice, use_rag: true }),
      });
      if (res.status === 401) { setShowAuth(true); setGenerating(false); return; }
      const task = await res.json();
      setCurrentTask(task);
      pollTask(task.id);
    } catch { setGenerating(false); }
  };

  const pollTask = (taskId: string) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/podcasts/${taskId}`, { headers: authHeaders() });
        const task = await res.json();
        setCurrentTask(task);
        if (task.status === "completed" || task.status === "failed") {
          setGenerating(false);
          clearInterval(interval);
        }
      } catch { clearInterval(interval); setGenerating(false); }
    }, 2000);
  };

  const loadHistory = async () => {
    const res = await fetch("/api/podcasts?limit=50", { headers: authHeaders() });
    const data = await res.json();
    setTasks(data.tasks || []);
  };

  const deleteTask = async (id: string) => {
    await fetch(`/api/podcasts/${id}`, { method: "DELETE", headers: authHeaders() });
    loadHistory();
  };

  const uploadDoc = async () => {
    if (!docTitle.trim() || !docContent.trim()) return;
    await fetch("/api/knowledge", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ title: docTitle, content: docContent, source: docSource }),
    });
    setDocTitle(""); setDocContent(""); setDocSource("");
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    const res = await fetch(`/api/knowledge/search?query=${encodeURIComponent(searchQuery)}&top_k=5`, { headers: authHeaders() });
    const data = await res.json();
    setSearchResults(data.results || []);
  };

  const loadAdminUsers = async () => {
    try {
      const res = await fetch("/api/admin/users", { headers: authHeaders() });
      if (res.ok) { const data = await res.json(); setAdminUsers(data); }
    } catch {}
  };

  const loadAdminStats = async () => {
    try {
      const res = await fetch("/api/admin/stats", { headers: authHeaders() });
      if (res.ok) { const data = await res.json(); setAdminStats(data); }
    } catch {}
  };

  const handleRecharge = async (userId: string) => {
    if (rechargeAmount <= 0) return;
    await fetch(`/api/admin/users/${userId}/credits`, {
      method: "POST", headers: authHeaders(),
      body: JSON.stringify({ amount: rechargeAmount, reason: "Admin recharge" }),
    });
    loadAdminUsers();
  };

  const loadMyCreditLogs = async () => {
    try {
      const res = await fetch("/api/auth/me/credits", { headers: authHeaders() });
      if (res.ok) { const data = await res.json(); setCreditLogs(data.logs || []); }
    } catch {}
  };

  // ============================================================
  // 着陆页
  // ============================================================

  if (!user) {
    return (
      <div className="min-h-screen bg-white dark:bg-gray-950">
        {/* 导航 */}
        <nav className="fixed top-0 w-full z-50 bg-white/80 dark:bg-gray-950/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-800">
          <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                <Mic className="w-4 h-4 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900 dark:text-white">PodCraft</span>
            </div>
            <div className="flex items-center gap-4">
              <button onClick={() => setDarkMode(!darkMode)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition">
                {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
              <button onClick={() => { setAuthMode("login"); setShowAuth(true); }}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition">
                登录
              </button>
              <button onClick={() => { setAuthMode("register"); setShowAuth(true); }}
                className="px-4 py-2 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition">
                免费开始
              </button>
            </div>
          </div>
        </nav>

        {/* Hero */}
        <section className="pt-32 pb-20 px-6">
          <div className="max-w-4xl mx-auto text-center">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 text-sm mb-8">
                <Zap className="w-4 h-4" /> AI 驱动的播客生成平台
              </div>
              <h1 className="text-5xl md:text-6xl font-bold mb-6 tracking-tight text-gray-900 dark:text-white">
                一句话，<br />
                <span className="bg-gradient-to-r from-indigo-600 to-pink-500 bg-clip-text text-transparent">生成完整播客</span>
              </h1>
              <p className="text-xl text-gray-500 dark:text-gray-400 mb-10 max-w-2xl mx-auto">
                输入主题，AI 自动完成脚本撰写、语音合成、音频处理。<br />支持多种心情风格，RAG 知识增强。
              </p>
              <div className="flex items-center justify-center gap-4">
                <button onClick={() => { setAuthMode("register"); setShowAuth(true); }}
                  className="px-8 py-4 text-lg font-medium bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition">
                  免费开始 <ArrowRight className="w-5 h-5 inline ml-2" />
                </button>
                <button onClick={() => { setAuthMode("login"); setShowAuth(true); }}
                  className="px-8 py-4 text-lg font-medium border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-900 transition">
                  登录
                </button>
              </div>
            </motion.div>
          </div>
        </section>

        {/* 功能 */}
        <section className="py-20 px-6 bg-gray-50 dark:bg-gray-900">
          <div className="max-w-6xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">强大功能</h2>
              <p className="text-gray-500 dark:text-gray-400">从主题到完整播客，AI 全程处理</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {FEATURES.map(({ icon: Icon, title, desc }, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }} viewport={{ once: true }}
                  className="p-6 rounded-2xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 hover:shadow-lg transition">
                  <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center mb-4">
                    <Icon className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">{title}</h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{desc}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* 定价 */}
        <section className="py-20 px-6">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">简单定价</h2>
              <p className="text-gray-500 dark:text-gray-400">选择适合你的方案</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {PLANS.map((plan, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.1 }} viewport={{ once: true }}
                  className={`p-6 rounded-2xl border ${plan.popular ? "border-indigo-500 shadow-lg" : "border-gray-200 dark:border-gray-700"} bg-white dark:bg-gray-800 relative`}>
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-indigo-600 text-white text-xs font-medium">
                      最受欢迎
                    </div>
                  )}
                  <h3 className="font-bold text-gray-900 dark:text-white mb-2">{plan.name}</h3>
                  <div className="mb-4">
                    <span className="text-3xl font-bold text-gray-900 dark:text-white">{plan.price}</span>
                    <span className="text-gray-500 dark:text-gray-400">/月</span>
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">每月 {plan.credits} 次生成额度</p>
                  <ul className="space-y-2 mb-6">
                    {plan.features.map((f, j) => (
                      <li key={j} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                        <Check className="w-4 h-4 text-indigo-600" /> {f}
                      </li>
                    ))}
                  </ul>
                  <button onClick={() => { setAuthMode("register"); setShowAuth(true); }}
                    className={`w-full py-3 rounded-xl font-medium transition ${plan.popular ? "bg-indigo-600 text-white hover:bg-indigo-700" : "border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900"}`}>
                    开始使用
                  </button>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

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

        {/* 登录弹窗 */}
        {showAuth && (
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
        )}
      </div>
    );
  }

  // ============================================================
  // 仪表盘
  // ============================================================

  return (
    <div className="min-h-screen flex bg-gray-50 dark:bg-gray-950">
      {/* 侧边栏 */}
      <aside className="w-64 border-r border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 hidden md:flex flex-col">
        <div className="p-6 border-b border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
              <Mic className="w-4 h-4 text-white" />
            </div>
            <span className="text-lg font-bold text-gray-900 dark:text-white">PodCraft</span>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {[
            { key: "generate", icon: Sparkles, label: "生成播客" },
            { key: "history", icon: History, label: "历史记录" },
            { key: "knowledge", icon: BookOpen, label: "知识库" },
            { key: "credits", icon: CreditCard, label: "积分充值" },
            { key: "settings", icon: Settings, label: "设置" },
            ...(user.is_admin ? [{ key: "admin", icon: Shield, label: "管理后台" }] : []),
          ].map(({ key, icon: Icon, label }) => (
            <button key={key}
              onClick={() => {
                setActiveTab(key);
                if (key === "history") loadHistory();
                if (key === "admin") { loadAdminUsers(); loadAdminStats(); }
                if (key === "credits") loadMyCreditLogs();
              }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition ${activeTab === key ? "bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400" : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"}`}>
              <Icon className="w-5 h-5" /> {label}
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 dark:bg-gray-800">
            <div className="w-10 h-10 rounded-full bg-indigo-600 flex items-center justify-center text-white font-bold">
              {user.username[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{user.username}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{user.credits} 积分</p>
            </div>
            <button onClick={handleLogout} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition">
              <LogOut className="w-4 h-4 text-gray-500" />
            </button>
          </div>
        </div>
      </aside>

      {/* 主内容 */}
      <main className="flex-1 overflow-auto">
        <header className="sticky top-0 z-40 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-800 px-6 h-16 flex items-center justify-between">
          <h1 className="text-lg font-bold text-gray-900 dark:text-white">
            {activeTab === "generate" && "生成播客"}
            {activeTab === "history" && "历史记录"}
            {activeTab === "knowledge" && "知识库"}
            {activeTab === "credits" && "积分充值"}
            {activeTab === "settings" && "设置"}
            {activeTab === "admin" && "管理后台"}
          </h1>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-50 dark:bg-indigo-950 text-sm">
              <Zap className="w-4 h-4 text-indigo-600" />
              <span className="font-medium text-indigo-600">{user.credits}</span>
              <span className="text-gray-500">积分</span>
            </div>
            <button onClick={() => setDarkMode(!darkMode)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition">
              {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </header>

        <div className="p-6 max-w-4xl mx-auto">
          {/* 生成页 */}
          {activeTab === "generate" && (
            <div>
              <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8 mb-6">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">创建播客</h2>
                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">播客主题</label>
                  <textarea value={topic} onChange={e => setTopic(e.target.value)}
                    placeholder="例如：AI 时代的生活、为什么年轻人爱养猫..."
                    rows={3}
                    className="w-full px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-indigo-500 text-lg resize-none" />
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">心情</label>
                    <select value={mood} onChange={e => setMood(e.target.value)}
                      className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none text-sm">
                      {MOODS.map(m => <option key={m.id} value={m.id}>{m.emoji} {m.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">风格</label>
                    <select value={style} onChange={e => setStyle(e.target.value)}
                      className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none text-sm">
                      {STYLES.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">语音</label>
                    <select value={voice} onChange={e => setVoice(e.target.value)}
                      className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none text-sm">
                      {VOICES.map(v => <option key={v} value={v}>{v}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">时长 ({duration}分钟)</label>
                    <input type="range" min={1} max={15} value={duration} onChange={e => setDuration(Number(e.target.value))}
                      className="w-full accent-indigo-600" />
                  </div>
                </div>
                <button onClick={handleGenerate} disabled={!topic.trim() || generating}
                  className="w-full py-4 rounded-xl bg-indigo-600 text-white font-medium text-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-indigo-700 transition">
                  {generating ? <Loader2 className="w-5 h-5 inline mr-2 animate-spin" /> : <Sparkles className="w-5 h-5 inline mr-2" />}
                  {generating ? "生成中..." : "开始生成"}
                </button>
              </div>

              {/* 进度 */}
              {currentTask && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                  className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 p-8">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-white">{currentTask.title || currentTask.topic}</h3>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${currentTask.status === "completed" ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                      : currentTask.status === "failed" ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                        : "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300"}`}>
                      {currentTask.status === "completed" ? "✅ 完成" : currentTask.status === "failed" ? "❌ 失败" : `⏳ ${currentTask.current_step}`}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-2">
                    <motion.div className="h-3 rounded-full bg-indigo-600"
                      initial={{ width: 0 }} animate={{ width: `${currentTask.progress}%` }} />
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">{Math.round(currentTask.progress)}%</p>

                  {currentTask.status === "completed" && currentTask.audio_path && (
                    <div className="mb-6">
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">音频</label>
                      <audio controls className="w-full" src={`/files/${currentTask.audio_path.split("/").pop()}`} />
                    </div>
                  )}

                  {currentTask.segments?.length > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">脚本</label>
                      <div className="space-y-3">
                        {currentTask.segments.map((seg, i) => (
                          <div key={i} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                            <span className="text-xs font-medium text-indigo-600 uppercase">{seg.type}</span>
                            <p className="text-sm mt-2 text-gray-700 dark:text-gray-300 leading-relaxed">{seg.content}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {currentTask.error_message && (
                    <div className="mt-4 p-4 bg-red-50 dark:bg-red-950 rounded-xl text-red-700 dark:text-red-300 text-sm">
                      {currentTask.error_message}
                    </div>
                  )}
                </motion.div>
              )}
            </div>
          )}

          {/* 历史页 */}
          {activeTab === "history" && (
            <div>
              {tasks.length === 0 ? (
                <div className="text-center py-20">
                  <History className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
                  <p className="text-gray-500 dark:text-gray-400">暂无记录</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {tasks.map((task) => (
                    <div key={task.id} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white">{task.title || task.topic}</h3>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-1 rounded text-xs font-medium ${task.status === "completed" ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                            : task.status === "failed" ? "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300"
                              : "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300"}`}>
                            {task.status === "completed" ? "完成" : task.status === "failed" ? "失败" : "进行中"}
                          </span>
                          <button onClick={() => deleteTask(task.id)} className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition">
                            <Trash2 className="w-4 h-4 text-gray-400" />
                          </button>
                        </div>
                      </div>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
                        {task.topic} · {MOODS.find(m => m.id === task.mood)?.name || task.mood}
                        {task.duration_sec > 0 && ` · ${Math.round(task.duration_sec)}秒`}
                      </p>
                      {task.status === "completed" && task.audio_path && (
                        <audio controls className="w-full" src={`/files/${task.audio_path.split("/").pop()}`} />
                      )}
                      {task.segments?.length > 0 && (
                        <details className="mt-3">
                          <summary className="text-sm text-indigo-600 cursor-pointer hover:underline">查看脚本</summary>
                          <div className="mt-2 space-y-2">
                            {task.segments.map((seg, i) => (
                              <div key={i} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-sm">
                                <span className="text-xs font-medium text-indigo-600 uppercase">{seg.type}</span>
                                <p className="mt-1 text-gray-700 dark:text-gray-300">{seg.content}</p>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 知识库页 */}
          {activeTab === "knowledge" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
                <h3 className="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <Upload className="w-5 h-5" /> 上传文档
                </h3>
                <div className="space-y-4">
                  <input type="text" value={docTitle} onChange={e => setDocTitle(e.target.value)}
                    placeholder="文档标题"
                    className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none text-sm" />
                  <input type="text" value={docSource} onChange={e => setDocSource(e.target.value)}
                    placeholder="来源（wiki/news/report）"
                    className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none text-sm" />
                  <textarea value={docContent} onChange={e => setDocContent(e.target.value)}
                    placeholder="粘贴文档内容..." rows={8}
                    className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none text-sm resize-none" />
                  <button onClick={uploadDoc} disabled={!docTitle.trim() || !docContent.trim()}
                    className="w-full py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-medium disabled:opacity-50 hover:bg-indigo-700 transition">
                    上传
                  </button>
                </div>
              </div>
              <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
                <h3 className="font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <Search className="w-5 h-5" /> 检索
                </h3>
                <div className="flex gap-2 mb-4">
                  <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)}
                    placeholder="检索关键词..."
                    className="flex-1 px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none text-sm"
                    onKeyDown={e => e.key === "Enter" && handleSearch()} />
                  <button onClick={handleSearch}
                    className="px-4 py-2.5 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition">
                    检索
                  </button>
                </div>
                {searchResults.length > 0 ? (
                  <div className="space-y-3">
                    {searchResults.map((r, i) => (
                      <div key={i} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-gray-500">{r.metadata?.source || "未知"}</span>
                          <span className="text-xs text-gray-400">{(1 - (r.distance || 0)).toFixed(2)}</span>
                        </div>
                        <p className="text-sm text-gray-700 dark:text-gray-300">{r.content}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-10 text-gray-400">
                    <FileText className="w-8 h-8 mx-auto mb-2" />
                    <p className="text-sm">输入关键词检索</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 积分页 */}
          {activeTab === "credits" && (
            <div>
              <div className="text-center mb-10">
                <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">积分充值</h2>
                <p className="text-gray-500 dark:text-gray-400">当前余额：<span className="text-indigo-600 font-bold text-2xl">{user.credits}</span> 积分</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {PLANS.map((plan, i) => (
                  <div key={i} className={`p-6 rounded-2xl border ${plan.popular ? "border-indigo-500 shadow-lg" : "border-gray-200 dark:border-gray-700"} bg-white dark:bg-gray-900 relative`}>
                    {plan.popular && (
                      <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-indigo-600 text-white text-xs font-medium">推荐</div>
                    )}
                    <h3 className="font-bold text-gray-900 dark:text-white mb-2">{plan.name}</h3>
                    <div className="mb-4">
                      <span className="text-3xl font-bold text-gray-900 dark:text-white">{plan.price}</span>
                      <span className="text-gray-500 dark:text-gray-400">/月</span>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{plan.credits} 积分/月</p>
                    <ul className="space-y-2 mb-6">
                      {plan.features.map((f, j) => (
                        <li key={j} className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                          <Check className="w-4 h-4 text-indigo-600" /> {f}
                        </li>
                      ))}
                    </ul>
                    <button className={`w-full py-3 rounded-xl font-medium transition ${plan.popular ? "bg-indigo-600 text-white hover:bg-indigo-700" : "border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900"}`}>
                      购买
                    </button>
                  </div>
                ))}
              </div>

              {/* Credit Logs */}
              {creditLogs.length > 0 && (
                <div className="mt-8 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
                  <h3 className="font-bold text-gray-900 dark:text-white mb-4">积分记录</h3>
                  <div className="space-y-2">
                    {creditLogs.map((log: any, i: number) => (
                      <div key={i} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div>
                          <p className="text-sm text-gray-700 dark:text-gray-300">{log.reason}</p>
                          <p className="text-xs text-gray-400">{new Date(log.created_at).toLocaleString("zh-CN")}</p>
                        </div>
                        <span className={`text-sm font-bold ${log.amount > 0 ? "text-green-600" : "text-red-500"}`}>
                          {log.amount > 0 ? "+" : ""}{log.amount}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 设置页 */}
          {activeTab === "settings" && (
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">默认语音</label>
                <select className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none">
                  {VOICES.map(v => <option key={v} value={v}>{v}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">默认心情</label>
                <select className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none">
                  {MOODS.map(m => <option key={m.id} value={m.id}>{m.emoji} {m.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">默认风格</label>
                <select className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white outline-none">
                  {STYLES.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">暗色模式</span>
                <button onClick={() => setDarkMode(!darkMode)}
                  className={`w-12 h-6 rounded-full transition ${darkMode ? "bg-indigo-600" : "bg-gray-300"} relative`}>
                  <div className={`w-5 h-5 rounded-full bg-white shadow transition-transform ${darkMode ? "translate-x-6" : "translate-x-0.5"}`} />
                </button>
              </div>
              <button className="w-full py-3 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 transition">
                保存设置
              </button>
            </div>
          )}

          {/* 管理后台 */}
          {activeTab === "admin" && user.is_admin && (
            <div>
              {/* System Stats */}
              {adminStats && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  {[
                    { label: "用户总数", value: adminStats.total_users, color: "text-indigo-600" },
                    { label: "播客总数", value: adminStats.total_tasks, color: "text-blue-600" },
                    { label: "已完成", value: adminStats.completed_tasks, color: "text-green-600" },
                    { label: "积分消耗", value: adminStats.total_credits_used, color: "text-orange-600" },
                  ].map((stat, i) => (
                    <div key={i} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4">
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">{stat.label}</p>
                      <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* User Table */}
              <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
                <h3 className="font-bold text-gray-900 dark:text-white mb-4">用户管理</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-gray-200 dark:border-gray-700">
                        <th className="text-left py-3 px-2 text-gray-500 dark:text-gray-400 font-medium">用户名</th>
                        <th className="text-left py-3 px-2 text-gray-500 dark:text-gray-400 font-medium">邮箱</th>
                        <th className="text-left py-3 px-2 text-gray-500 dark:text-gray-400 font-medium">积分</th>
                        <th className="text-left py-3 px-2 text-gray-500 dark:text-gray-400 font-medium">方案</th>
                        <th className="text-left py-3 px-2 text-gray-500 dark:text-gray-400 font-medium">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {adminUsers.map((u: any) => (
                        <tr key={u.id} className="border-b border-gray-100 dark:border-gray-800">
                          <td className="py-3 px-2 text-gray-900 dark:text-white">
                            {u.username} {u.is_admin && <span className="text-xs text-indigo-600 ml-1">管理员</span>}
                          </td>
                          <td className="py-3 px-2 text-gray-500 dark:text-gray-400">{u.email}</td>
                          <td className="py-3 px-2 font-medium text-gray-900 dark:text-white">{u.credits}</td>
                          <td className="py-3 px-2">
                            <span className="px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400">{u.plan}</span>
                          </td>
                          <td className="py-3 px-2">
                            <div className="flex items-center gap-2">
                              <input type="number" min={1} max={1000} defaultValue={10}
                                onChange={e => setRechargeAmount(Number(e.target.value))}
                                className="w-20 px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm outline-none" />
                              <button onClick={() => handleRecharge(u.id)}
                                className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700 transition">
                                充值
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
