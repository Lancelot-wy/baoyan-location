"use client";
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-16">
      {/* Hero */}
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          保研推免智能定位器
        </h1>
        <p className="text-xl text-gray-600 mb-2">
          基于真实案例库、结构化证据和AI分析的CS保研推荐系统
        </p>
        <p className="text-sm text-gray-500 mb-8">
          不是简单分数加总，而是带证据、带置信度、面向真实申请场景的推荐决策支持
        </p>
        <Link
          href="/questionnaire"
          className="btn-primary text-lg px-10 py-3 inline-block rounded-xl"
        >
          开始填写信息 →
        </Link>
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {[
          {
            icon: "📊",
            title: "多维画像",
            desc: "采集成绩、科研、论文、竞赛、实习、职业偏好等完整信息，动态追问，不遗漏关键信息",
          },
          {
            icon: "🔍",
            title: "证据驱动",
            desc: "每个推荐项都附带证据来源、年份、可信度。官方通知 > 经验帖 > 群消息，权重透明",
          },
          {
            icon: "⚖️",
            title: "冲刺/主申/保底",
            desc: "基于相似历史案例和学院画像，给出分层推荐，区分「能申上」和「去了合适」",
          },
        ].map((f) => (
          <div key={f.title} className="card p-6">
            <div className="text-3xl mb-3">{f.icon}</div>
            <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
            <p className="text-gray-600 text-sm leading-relaxed">{f.desc}</p>
          </div>
        ))}
      </div>

      {/* Disclaimer */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-800">
        <strong>⚠️ 说明：</strong>
        本系统输出的是「带证据和置信度的推荐建议」，不是「确定录取预测」。
        推免竞争情况每年变化，请以各院校最新官方通知为准。
        系统中的案例数据来自公开信息，已脱敏处理。
      </div>
    </div>
  );
}
