"use client";

import { motion } from "framer-motion";
import { Zap, ArrowRight } from "lucide-react";

interface HeroSectionProps {
  openLogin: () => void;
  openRegister: () => void;
}

export default function HeroSection({ openLogin, openRegister }: HeroSectionProps) {
  return (
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
            <button onClick={openRegister}
              className="px-8 py-4 text-lg font-medium bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition">
              免费开始 <ArrowRight className="w-5 h-5 inline ml-2" />
            </button>
            <button onClick={openLogin}
              className="px-8 py-4 text-lg font-medium border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-900 transition">
              登录
            </button>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
