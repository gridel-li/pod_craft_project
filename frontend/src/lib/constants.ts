/**
 * App-wide constants — moods, styles, voices, features, pricing plans.
 */

import { Bot, Headphones, Layers, Volume2, Clock, Shield } from "lucide-react";

export const MOODS = [
  { id: "neutral", name: "自然", emoji: "🌿" },
  { id: "excited", name: "兴奋", emoji: "🔥" },
  { id: "calm", name: "平静", emoji: "🌊" },
  { id: "humorous", name: "幽默", emoji: "😄" },
  { id: "serious", name: "严肃", emoji: "📚" },
];

export const STYLES = [
  { id: "narrative", name: "叙述" },
  { id: "conversational", name: "对话" },
  { id: "educational", name: "教育" },
  { id: "storytelling", name: "故事" },
];

export const VOICES = ["冰糖", "茉莉", "苏打", "白桦", "Mia", "Chloe"];

// 展示数据与组件分离：页面通过 map 渲染数组，新增功能卡片时无需复制 JSX。
export const FEATURES = [
  { icon: Bot, title: "多 Agent 协作", desc: "心情分析→内容规划→脚本生成→质量审查" },
  { icon: Headphones, title: "高质量语音", desc: "8 种内置语音，中英文支持" },
  { icon: Layers, title: "RAG 知识增强", desc: "上传参考资料，生成更专业的脚本" },
  { icon: Volume2, title: "音频处理", desc: "自动拼接、淡入淡出、BGM 混音" },
  { icon: Clock, title: "实时进度", desc: "生成过程实时显示" },
  { icon: Shield, title: "安全可靠", desc: "数据加密，API Key 安全管理" },
];

export const PLANS = [
  { name: "免费版", price: "¥0", credits: 5, features: ["每月 5 次生成", "基础语音", "标准质量"] },
  { name: "专业版", price: "¥49", credits: 50, features: ["每月 50 次生成", "全部语音", "高质量", "RAG 增强"], popular: true },
  { name: "企业版", price: "¥199", credits: 200, features: ["每月 200 次生成", "全部语音", "最高质量", "API 接口"] },
];
