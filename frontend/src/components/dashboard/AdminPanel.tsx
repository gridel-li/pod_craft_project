"use client";

import { useState, useEffect } from "react";
import { authHeaders } from "@/hooks/useApi";

export default function AdminPanel() {
  const [adminUsers, setAdminUsers] = useState<any[]>([]);
  const [adminStats, setAdminStats] = useState<any>(null);
  const [rechargeAmount, setRechargeAmount] = useState(10);

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

  // Load data on mount
  useEffect(() => { loadAdminUsers(); loadAdminStats(); }, []);

  return (
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
  );
}
