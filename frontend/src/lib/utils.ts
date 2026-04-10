import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function tierColor(tier: string): string {
  switch (tier) {
    case "冲刺": return "text-red-600 bg-red-50 border-red-200";
    case "主申": return "text-blue-600 bg-blue-50 border-blue-200";
    case "保底": return "text-green-600 bg-green-50 border-green-200";
    default: return "text-gray-600 bg-gray-50 border-gray-200";
  }
}

export function tierEmoji(tier: string): string {
  switch (tier) {
    case "冲刺": return "🔥";
    case "主申": return "⭐";
    case "保底": return "🛡️";
    default: return "•";
  }
}

export function scoreColor(score: number): string {
  if (score >= 70) return "text-green-700";
  if (score >= 50) return "text-blue-700";
  if (score >= 30) return "text-yellow-700";
  return "text-red-700";
}

export function CITIES(): string[] {
  return [
    "北京", "上海", "深圳", "杭州", "广州", "南京", "武汉",
    "成都", "西安", "合肥", "哈尔滨", "长沙", "天津",
  ];
}

export function CS_DIRECTIONS(): string[] {
  return [
    "人工智能", "机器学习", "深度学习", "自然语言处理",
    "计算机视觉", "数据挖掘", "大数据", "分布式系统",
    "网络安全", "系统与体系结构", "软件工程", "数据库",
    "人机交互", "图形学", "计算理论",
  ];
}
