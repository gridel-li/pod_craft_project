"use client";

import { motion } from "framer-motion";
import { Check } from "lucide-react";
import { PLANS } from "@/lib/constants";

interface PricingSectionProps {
  openRegister: () => void;
}

export default function PricingSection({ openRegister }: PricingSectionProps) {
  return (
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
              <button onClick={openRegister}
                className={`w-full py-3 rounded-xl font-medium transition ${plan.popular ? "bg-indigo-600 text-white hover:bg-indigo-700" : "border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-900"}`}>
                开始使用
              </button>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
