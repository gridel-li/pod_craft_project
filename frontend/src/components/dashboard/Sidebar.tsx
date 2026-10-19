"use client";

import {
  Mic, Sparkles, History, BookOpen, CreditCard, Settings, Shield, LogOut,
} from "lucide-react";
import type { User } from "@/lib/types";

interface SidebarProps {
  user: User;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onTabChange: (tab: string) => void;
  handleLogout: () => void;
}

const NAV_ITEMS = [
  { key: "generate", icon: Sparkles, label: "生成播客" },
  { key: "history", icon: History, label: "历史记录" },
  { key: "knowledge", icon: BookOpen, label: "知识库" },
  { key: "credits", icon: CreditCard, label: "积分充值" },
  { key: "settings", icon: Settings, label: "设置" },
];

export default function Sidebar({ user, activeTab, setActiveTab, onTabChange, handleLogout }: SidebarProps) {
  // 根据角色动态扩展导航项只是体验优化；真正的管理员权限仍必须由后端校验。
  const items = [
    ...NAV_ITEMS,
    ...(user.is_admin ? [{ key: "admin", icon: Shield, label: "管理后台" }] : []),
  ];

  return (
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
        {items.map(({ key, icon: Icon, label }) => (
          <button key={key}
            onClick={() => {
              setActiveTab(key);
              onTabChange(key);
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
  );
}
