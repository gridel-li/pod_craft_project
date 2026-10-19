"use client";

import { useState, useEffect } from "react";
import { Check } from "lucide-react";
import { PLANS } from "@/lib/constants";
import { authHeaders } from "@/hooks/useApi";
import type { User } from "@/lib/types";

interface CreditsTabProps {
  user: User;
}

export default function CreditsTab({ user }: CreditsTabProps) {
  const [creditLogs, setCreditLogs] = useState<any[]>([]);

  const loadMyCreditLogs = async () => {
    try {
      const res = await fetch("/api/auth/me/credits", { headers: authHeaders() });
      if (res.ok) { const data = await res.json(); setCreditLogs(data.logs || []); }
    } catch {}
  };

  // Load credit logs on mount
  useEffect(() => { loadMyCreditLogs(); }, []);

  return (
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
  );
}
