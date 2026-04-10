"use client";

const STEP_LABELS = [
  "基础信息", "科研经历", "论文成果", "竞赛经历", "实习经历", "申请偏好", "生成推荐"
];

export default function ProgressBar({ step, total }: { step: number; total: number }) {
  const pct = Math.round((step / total) * 100);

  return (
    <div className="mb-8">
      <div className="flex justify-between text-xs text-gray-500 mb-2">
        <span>步骤 {step} / {total}：{STEP_LABELS[step - 1]}</span>
        <span>{pct}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex justify-between mt-1">
        {STEP_LABELS.map((label, i) => (
          <div
            key={label}
            className={`text-xs ${i + 1 <= step ? "text-blue-600 font-medium" : "text-gray-400"}`}
            style={{ width: `${100 / total}%`, textAlign: "center" }}
          >
            {i < 1 || i > 5 ? label.slice(0, 2) : ""}
          </div>
        ))}
      </div>
    </div>
  );
}
