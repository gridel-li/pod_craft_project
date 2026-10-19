"use client";

import { useState } from "react";
import { Upload, Search, FileText } from "lucide-react";
import { authHeaders } from "@/hooks/useApi";

export default function KnowledgeTab() {
  const [docTitle, setDocTitle] = useState("");
  const [docContent, setDocContent] = useState("");
  const [docSource, setDocSource] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const uploadDoc = async () => {
    // 当前上传的是“粘贴的纯文本”，不是 multipart 文件上传；后端随后负责切块和写入向量库。
    if (!docTitle.trim() || !docContent.trim()) return;
    await fetch("/api/knowledge", {
      method: "POST",
      headers: authHeaders(),
      body: JSON.stringify({ title: docTitle, content: docContent, source: docSource }),
    });
    setDocTitle(""); setDocContent(""); setDocSource("");
  };

  const handleSearch = async () => {
    // encodeURIComponent 防止中文、空格、& 等字符破坏 query string。
    if (!searchQuery.trim()) return;
    const res = await fetch(`/api/knowledge/search?query=${encodeURIComponent(searchQuery)}&top_k=5`, { headers: authHeaders() });
    const data = await res.json();
    setSearchResults(data.results || []);
  };

  return (
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
  );
}
