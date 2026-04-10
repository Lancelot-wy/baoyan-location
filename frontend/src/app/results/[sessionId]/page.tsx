"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import type { FullRecommendationResponse, RecommendationResultOut, RecommendationTier } from "@/lib/types";
import { getRecommendations, pollRecommendations } from "@/lib/api";
import RecommendationCard from "@/components/results/RecommendationCard";
import ProfileSummaryCard from "@/components/results/ProfileSummary";

type GroupedResults = Record<RecommendationTier, RecommendationResultOut[]>;

export default function ResultsPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;

  const [status, setStatus] = useState<"loading" | "processing" | "done" | "failed">("loading");
  const [data, setData] = useState<FullRecommendationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<RecommendationTier | "all">("all");

  useEffect(() => {
    if (!sessionId) return;

    setStatus("loading");
    // Data should already be ready (generate is now synchronous)
    // Just fetch it directly
    getRecommendations(sessionId)
      .then((result) => {
        if (result.status === "done") {
          setData(result);
          setStatus("done");
        } else if (result.status === "failed") {
          setError(result.error || "推荐生成失败");
          setStatus("failed");
        } else {
          // Still processing — poll
          pollRecommendations(
            sessionId,
            (r) => { setData(r); setStatus("done"); },
            (e) => { setError(e); setStatus("failed"); },
            3000, 120
          );
        }
      })
      .catch((err) => {
        setError(err?.message || "获取推荐结果失败");
        setStatus("failed");
      });
  }, [sessionId]);

  if (status === "loading" || status === "processing") {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <div className="text-5xl mb-4 animate-spin">⚙️</div>
        <h2 className="text-2xl font-bold mb-2">正在生成推荐...</h2>
        <p className="text-gray-500 mb-4">
          系统正在检索历史案例、匹配院校画像、调用AI生成解释
        </p>
        <div className="w-full max-w-xs mx-auto bg-gray-200 rounded-full h-2 overflow-hidden">
          <div className="bg-blue-600 h-2 rounded-full animate-pulse w-2/3" />
        </div>
        <p className="text-xs text-gray-400 mt-4">通常需要 30-60 秒，请耐心等待</p>
      </div>
    );
  }

  if (status === "failed" || error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <div className="text-5xl mb-4">❌</div>
        <h2 className="text-2xl font-bold mb-2">生成失败</h2>
        <p className="text-gray-500 mb-6">{error || "未知错误，请重试"}</p>
        <a href="/questionnaire" className="btn-primary">重新填写</a>
      </div>
    );
  }

  if (!data || data.results.length === 0) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <div className="text-5xl mb-4">🤷</div>
        <h2 className="text-2xl font-bold mb-2">暂无推荐结果</h2>
        <p className="text-gray-500 mb-4">
          知识库中可能缺乏足够的院校数据。请联系管理员导入数据，或先运行种子脚本。
        </p>
        <a href="/" className="btn-secondary">返回首页</a>
      </div>
    );
  }

  // Group by tier
  const grouped: GroupedResults = { "冲刺": [], "主申": [], "保底": [] };
  data.results.forEach((r) => {
    grouped[r.tier]?.push(r);
  });

  const tierCounts = {
    all: data.results.length,
    "冲刺": grouped["冲刺"].length,
    "主申": grouped["主申"].length,
    "保底": grouped["保底"].length,
  };

  const displayResults = activeTab === "all" ? data.results : grouped[activeTab] || [];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">推荐结果</h1>
        <div className="flex gap-2">
          <a href="/questionnaire" className="btn-secondary text-sm py-1.5 px-4">重新填写</a>
          <button
            onClick={() => window.print()}
            className="btn-secondary text-sm py-1.5 px-4"
          >
            打印/保存
          </button>
        </div>
      </div>

      {/* Profile summary */}
      {data.profile_summary && (
        <ProfileSummaryCard summary={data.profile_summary} />
      )}

      {/* Tier tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        {(["all", "冲刺", "主申", "保底"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2 px-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {tab === "all" ? "全部" : tab}
            <span className="ml-1.5 text-xs bg-gray-100 px-1.5 py-0.5 rounded-full">
              {tierCounts[tab]}
            </span>
          </button>
        ))}
      </div>

      {/* Warning */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-700 mb-6">
        ⚠️ 以下推荐基于公开信息和历史案例，不代表确定录取结果。请以目标院校最新官方招生通知为准。
        录取概率区间仅供参考，实际情况受当年招生计划、竞争情况等多因素影响。
      </div>

      {/* Results list */}
      <div className="space-y-4">
        {displayResults.map((result, i) => (
          <RecommendationCard key={result.id} result={result} rank={result.rank} />
        ))}
      </div>

      {/* Strategy summary at bottom */}
      <div className="mt-8 card p-5">
        <h3 className="font-medium text-gray-900 mb-2">🎯 申请策略总结</h3>
        <div className="grid grid-cols-3 gap-4 text-center text-sm">
          <div className="bg-red-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-red-600">{tierCounts["冲刺"]}</div>
            <div className="text-red-700">冲刺院校</div>
            <div className="text-xs text-gray-500 mt-1">低概率、高价值</div>
          </div>
          <div className="bg-blue-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-blue-600">{tierCounts["主申"]}</div>
            <div className="text-blue-700">主申院校</div>
            <div className="text-xs text-gray-500 mt-1">核心投递目标</div>
          </div>
          <div className="bg-green-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-green-600">{tierCounts["保底"]}</div>
            <div className="text-green-700">保底院校</div>
            <div className="text-xs text-gray-500 mt-1">确保有书读</div>
          </div>
        </div>
      </div>
    </div>
  );
}
