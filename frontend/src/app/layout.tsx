import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "保研推免定位器",
  description: "CS专业本科生保研/推免智能定位与推荐系统",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh">
      <body className={inter.className}>
        <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between sticky top-0 z-50 shadow-sm">
          <a href="/" className="flex items-center gap-2">
            <span className="text-2xl">🎓</span>
            <span className="font-bold text-gray-900 text-lg">保研推免定位器</span>
            <span className="text-xs text-gray-400 font-normal ml-1">Beta</span>
          </a>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <a href="/questionnaire" className="hover:text-blue-600 transition-colors">开始测评</a>
            <a href="/admin" className="hover:text-blue-600 transition-colors">管理后台</a>
          </div>
        </nav>
        <main className="min-h-screen">
          {children}
        </main>
        <Toaster position="top-right" />
      </body>
    </html>
  );
}
