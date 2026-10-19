"use client";

import { MOODS, STYLES, VOICES } from "@/lib/constants";

interface SettingsTabProps {
  darkMode: boolean;
  setDarkMode: (v: boolean) => void;
}

export default function SettingsTab({ darkMode, setDarkMode }: SettingsTabProps) {
  return (
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
  );
}
