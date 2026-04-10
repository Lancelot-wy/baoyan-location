"use client";
import { useState } from "react";
import type { RecommendationResultOut } from "@/lib/types";
import { tierColor, tierEmoji, scoreColor } from "@/lib/utils";
import EvidencePanel from "./EvidencePanel";

interface Props {
  result: RecommendationResultOut;
  rank: number;
}

export default function RecommendationCard({ result, rank }: Props) {
  const [expanded, setExpanded] = useState(false);
  const probLow = Math.round(result.admission_probability_low * 100);
  const probHigh = Math.round(result.admission_probability_high * 100);

  return (
    <div className="card overflow-hidden">
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <span className={`text-xs font-medium px-2.5 py-1 rounded-full border ${tierColor(result.tier)}`}>
                {tierEmoji(result.tier)} {result.tier}
              </span>
              <span className="text-xs text-gray-400">#{rank}</span>
              {result.is_suitable_for_reach && (
                <span className="text-xs bg-orange-50 text-orange-600 border border-orange-200 px-2 py-0.5 rounded-full">
                  适合冲
                </span>
              )}
              {result.is_suitable_for_safe && (
                <span className="text-xs bg-green-50 text-green-600 border border-green-200 px-2 py-0.5 rounded-full">
                  可保底
                </span>
              )}
            </div>
            <h3 className="text-lg font-bold text-gray-900">
              {result.school}
            </h3>
            <p className="text-sm text-gray-600">
              {result.department}
              {result.direction && ` · ${result.direction}`}
              {result.program_type && (
                <span className="ml-2 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                  {result.program_type}
                </span>
              )}
            </p>
            {result.advisor_name && (
              <p className="text-xs text-blue-600 mt-1">👨‍🏫 {result.advisor_name}</p>
            )}
          </div>

          <div className="text-right shrink-0">
            <div className={`text-2xl font-bold ${scoreColor(result.compatibility_score)}`}>
              {result.compatibility_score.toFixed(0)}
              <span className="text-sm font-normal text-gray-400">/100</span>
            </div>
            <div className="text-xs text-gray-500 mt-1">
              录取概率 {probLow}%-{probHigh}%
            </div>
            {result.career_fit_score && (
              <div className="text-xs text-gray-400">就业匹配 {result.career_fit_score.toFixed(0)}/100</div>
            )}
          </div>
        </div>

        {/* Evidence summary (always visible) */}
        <div className="mt-3 text-sm text-gray-700 bg-blue-50 rounded-lg p-3">
          <span className="font-medium text-blue-700">推荐理由：</span>
          {result.evidence_summary}
        </div>

        {/* Strengths/weaknesses quick view */}
        {result.reasons.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {result.reasons.filter(r => r.reason_type === "strength").slice(0, 3).map((r, i) => (
              <span key={i} className="text-xs bg-green-50 text-green-700 border border-green-200 px-2 py-0.5 rounded-full">
                ✓ {r.reason_text}
              </span>
            ))}
            {result.reasons.filter(r => r.reason_type === "weakness").slice(0, 2).map((r, i) => (
              <span key={i} className="text-xs bg-red-50 text-red-700 border border-red-200 px-2 py-0.5 rounded-full">
                ⚠ {r.reason_text}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Expandable section */}
      <div className="border-t border-gray-100">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full px-5 py-2.5 text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-50 flex items-center justify-center gap-1 transition-colors"
        >
          {expanded ? "收起详情 ↑" : "查看详情（风险、备考建议、就业/读博分析）↓"}
        </button>
      </div>

      {expanded && (
        <EvidencePanel result={result} />
      )}
    </div>
  );
}
