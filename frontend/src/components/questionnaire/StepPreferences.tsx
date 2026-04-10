"use client";
import { useForm } from "react-hook-form";
import type { PreferenceProfileCreate, CareerGoal, RiskAppetite } from "@/lib/types";
import { CITIES, CS_DIRECTIONS } from "@/lib/utils";

interface Props {
  onSubmit: (data: PreferenceProfileCreate) => void;
  onBack: () => void;
  loading: boolean;
  careerGoalHint?: string;  // from profile builder for adaptive questions
}

export default function StepPreferences({ onSubmit, onBack, loading, careerGoalHint }: Props) {
  const { register, handleSubmit, watch } = useForm<PreferenceProfileCreate>({
    defaultValues: {
      career_goal: "就业",
      risk_appetite: "稳健",
      accept_high_pressure_advisor: false,
      prioritize_city: false,
      prioritize_school_brand: false,
      prioritize_internship_resources: false,
      prioritize_phd_track: false,
      accept_cross_direction: false,
      preferred_cities: [],
      excluded_cities: [],
      care_about_living_cost: false,
      care_about_internet_industry: false,
      accept_remote_study: false,
      target_directions: [],
    },
  });

  const careerGoal = watch("career_goal");
  const cities = CITIES();
  const directions = CS_DIRECTIONS();

  const onFormSubmit = (data: PreferenceProfileCreate) => {
    // Convert checkbox group values
    const formData = new FormData();
    // preferred_cities and target_directions come as checkbox arrays
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">第六步：申请偏好与职业规划</h2>
        <p className="text-sm text-gray-500 mt-1">
          这些信息帮助系统为你调整推荐权重，匹配更适合你目标的项目。
        </p>
      </div>

      {/* Career goal */}
      <div className="card p-5">
        <h3 className="font-medium mb-3">职业目标 <span className="text-red-500">*</span></h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {[
            { value: "就业", label: "毕业后就业", emoji: "💼" },
            { value: "读博", label: "硕博连读/直博", emoji: "🔬" },
            { value: "考公", label: "考公务员", emoji: "🏛️" },
            { value: "选调", label: "选调生", emoji: "🌐" },
            { value: "出国", label: "出国深造", emoji: "✈️" },
            { value: "未定", label: "还没确定", emoji: "🤔" },
          ].map((opt) => (
            <label key={opt.value} className="flex items-center gap-2 cursor-pointer">
              <input type="radio" {...register("career_goal")} value={opt.value} className="w-4 h-4" />
              <span className="text-sm">{opt.emoji} {opt.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Risk appetite */}
      <div className="card p-5">
        <h3 className="font-medium mb-1">申请风格 <span className="text-red-500">*</span></h3>
        <p className="text-xs text-gray-400 mb-3">影响冲刺/主申/保底比例的推荐权重</p>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: "冲刺", label: "冲刺型", desc: "敢于冲高，接受低录取概率" },
            { value: "稳健", label: "稳健型", desc: "冲高但保底兼顾" },
            { value: "保守", label: "保守型", desc: "优先确保拿到offer" },
          ].map((opt) => (
            <label key={opt.value}
              className="border rounded-lg p-3 cursor-pointer hover:border-blue-400 transition-colors">
              <input type="radio" {...register("risk_appetite")} value={opt.value} className="mr-2" />
              <span className="font-medium text-sm">{opt.label}</span>
              <p className="text-xs text-gray-500 mt-1">{opt.desc}</p>
            </label>
          ))}
        </div>
      </div>

      {/* City preferences */}
      <div className="card p-5">
        <h3 className="font-medium mb-3">城市偏好</h3>
        <div className="mb-3">
          <label className="label">意向城市（可多选）</label>
          <div className="flex flex-wrap gap-2">
            {cities.map((city) => (
              <label key={city} className="flex items-center gap-1 cursor-pointer">
                <input type="checkbox" {...register("preferred_cities")} value={city} className="w-3.5 h-3.5" />
                <span className="text-sm">{city}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <label className="label">不接受的城市（可多选）</label>
          <div className="flex flex-wrap gap-2">
            {cities.map((city) => (
              <label key={city} className="flex items-center gap-1 cursor-pointer">
                <input type="checkbox" {...register("excluded_cities")} value={city} className="w-3.5 h-3.5" />
                <span className="text-sm">{city}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Target research directions */}
      <div className="card p-5">
        <h3 className="font-medium mb-3">意向研究方向（可多选）</h3>
        <div className="flex flex-wrap gap-2">
          {directions.map((dir) => (
            <label key={dir} className="flex items-center gap-1 cursor-pointer">
              <input type="checkbox" {...register("target_directions")} value={dir} className="w-3.5 h-3.5" />
              <span className="text-sm">{dir}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Other preferences */}
      <div className="card p-5">
        <h3 className="font-medium mb-3">其他偏好</h3>
        <div className="space-y-3">
          {[
            { name: "prioritize_school_brand" as const, label: "优先考虑学校牌子（985/顶校品牌溢价）" },
            { name: "prioritize_city" as const, label: "城市是重要决策因素" },
            { name: "prioritize_internship_resources" as const, label: "优先互联网/产业实习资源丰富的城市" },
            { name: "prioritize_phd_track" as const, label: "希望有硕博连读/转博机会" },
            { name: "accept_high_pressure_advisor" as const, label: "可以接受高压/强管理风格的导师" },
            { name: "accept_cross_direction" as const, label: "接受跨研究方向申请" },
            { name: "care_about_living_cost" as const, label: "生活成本是重要考量" },
            { name: "care_about_internet_industry" as const, label: "互联网大厂就业是核心目标" },
            { name: "accept_remote_study" as const, label: "接受异地/偏远城市读研" },
          ].map((pref) => (
            <div key={pref.name} className="flex items-center gap-2">
              <input type="checkbox" {...register(pref.name)} id={pref.name} className="w-4 h-4" />
              <label htmlFor={pref.name} className="text-sm text-gray-700">{pref.label}</label>
            </div>
          ))}
        </div>
      </div>

      <div>
        <label className="label">补充说明（选填）</label>
        <textarea {...register("notes")} className="input-field" rows={3}
          placeholder="任何其他想让系统知道的偏好、特殊情况、或对推荐的期望..." />
      </div>

      <div className="flex justify-between">
        <button type="button" onClick={onBack} className="btn-secondary">← 上一步</button>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "保存中..." : "下一步：生成推荐 →"}
        </button>
      </div>
    </form>
  );
}
