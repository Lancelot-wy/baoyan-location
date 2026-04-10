"use client";
import { useState } from "react";
import { useForm } from "react-hook-form";
import type { PaperCreate } from "@/lib/types";

interface Props {
  onSubmit: (papers: PaperCreate[]) => void;
  onBack: () => void;
  loading: boolean;
}

export default function StepPapers({ onSubmit, onBack, loading }: Props) {
  const [papers, setPapers] = useState<PaperCreate[]>([]);
  const [adding, setAdding] = useState(false);
  const { register, handleSubmit, reset } = useForm<PaperCreate>({
    defaultValues: { year: new Date().getFullYear(), author_position: 1, total_authors: 3 },
  });

  const addPaper = (data: PaperCreate) => {
    setPapers((prev) => [...prev, { ...data, author_position: Number(data.author_position), total_authors: Number(data.total_authors), year: Number(data.year) }]);
    reset({ year: new Date().getFullYear(), author_position: 1, total_authors: 3 });
    setAdding(false);
  };

  const removePaper = (i: number) => setPapers((prev) => prev.filter((_, idx) => idx !== i));

  const VENUE_LEVELS = [
    { value: "CCF-A", label: "CCF-A（顶级，如NeurIPS/CVPR/ACL/SIGMOD等）" },
    { value: "顶会", label: "顶级会议/期刊（非CCF分类但公认顶会）" },
    { value: "CCF-B", label: "CCF-B" },
    { value: "SCI", label: "SCI期刊" },
    { value: "CCF-C", label: "CCF-C" },
    { value: "EI", label: "EI收录" },
    { value: "普通期刊", label: "普通期刊/会议" },
    { value: "在投", label: "在投（还未接收）" },
    { value: "其他", label: "其他" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-gray-900">第三步：论文成果</h2>
        <p className="text-sm text-gray-500 mt-1">
          包括已发表、在投、甚至在写的论文。在投和在写的论文也有参考价值。
        </p>
      </div>

      {papers.map((paper, i) => (
        <div key={i} className="card p-4 border-l-4 border-l-purple-500">
          <div className="flex justify-between items-start">
            <div>
              <div className="font-medium text-sm">{paper.title}</div>
              <div className="text-xs text-gray-600 mt-1">
                <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded">{paper.venue_level}</span>
                <span className="ml-2">{paper.venue}</span>
                <span className="ml-2">{paper.status}</span>
                <span className="ml-2">第{paper.author_position}作者/共{paper.total_authors}人</span>
              </div>
            </div>
            <button onClick={() => removePaper(i)} className="text-red-400 hover:text-red-600 text-sm">删除</button>
          </div>
        </div>
      ))}

      {adding ? (
        <form onSubmit={handleSubmit(addPaper)} className="card p-6 space-y-4">
          <h3 className="font-medium">添加论文</h3>
          <div>
            <label className="label">论文标题 *</label>
            <input {...register("title", { required: true })} className="input-field" placeholder="论文完整标题" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">
                发表/投稿期刊/会议名称 *
              </label>
              <input {...register("venue", { required: true })} className="input-field" placeholder="如：NeurIPS 2025、IEEE TPAMI" />
            </div>
            <div>
              <label className="label">级别评定 *</label>
              <select {...register("venue_level", { required: true })} className="input-field">
                <option value="">请选择</option>
                {VENUE_LEVELS.map((v) => (
                  <option key={v.value} value={v.value}>{v.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">状态 *</label>
              <select {...register("status", { required: true })} className="input-field">
                <option value="">请选择</option>
                <option value="已发表">已发表/已接收</option>
                <option value="在投">在投（已投稿待审）</option>
                <option value="在写">在写（尚未投稿）</option>
              </select>
            </div>
            <div>
              <label className="label">年份 *</label>
              <input type="number" {...register("year", { required: true, valueAsNumber: true })} className="input-field" />
            </div>
            <div>
              <label className="label">你是第几作者 *</label>
              <input type="number" {...register("author_position", { required: true, min: 1, valueAsNumber: true })} className="input-field" />
            </div>
            <div>
              <label className="label">总作者数</label>
              <input type="number" {...register("total_authors", { required: true, min: 1, valueAsNumber: true })} className="input-field" />
            </div>
            <div>
              <label className="label">研究方向 *</label>
              <input {...register("research_direction", { required: true })} className="input-field" placeholder="如：自然语言处理" />
            </div>
            <div>
              <label className="label">论文链接（选填）</label>
              <input {...register("paper_url")} className="input-field" placeholder="arxiv或论文主页链接" />
            </div>
          </div>
          <div>
            <label className="label">实际贡献描述（选填）</label>
            <textarea {...register("actual_contribution")} className="input-field" rows={2}
              placeholder="如：负责模型设计和实验，完成了约60%的工作量" />
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" {...register("has_open_source")} id="opensource" />
            <label htmlFor="opensource" className="text-sm">代码已开源（GitHub等）</label>
          </div>
          <div className="flex gap-3">
            <button type="submit" className="btn-primary">添加这篇论文</button>
            <button type="button" onClick={() => setAdding(false)} className="btn-secondary">取消</button>
          </div>
        </form>
      ) : (
        <button
          onClick={() => setAdding(true)}
          className="w-full border-2 border-dashed border-gray-300 rounded-lg py-4 text-gray-500 hover:border-purple-400 hover:text-purple-600 transition-colors"
        >
          + 添加一篇论文
        </button>
      )}

      <div className="flex justify-between">
        <button onClick={onBack} className="btn-secondary">← 上一步</button>
        <button onClick={() => onSubmit(papers)} className="btn-primary" disabled={loading}>
          {loading ? "保存中..." : `下一步：竞赛经历 → ${papers.length > 0 ? `（已填${papers.length}篇）` : "（跳过）"}`}
        </button>
      </div>
    </div>
  );
}
