"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Sparkles, Loader2 } from "lucide-react";
import { MOODS, STYLES, VOICES } from "@/lib/constants";
import { authHeaders } from "@/hooks/useApi";
import type { Task } from "@/lib/types";

interface GenerateTabProps {
  onUnauthorized: () => void;
}

export default function GenerateTab({ onUnauthorized }: GenerateTabProps) {
  const [topic, setTopic] = useState("");
  const [mood, setMood] = useState("neutral");
  const [style, setStyle] = useState("narrative");
  const [voice, setVoice] = useState("冰糖");
  const [duration, setDuration] = useState(5);
  const [generating, setGenerating] = useState(false);
  const [currentTask, setCurrentTask] = useState<Task | null>(null);

  const pollTask = (taskId: string) => {
    // 轮询是实现异步任务进度的简单方式：客户端定时请求，直到服务端给出终态。
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/podcasts/${taskId}`, { headers: authHeaders() });
        const task = await res.json();
        setCurrentTask(task);
        // completed / failed 是终态，必须 clearInterval，否则组件会一直产生网络请求。
        if (task.status === "completed" || task.status === "failed") {
          setGenerating(false);
          clearInterval(interval);
        }
      } catch { clearInterval(interval); setGenerating(false); }
    }, 2000);
  };

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setGenerating(true);
    setCurrentTask(null);
    try {
      // await 不会冻结浏览器；它只暂停本 async 函数，网络完成后从这里继续。
      const res = await fetch("/api/podcasts/generate", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ topic, mood, style, duration_min: duration, voice, use_rag: true }),
      });
      if (res.status === 401) { onUnauthorized(); setGenerating(false); return; }
      const task = await res.json();
      setCurrentTask(task);
      pollTask(task.id);
    } catch { setGenerating(false); }
  };

  return (
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

      {/* Task progress */}
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
  );
}
