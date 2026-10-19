"use client";

import { useState, useEffect } from "react";
import { History, Trash2 } from "lucide-react";
import { MOODS } from "@/lib/constants";
import { authHeaders } from "@/hooks/useApi";
import type { Task } from "@/lib/types";

export default function HistoryTab() {
  const [tasks, setTasks] = useState<Task[]>([]);

  const loadHistory = async () => {
    // 组件挂载时拉取历史；真正生产场景还应处理 loading、错误、分页和用户权限隔离。
    const res = await fetch("/api/podcasts?limit=50", { headers: authHeaders() });
    const data = await res.json();
    setTasks(data.tasks || []);
  };

  const deleteTask = async (id: string) => {
    await fetch(`/api/podcasts/${id}`, { method: "DELETE", headers: authHeaders() });
    loadHistory();
  };

  // 空依赖数组 [] 表示 effect 只在该组件首次挂载时运行一次。
  useEffect(() => { loadHistory(); }, []);

  return (
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
  );
}
