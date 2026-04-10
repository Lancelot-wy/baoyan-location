"use client";
import { useState, useEffect, useCallback } from "react";
import { useForm } from "react-hook-form";
import type { UserProfileCreate } from "@/lib/types";
import axios from "axios";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface SchoolInfo {
  name: string;
  tier: string;
  has_baoyan: boolean;
  warning?: string;
}

interface Props {
  onSubmit: (data: UserProfileCreate) => void;
  loading: boolean;
}

export default function StepBasic({ onSubmit, loading }: Props) {
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<UserProfileCreate>({
    defaultValues: {
      gpa_full: 4.0,
      has_guaranteed_admission: false,
      has_disciplinary_issues: false,
      english_reading_level: "基础",
      research_orientation: "均衡",
    },
  });

  const hasDisciplinary = watch("has_disciplinary_issues");
  const schoolName = watch("undergraduate_school");

  // ─── School autocomplete ─────────────────────────────────────────────────
  const [schoolSuggestions, setSchoolSuggestions] = useState<SchoolInfo[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [schoolWarning, setSchoolWarning] = useState<string | null>(null);
  const [schoolTierAuto, setSchoolTierAuto] = useState<string | null>(null);

  // Debounced school search
  useEffect(() => {
    if (!schoolName || schoolName.length < 1) {
      setSchoolSuggestions([]);
      setSchoolWarning(null);
      setSchoolTierAuto(null);
      return;
    }
    const timer = setTimeout(async () => {
      try {
        const res = await axios.get(`${API}/api/v1/students/schools/search`, {
          params: { q: schoolName, limit: 8 },
        });
        setSchoolSuggestions(res.data);
        setShowSuggestions(res.data.length > 0);
      } catch { /* ignore */ }
    }, 300);
    return () => clearTimeout(timer);
  }, [schoolName]);

  const selectSchool = useCallback((school: SchoolInfo) => {
    setValue("undergraduate_school", school.name);
    setValue("school_tier", school.tier as any);
    setSchoolTierAuto(school.tier);
    setShowSuggestions(false);
    if (!school.has_baoyan) {
      setSchoolWarning(`「${school.name}」可能不在教育部推免资格高校名单中，请确认是否具有保研资格。`);
    } else {
      setSchoolWarning(null);
    }
  }, [setValue]);

  // Check school on blur
  const checkSchool = useCallback(async () => {
    setShowSuggestions(false);
    if (!schoolName || schoolName.length < 2) return;
    try {
      const res = await axios.get(`${API}/api/v1/students/schools/check/${encodeURIComponent(schoolName)}`);
      const data = res.data;
      setValue("school_tier", data.tier as any);
      setSchoolTierAuto(data.tier);
      if (data.warning) {
        setSchoolWarning(data.warning);
      } else {
        setSchoolWarning(null);
      }
    } catch { /* ignore */ }
  }, [schoolName, setValue]);

  const onSubmitFixed = (data: any) => {
    data.has_guaranteed_admission = data.has_guaranteed_admission === "true" || data.has_guaranteed_admission === true;
    data.has_disciplinary_issues = data.has_disciplinary_issues === true || data.has_disciplinary_issues === "on";
    data.gpa = Number(data.gpa);
    data.gpa_full = Number(data.gpa_full);
    data.major_rank = Number(data.major_rank);
    data.major_rank_total = Number(data.major_rank_total);
    if (data.cet4_score) data.cet4_score = Number(data.cet4_score);
    if (data.cet6_score) data.cet6_score = Number(data.cet6_score);
    if (data.ielts_score) data.ielts_score = Number(data.ielts_score);
    if (data.toefl_score) data.toefl_score = Number(data.toefl_score);
    for (const key of ["cet4_score", "cet6_score", "ielts_score", "toefl_score", "comprehensive_rank", "comprehensive_rank_total"]) {
      if (data[key] === "" || data[key] === null || Number.isNaN(data[key])) delete data[key];
    }
    onSubmit(data);
  };

  const tierLabel: Record<string, string> = {
    "985": "985 院校",
    "211": "211 院校",
    "双非": "双非院校",
    "其他": "其他",
  };

  return (
    <form onSubmit={handleSubmit(onSubmitFixed)} className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900">第一步：基础背景信息</h2>

      {/* School info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="relative">
          <label className="label">
            本科学校 <span className="text-red-500">*</span>
            <span className="text-xs text-gray-400 ml-1">（输入后自动匹配层次）</span>
          </label>
          <input
            {...register("undergraduate_school", { required: "请填写本科学校" })}
            className="input-field"
            placeholder="输入学校名称，如：北京邮电大学"
            autoComplete="off"
            onBlur={() => { setTimeout(() => { setShowSuggestions(false); checkSchool(); }, 200); }}
            onFocus={() => { if (schoolSuggestions.length > 0) setShowSuggestions(true); }}
          />
          {errors.undergraduate_school && <p className="error-text">{errors.undergraduate_school.message}</p>}

          {/* Autocomplete dropdown */}
          {showSuggestions && schoolSuggestions.length > 0 && (
            <div className="absolute z-20 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-56 overflow-y-auto">
              {schoolSuggestions.map((s) => (
                <button
                  key={s.name}
                  type="button"
                  className="w-full px-3 py-2 text-left hover:bg-blue-50 flex justify-between items-center text-sm"
                  onMouseDown={(e) => { e.preventDefault(); selectSchool(s); }}
                >
                  <span>{s.name}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    s.tier === "985" ? "bg-red-100 text-red-700" :
                    s.tier === "211" ? "bg-blue-100 text-blue-700" :
                    "bg-gray-100 text-gray-600"
                  }`}>
                    {s.tier}
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* School warning */}
          {schoolWarning && (
            <div className="mt-2 bg-amber-50 border border-amber-200 rounded-lg p-2.5 text-sm text-amber-800">
              ⚠️ {schoolWarning}
            </div>
          )}
        </div>

        <div>
          <label className="label">
            学校层次
            {schoolTierAuto && (
              <span className={`ml-2 text-xs px-2 py-0.5 rounded-full ${
                schoolTierAuto === "985" ? "bg-red-100 text-red-700" :
                schoolTierAuto === "211" ? "bg-blue-100 text-blue-700" :
                "bg-gray-100 text-gray-600"
              }`}>
                已自动识别：{tierLabel[schoolTierAuto] || schoolTierAuto}
              </span>
            )}
          </label>
          <select {...register("school_tier", { required: true })} className="input-field">
            <option value="">请选择</option>
            <option value="985">985院校</option>
            <option value="211">211院校（非985）</option>
            <option value="双非">双非院校</option>
            <option value="其他">其他</option>
          </select>
          <p className="text-xs text-gray-400 mt-1">输入学校名后会自动填充，也可手动修改</p>
        </div>

        <div>
          <label className="label">专业名称 <span className="text-red-500">*</span></label>
          <input
            {...register("major_name", { required: "请填写专业名称" })}
            className="input-field"
            placeholder="如：计算机科学与技术"
          />
          {errors.major_name && <p className="error-text">{errors.major_name.message}</p>}
        </div>
        <div>
          <label className="label">专业类别 <span className="text-red-500">*</span></label>
          <select {...register("major_category", { required: true })} className="input-field">
            <option value="">请选择</option>
            <option value="计算机科学与技术">计算机科学与技术</option>
            <option value="软件工程">软件工程</option>
            <option value="人工智能">人工智能</option>
            <option value="数据科学">数据科学与大数据</option>
            <option value="电子信息">电子信息</option>
            <option value="数学">数学/统计</option>
            <option value="物理">物理</option>
            <option value="其他">其他理工科</option>
          </select>
        </div>
        <div>
          <label className="label">当前年级 <span className="text-red-500">*</span></label>
          <select {...register("current_year", { required: true })} className="input-field">
            <option value="">请选择</option>
            <option value="大三">大三（正在申请）</option>
            <option value="大四">大四（本年度申请）</option>
            <option value="已毕业">已毕业</option>
          </select>
        </div>
        <div>
          <label className="label">是否已确定保研名额</label>
          <select {...register("has_guaranteed_admission")} className="input-field">
            <option value="false">否/未确定</option>
            <option value="true">是，已有名额</option>
          </select>
          <p className="text-xs text-gray-400 mt-1">指本校保研名额已确定，但尚未确定去向</p>
        </div>
      </div>

      {/* Academic performance */}
      <div className="border-t pt-4">
        <h3 className="font-medium text-gray-900 mb-3">学业成绩</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="label">GPA <span className="text-red-500">*</span></label>
            <input
              type="number" step="0.01"
              {...register("gpa", { required: true, min: 0, valueAsNumber: true })}
              className="input-field"
              placeholder="如：3.7"
            />
          </div>
          <div>
            <label className="label">GPA满分 <span className="text-red-500">*</span></label>
            <input
              type="number" step="0.01"
              {...register("gpa_full", { required: true, min: 0.1, valueAsNumber: true })}
              className="input-field"
              placeholder="如：4.0"
            />
          </div>
          <div>
            <label className="label">专业排名 <span className="text-red-500">*</span></label>
            <input
              type="number"
              {...register("major_rank", { required: true, min: 1, valueAsNumber: true })}
              className="input-field"
              placeholder="如：8"
            />
          </div>
          <div>
            <label className="label">专业总人数 <span className="text-red-500">*</span></label>
            <input
              type="number"
              {...register("major_rank_total", { required: true, min: 1, valueAsNumber: true })}
              className="input-field"
              placeholder="如：80"
            />
          </div>
        </div>
      </div>

      {/* English */}
      <div className="border-t pt-4">
        <h3 className="font-medium text-gray-900 mb-3">英语能力</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="label">四级成绩</label>
            <input type="number" {...register("cet4_score", { min: 200, max: 710, valueAsNumber: true })} className="input-field" placeholder="如：580" />
          </div>
          <div>
            <label className="label">六级成绩</label>
            <input type="number" {...register("cet6_score", { min: 200, max: 710, valueAsNumber: true })} className="input-field" placeholder="如：530" />
          </div>
          <div>
            <label className="label">雅思</label>
            <input type="number" step="0.5" {...register("ielts_score", { min: 0, max: 9, valueAsNumber: true })} className="input-field" placeholder="如：6.5" />
          </div>
          <div>
            <label className="label">托福</label>
            <input type="number" {...register("toefl_score", { min: 0, max: 120, valueAsNumber: true })} className="input-field" placeholder="如：90" />
          </div>
        </div>
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">英文读写能力</label>
            <select {...register("english_reading_level")} className="input-field">
              <option value="基础">基础（能读中文资料为主）</option>
              <option value="可阅读英文文献">可阅读英文文献（读paper无障碍）</option>
              <option value="流利">流利（英文写作/口语均可）</option>
            </select>
          </div>
          <div>
            <label className="label">科研/工程取向</label>
            <select {...register("research_orientation")} className="input-field">
              <option value="偏科研">偏科研（更感兴趣发论文、做研究）</option>
              <option value="偏工程">偏工程（更感兴趣做系统、做产品）</option>
              <option value="均衡">均衡（两者都行）</option>
            </select>
          </div>
        </div>
      </div>

      {/* Disciplinary */}
      <div className="border-t pt-4">
        <div className="flex items-center gap-3">
          <input type="checkbox" {...register("has_disciplinary_issues")} id="disciplinary" className="w-4 h-4" />
          <label htmlFor="disciplinary" className="text-sm text-gray-700">
            有挂科或纪律处分记录
            <span className="text-gray-400 ml-1 text-xs">（可能影响推免资格，需如实填写）</span>
          </label>
        </div>
        {hasDisciplinary && (
          <textarea {...register("disciplinary_notes")} className="input-field mt-2" placeholder="简要说明情况（选填）" rows={2} />
        )}
      </div>

      <div className="flex justify-end">
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? "保存中..." : "下一步：科研经历 →"}
        </button>
      </div>
    </form>
  );
}
