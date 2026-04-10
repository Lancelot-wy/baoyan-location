"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import type { CompetitionCreate } from "@/lib/types";

interface Props {
  onSubmit: (data: CompetitionCreate[]) => void;
  onBack: () => void;
  loading: boolean;
}

export default function StepCompetitions({ onSubmit, onBack, loading }: Props) {
  const [comps, setComps] = useState<CompetitionCreate[]>([]);
  const [adding, setAdding] = useState(false);
  const { register, handleSubmit, watch, reset } = useForm<CompetitionCreate>({
    defaultValues: { year: new Date().getFullYear(), is_team: true, relevance_to_application: "部分相关" },
  });
  const isTeam = watch("is_team");

  const addComp = (data: CompetitionCreate) => {
    setComps((prev) => [...prev, { ...data, year: Number(data.year) }]);
    reset({ year: new Date().getFullYear(), is_team: true, relevance_to_application: "部分相关" });
    setAdding(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">第四步：竞赛经历</h2>
        <p className="text-sm text-gray-500 mt-1">
          ACM、数学建模、信息安全、机器学习等竞赛均可填写。校级奖项也可填，但权重较低。
        </p>
      </div>

      {comps.map((comp, i) => (
        <div key={i} className="card p-4 border-l-4 border-l-yellow-500">
          <div className="flex justify-between">
            <div>
              <span className="font-medium">{comp.name}</span>
              <span className="ml-2 text-sm text-gray-600">{comp.level} · {comp.award}</span>
              <span className="ml-2 text-xs text-gray-400">{comp.year}年</span>
            </div>
            <button onClick={() => setComps((p) => p.filter((_, idx) => idx !== i))}
              className="text-red-400 hover:text-red-600 text-sm">删除</button>
          </div>
        </div>
      ))}

      {adding ? (
        <form onSubmit={handleSubmit(addComp)} className="card p-6 space-y-4">
          <h3 className="font-medium">添加竞赛</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="label">竞赛名称 *</label>
              <input {...register("name", { required: true })} className="input-field"
                placeholder="如：第46届国际大学生程序设计竞赛（ICPC）亚洲区域赛" />
            </div>
            <div>
              <label className="label">竞赛类别 *</label>
              <select {...register("category", { required: true })} className="input-field">
                <option value="">请选择</option>
                <option value="ACM">ACM/ICPC/CCPC</option>
                <option value="数学建模">数学建模（全国/美赛/华赛）</option>
                <option value="信息安全">信息安全（CTF/全国信安竞赛）</option>
                <option value="机器学习">机器学习/数据科学（Kaggle等）</option>
                <option value="数据挖掘">数据挖掘竞赛</option>
                <option value="其他">其他（互联网+、挑战杯等）</option>
              </select>
            </div>
            <div>
              <label className="label">级别 *</label>
              <select {...register("level", { required: true })} className="input-field">
                <option value="">请选择</option>
                <option value="国际">国际（如ICPC世界总决赛、国际竞赛）</option>
                <option value="国家">国家（全国总决赛/全国赛）</option>
                <option value="省级">省级（省赛/区域赛）</option>
                <option value="校级">校级</option>
              </select>
            </div>
            <div>
              <label className="label">奖项等级 *</label>
              <select {...register("award", { required: true })} className="input-field">
                <option value="">请选择</option>
                <option value="金">金奖/一等奖</option>
                <option value="银">银奖</option>
                <option value="铜">铜奖</option>
                <option value="一等">一等奖</option>
                <option value="二等">二等奖</option>
                <option value="三等">三等奖/铜奖</option>
                <option value="优秀">优秀奖/入围</option>
                <option value="参与">参与（无奖）</option>
              </select>
            </div>
            <div>
              <label className="label">年份 *</label>
              <input type="number" {...register("year", { required: true, valueAsNumber: true })} className="input-field" />
            </div>
            <div>
              <label className="label">与申请方向相关性</label>
              <select {...register("relevance_to_application")} className="input-field">
                <option value="高度相关">高度相关（同一研究方向）</option>
                <option value="部分相关">部分相关（有技术交叉）</option>
                <option value="不相关">不相关（方向完全不同）</option>
              </select>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" {...register("is_team")} id="isteam" />
            <label htmlFor="isteam" className="text-sm">团队参赛</label>
          </div>
          {isTeam && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">团队人数</label>
                <input type="number" {...register("team_size", { valueAsNumber: true })} className="input-field" />
              </div>
              <div>
                <label className="label">你在团队中的角色</label>
                <input {...register("user_role")} className="input-field" placeholder="如：队长、算法负责人" />
              </div>
            </div>
          )}
          <div className="flex gap-3">
            <button type="submit" className="btn-primary">添加这项竞赛</button>
            <button type="button" onClick={() => setAdding(false)} className="btn-secondary">取消</button>
          </div>
        </form>
      ) : (
        <button onClick={() => setAdding(true)}
          className="w-full border-2 border-dashed border-gray-300 rounded-lg py-4 text-gray-500 hover:border-yellow-400 hover:text-yellow-600 transition-colors">
          + 添加一项竞赛经历
        </button>
      )}

      <div className="flex justify-between">
        <button onClick={onBack} className="btn-secondary">← 上一步</button>
        <button onClick={() => onSubmit(comps)} className="btn-primary" disabled={loading}>
          {loading ? "保存中..." : `下一步：实习经历 → ${comps.length > 0 ? `（已填${comps.length}项）` : "（跳过）"}`}
        </button>
      </div>
    </div>
  );
}
