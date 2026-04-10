"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuestionnaire } from "@/hooks/useQuestionnaire";
import { useRecommendationStream } from "@/hooks/useRecommendations";
import ProgressBar from "@/components/questionnaire/ProgressBar";
import StepBasic from "@/components/questionnaire/StepBasic";
import StepResearch from "@/components/questionnaire/StepResearch";
import StepPapers from "@/components/questionnaire/StepPapers";
import StepCompetitions from "@/components/questionnaire/StepCompetitions";
import StepInternships from "@/components/questionnaire/StepInternships";
import StepPreferences from "@/components/questionnaire/StepPreferences";

export default function QuestionnairePage() {
  const router = useRouter();
  const {
    state, loading, totalSteps, goPrev,
    submitBasicProfile, submitResearch, submitPapers,
    submitCompetitions, submitInternships, submitPreferences,
  } = useQuestionnaire();

  const stream = useRecommendationStream();
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async () => {
    if (!state.session_id) return;
    setGenerating(true);
    const sessionId = await stream.generate(state.session_id);
    if (sessionId) {
      router.push(`/results/${sessionId}`);
    }
  };

  // ─── Generating view with real-time progress ──────────────────────────────
  if (generating) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="card p-8">
          <h2 className="text-xl font-bold text-gray-900 mb-6 text-center">
            {stream.done ? "分析完成！" : "正在智能分析中..."}
          </h2>

          {/* Progress bar */}
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-500 mb-1">
              <span>{stream.message}</span>
              <span>{stream.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${stream.progress}%` }}
              />
            </div>
          </div>

          {/* Currently analyzing */}
          {stream.currentSchool && !stream.done && (
            <div className="bg-blue-50 rounded-lg p-3 mb-4 flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              <span className="text-sm text-blue-700">
                正在分析：<strong>{stream.currentSchool}</strong>
                {stream.currentTier && (
                  <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${
                    stream.currentTier === "冲刺" ? "bg-red-100 text-red-700" :
                    stream.currentTier === "主申" ? "bg-blue-100 text-blue-700" :
                    "bg-green-100 text-green-700"
                  }`}>{stream.currentTier}</span>
                )}
              </span>
            </div>
          )}

          {/* Analyzed schools log */}
          {stream.analyzedSchools.length > 0 && (
            <div className="max-h-48 overflow-y-auto border border-gray-100 rounded-lg">
              <div className="p-3 space-y-1.5">
                {stream.analyzedSchools.map((s, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-gray-600">
                    <span className="text-green-500">✓</span>
                    <span>{s.school} · {s.dept}</span>
                    <span className={`px-1.5 py-0.5 rounded text-xs ${
                      s.tier === "冲刺" ? "bg-red-50 text-red-600" :
                      s.tier === "主申" ? "bg-blue-50 text-blue-600" :
                      "bg-green-50 text-green-600"
                    }`}>{s.tier}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error */}
          {stream.error && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              {stream.error}
              <button onClick={() => setGenerating(false)} className="ml-3 underline">返回重试</button>
            </div>
          )}

          {/* Done */}
          {stream.done && (
            <div className="mt-4 text-center">
              <p className="text-green-600 font-medium mb-3">分析完成，正在跳转到结果页...</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // ─── Normal questionnaire flow ────────────────────────────────────────────
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <ProgressBar step={state.step} total={totalSteps} />

      {state.step === 1 && (
        <StepBasic onSubmit={submitBasicProfile} loading={loading} />
      )}
      {state.step === 2 && (
        <StepResearch onSubmit={submitResearch} onBack={goPrev} loading={loading} />
      )}
      {state.step === 3 && (
        <StepPapers onSubmit={submitPapers} onBack={goPrev} loading={loading} />
      )}
      {state.step === 4 && (
        <StepCompetitions onSubmit={submitCompetitions} onBack={goPrev} loading={loading} />
      )}
      {state.step === 5 && (
        <StepInternships onSubmit={submitInternships} onBack={goPrev} loading={loading} />
      )}
      {state.step === 6 && (
        <StepPreferences onSubmit={submitPreferences} onBack={goPrev} loading={loading} />
      )}
      {state.step === 7 && (
        <div className="card p-8 text-center">
          <div className="text-5xl mb-4">🎯</div>
          <h2 className="text-2xl font-bold mb-2">信息填写完成！</h2>
          <p className="text-gray-600 mb-6">
            点击下方按钮，系统将实时分析每个匹配院校并生成个性化推荐。
            <br />全程可看到分析进度，预计 1-2 分钟。
          </p>
          <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-600 mb-6 text-left">
            <p className="font-medium mb-2">已填写信息：</p>
            <ul className="space-y-1">
              <li>• 基础信息：{state.profile?.undergraduate_school}（{state.profile?.school_tier}）</li>
              <li>• 专业排名：{state.profile?.major_rank}/{state.profile?.major_rank_total}</li>
              <li>• 科研经历：{state.research_experiences.length} 段</li>
              <li>• 论文成果：{state.papers.length} 篇</li>
              <li>• 竞赛经历：{state.competitions.length} 项</li>
              <li>• 实习经历：{state.internships.length} 段</li>
              <li>• 职业目标：{state.preferences?.career_goal}，{state.preferences?.risk_appetite}型</li>
            </ul>
          </div>
          <div className="flex gap-3 justify-center">
            <button onClick={goPrev} className="btn-secondary">← 返回修改</button>
            <button
              onClick={handleGenerate}
              className="btn-primary text-lg px-8"
              disabled={loading}
            >
              🚀 开始智能分析
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
