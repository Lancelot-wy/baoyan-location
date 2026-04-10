"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import type { ResearchExperienceCreate } from "@/lib/types";

interface Props {
  onSubmit: (data: ResearchExperienceCreate[]) => void;
  onBack: () => void;
  loading: boolean;
}

export default function StepResearch({ onSubmit, onBack, loading }: Props) {
  const [experiences, setExperiences] = useState<ResearchExperienceCreate[]>([]);
  const [adding, setAdding] = useState(false);
  const { register, handleSubmit, reset, formState: { errors } } = useForm<ResearchExperienceCreate>();

  const addExp = (data: any) => {
    // Fix boolean strings from <select>
    data.is_long_term = data.is_long_term === "true" || data.is_long_term === true;
    data.has_advisor_endorsement = data.has_advisor_endorsement === true || data.has_advisor_endorsement === "on";
    setExperiences((prev) => [...prev, data]);
    reset();
    setAdding(false);
  };

  const removeExp = (i: number) => setExperiences((prev) => prev.filter((_, idx) => idx !== i));

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">第二步：科研经历</h2>
        <p className="text-sm text-gray-500 mt-1">
          科研经历对保研申请至关重要。如果没有，可以直接跳过（点击下一步）。
        </p>
      </div>

      {/* Existing experiences */}
      {experiences.map((exp, i) => (
        <div key={i} className="card p-4 border-l-4 border-l-blue-500">
          <div className="flex justify-between items-start">
            <div>
              <div className="font-medium">{exp.research_direction}</div>
              <div className="text-sm text-gray-600">
                {exp.advisor_name}（{exp.advisor_institution}）· {exp.user_role}
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {exp.start_date} ~ {exp.end_date || "至今"}
                {exp.has_advisor_endorsement && <span className="ml-2 text-green-600">✓ 导师背书</span>}
              </div>
            </div>
            <button onClick={() => removeExp(i)} className="text-red-400 hover:text-red-600 text-sm">删除</button>
          </div>
        </div>
      ))}

      {/* Add form */}
      {adding ? (
        <form onSubmit={handleSubmit(addExp)} className="card p-6 space-y-4">
          <h3 className="font-medium">添加科研经历</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">开始时间 *</label>
              <input type="date" {...register("start_date", { required: true })} className="input-field" />
            </div>
            <div>
              <label className="label">结束时间（未结束留空）</label>
              <input type="date" {...register("end_date")} className="input-field" />
            </div>
            <div>
              <label className="label">指导老师姓名 *</label>
              <input {...register("advisor_name", { required: true })} className="input-field" placeholder="如：张三" />
            </div>
            <div>
              <label className="label">老师职称</label>
              <input {...register("advisor_title")} className="input-field" placeholder="如：副教授、研究员" />
            </div>
            <div>
              <label className="label">老师所在单位 *</label>
              <input {...register("advisor_institution", { required: true })} className="input-field" placeholder="如：清华大学计算机系" />
            </div>
            <div>
              <label className="label">研究方向 *</label>
              <input {...register("research_direction", { required: true })} className="input-field" placeholder="如：自然语言处理" />
            </div>
            <div>
              <label className="label">
                你在组里的角色 *
                <span className="text-xs text-gray-400 ml-1">（影响评估权重）</span>
              </label>
              <select {...register("user_role", { required: true })} className="input-field">
                <option value="">请选择</option>
                <option value="旁观">旁观/学习为主，基本不参与实际工作</option>
                <option value="辅助">辅助，帮忙跑实验/整理数据</option>
                <option value="独立模块">独立负责某个模块</option>
                <option value="主负责">主负责人，推动整个项目</option>
              </select>
            </div>
            <div>
              <label className="label">是否长期进组（超过6个月）</label>
              <select {...register("is_long_term")} className="input-field">
                <option value="false">否</option>
                <option value="true">是</option>
              </select>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" {...register("has_advisor_endorsement")} id="endorsement" />
            <label htmlFor="endorsement" className="text-sm">
              导师愿意为我背书/写推荐信
            </label>
          </div>
          <div>
            <label className="label">补充说明（选填）</label>
            <textarea {...register("notes")} className="input-field" rows={2}
              placeholder="如：参与了某某课题、参与了某某竞赛/比赛相关研究等" />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="btn-primary">添加这段经历</button>
            <button type="button" onClick={() => setAdding(false)} className="btn-secondary">取消</button>
          </div>
        </form>
      ) : (
        <button
          onClick={() => setAdding(true)}
          className="w-full border-2 border-dashed border-gray-300 rounded-lg py-4 text-gray-500 hover:border-blue-400 hover:text-blue-600 transition-colors"
        >
          + 添加一段科研经历
        </button>
      )}

      <div className="flex justify-between">
        <button onClick={onBack} className="btn-secondary">← 上一步</button>
        <button
          onClick={() => onSubmit(experiences)}
          className="btn-primary"
          disabled={loading}
        >
          {loading ? "保存中..." : `下一步：论文成果 → ${experiences.length > 0 ? `（已填${experiences.length}段）` : "（跳过）"}`}
        </button>
      </div>
    </div>
  );
}
