import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PodCraft — AI 播客生成器",
  description: "输入主题，AI 自动生成完整播客",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="min-h-screen font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
