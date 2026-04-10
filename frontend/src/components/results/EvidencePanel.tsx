"use client";
import type { RecommendationResultOut } from "@/lib/types";

interface Props {
  result: RecommendationResultOut;
}

export default function EvidencePanel({ result }: Props) {
  return (
    <div className="px-5 pb-5 space-y-4">
      {/* Risk */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <h4 className="font-medium text-amber-800 mb-1.5">⚠️ 主要风险</h4>
        <p className="text-sm text-amber-700">{result.risk_summary}</p>
      </div>

      {/* Preparation */}
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
        <h4 className="font-medium text-blue-800 mb-1.5">📋 准备建议</h4>
        <div className="text-sm text-blue-700 whitespace-pre-line">{result.preparation_advice}</div>
      </div>

      {/* Employment vs PhD */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {(result.employment_pros || result.employment_cons) && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-700 mb-2">💼 就业视角</h4>
            {result.employment_pros && (
              <div className="text-sm">
                <span className="text-green-600 font-medium">优势：</span>
                <span className="text-gray-600">{result.employment_pros}</span>
              </div>
            )}
            {result.employment_cons && (
              <div className="text-sm mt-1">
                <span className="text-red-600 font-medium">劣势：</span>
                <span className="text-gray-600">{result.employment_cons}</span>
              </div>
            )}
          </div>
        )}
        {(result.phd_pros || result.phd_cons) && (
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-medium text-gray-700 mb-2">🔬 读博视角</h4>
            {result.phd_pros && (
              <div className="text-sm">
                <span className="text-green-600 font-medium">优势：</span>
                <span className="text-gray-600">{result.phd_pros}</span>
              </div>
            )}
            {result.phd_cons && (
              <div className="text-sm mt-1">
                <span className="text-red-600 font-medium">劣势：</span>
                <span className="text-gray-600">{result.phd_cons}</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* All reasons */}
      {result.reasons.length > 0 && (
        <div>
          <h4 className="font-medium text-gray-700 mb-2">分析维度</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {[
              { type: "strength" as const, label: "✓ 优势", cls: "bg-green-50 text-green-700 border-green-200" },
              { type: "weakness" as const, label: "△ 短板", cls: "bg-red-50 text-red-700 border-red-200" },
              { type: "opportunity" as const, label: "★ 机会", cls: "bg-blue-50 text-blue-700 border-blue-200" },
              { type: "risk" as const, label: "⚠ 风险", cls: "bg-amber-50 text-amber-700 border-amber-200" },
            ].map(({ type, label, cls }) => {
              const items = result.reasons.filter(r => r.reason_type === type);
              if (!items.length) return null;
              return (
                <div key={type} className={`border rounded-lg p-3 ${cls}`}>
                  <div className="font-medium text-xs mb-1.5">{label}</div>
                  <ul className="space-y-1">
                    {items.map((r, i) => (
                      <li key={i} className="text-xs">• {r.reason_text}</li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
