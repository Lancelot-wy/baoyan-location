"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import type { InternshipCreate } from "@/lib/types";

interface Props {
  onSubmit: (data: InternshipCreate[]) => void;
  onBack: () => void;
  loading: boolean;
}

export default function StepInternships({ onSubmit, onBack, loading }: Props) {
  const [internships, setInternships] = useState<InternshipCreate[]>([]);
  const [adding, setAdding] = useState(false);
  const { register, handleSubmit, watch, reset } = useForm<InternshipCreate>({
    defaultValues: { is_ongoing: false, relevance: "部分相关", is_research_type: false },
  });
  const isOngoing = watch("is_ongoing");

  const addInternship = (data: InternshipCreate) => {
    setInternships((prev) => [...prev, data]);
    reset({ is_ongoing: false, relevance: "部分相关", is_research_type: false });
    setAdding(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">第五步：实习经历</h2>
        <p className="text-sm text-gray-500 mt-1">
          包括公司实习和科研实习（如在高校实验室的实习）。对就业导向的申请者权重更高。
        </p>
      </div>

      {internships.map((intern, i) => (
        <div key={i} className="card p-4 border-l-4 border-l-green-500">
          <div className="flex justify-between">
            <div>
              <span className="font-medium">{intern.company}</span>
              <span className="ml-2 text-sm text-gray-600">{intern.position}</span>
              {intern.is_research_type && <span className="ml-2 text-xs bg-blue-100 text-blue-700 px-1.5 rounded">科研实习</span>}
              <div className="text-xs text-gray-400 mt-1">
                {intern.start_date} ~ {intern.is_ongoing ? "至今" : intern.end_date || ""}
              </div>
            </div>
            <button onClick={() => setInternships((p) => p.filter((_, idx) => idx !== i))}
              className="text-red-400 hover:text-red-600 text-sm">删除</button>
          </div>
        </div>
      ))}

      {adding ? (
        <form onSubmit={handleSubmit(addInternship)} className="card p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">公司/单位名称 *</label>
              <input {...register("company", { required: true })} className="input-field" placeholder="如：字节跳动、微软亚洲研究院" />
            </div>
            <div>
              <label className="label">岗位名称 *</label>
              <input {...register("position", { required: true })} className="input-field" placeholder="如：算法实习生、研究实习生" />
            </div>
            <div>
              <label className="label">部门（选填）</label>
              <input {...register("department")} className="input-field" placeholder="如：NLP组" />
            </div>
            <div>
              <label className="label">开始时间 *</label>
              <input type="date" {...register("start_date", { required: true })} className="input-field" />
            </div>
            <div className="flex items-center gap-2 mt-6">
              <input type="checkbox" {...register("is_ongoing")} id="isongoing" />
              <label htmlFor="isongoing" className="text-sm">目前仍在实习中</label>
            </div>
            {!isOngoing && (
              <div>
                <label className="label">结束时间</label>
                <input type="date" {...register("end_date")} className="input-field" />
              </div>
            )}
            <div>
              <label className="label">与申请方向相关性</label>
              <select {...register("relevance")} className="input-field">
                <option value="高度相关">高度相关（直接相关的技术/研究方向）</option>
                <option value="部分相关">部分相关（有技术交叉）</option>
                <option value="不相关">不相关（如纯财务、行政等）</option>
              </select>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" {...register("is_research_type")} id="isresearch" />
            <label htmlFor="isresearch" className="text-sm">
              科研性质实习（如高校实验室、企业研究院）
            </label>
          </div>
          <div>
            <label className="label">备注（选填）</label>
            <textarea {...register("notes")} className="input-field" rows={2}
              placeholder="如：参与了xxx项目，负责xxx模块" />
          </div>
          <div className="flex gap-3">
            <button type="submit" className="btn-primary">添加这段实习</button>
            <button type="button" onClick={() => setAdding(false)} className="btn-secondary">取消</button>
          </div>
        </form>
      ) : (
        <button onClick={() => setAdding(true)}
          className="w-full border-2 border-dashed border-gray-300 rounded-lg py-4 text-gray-500 hover:border-green-400 hover:text-green-600 transition-colors">
          + 添加一段实习经历
        </button>
      )}

      <div className="flex justify-between">
        <button onClick={onBack} className="btn-secondary">← 上一步</button>
        <button onClick={() => onSubmit(internships)} className="btn-primary" disabled={loading}>
          {loading ? "保存中..." : `下一步：申请偏好 → ${internships.length > 0 ? `（已填${internships.length}段）` : "（跳过）"}`}
        </button>
      </div>
    </div>
  );
}
