"use client";
import type { ProfileSummary } from "@/lib/types";

interface Props {
  summary: ProfileSummary;
}

export default function ProfileSummaryCard({ summary }: Props) {
  return (
    <div className="card p-6 mb-6">
      <h2 className="text-lg font-bold text-gray-900 mb-4">📊 个人画像分析</h2>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <p className="text-blue-800 font-medium">{summary.overall_assessment}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <h3 className="font-medium text-green-700 mb-2">✅ 核心优势</h3>
          <ul className="space-y-1">
            {summary.core_strengths.map((s, i) => (
              <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-green-500 mt-0.5">•</span>{s}
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="font-medium text-red-700 mb-2">⚠️ 核心短板</h3>
          <ul className="space-y-1">
            {summary.core_weaknesses.map((w, i) => (
              <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                <span className="text-red-400 mt-0.5">•</span>{w}
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="bg-gray-50 rounded-lg p-4 mb-3">
        <h3 className="font-medium text-gray-700 mb-2">🗺️ 整体策略建议</h3>
        <p className="text-sm text-gray-600">{summary.strategic_advice}</p>
      </div>

      <div className="bg-amber-50 rounded-lg p-4">
        <h3 className="font-medium text-amber-700 mb-2">⏰ 时间安排建议</h3>
        <p className="text-sm text-amber-800">{summary.timeline_advice}</p>
      </div>

      {summary.directions_to_avoid.length > 0 && (
        <div className="mt-3 text-sm text-gray-500">
          <span className="font-medium">不建议重点投入：</span>
          {summary.directions_to_avoid.join("、")}
        </div>
      )}
    </div>
  );
}
