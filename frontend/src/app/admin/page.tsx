"use client";
import { useState, useEffect } from "react";
import { listDocuments, crawlUrl, uploadDocument, listPrograms, listCases } from "@/lib/api";

export default function AdminPage() {
  const [tab, setTab] = useState<"documents" | "programs" | "cases">("documents");
  const [documents, setDocuments] = useState<any[]>([]);
  const [programs, setPrograms] = useState<any[]>([]);
  const [cases, setCases] = useState<any[]>([]);
  const [urlInput, setUrlInput] = useState("");
  const [sourceType, setSourceType] = useState("experience_post");
  const [year, setYear] = useState(new Date().getFullYear());
  const [institution, setInstitution] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (tab === "documents") loadDocuments();
    else if (tab === "programs") loadPrograms();
    else if (tab === "cases") loadCases();
  }, [tab]);

  const loadDocuments = async () => {
    try {
      const data = await listDocuments();
      setDocuments(data);
    } catch (e) { console.error(e); }
  };

  const loadPrograms = async () => {
    try {
      const data = await listPrograms();
      setPrograms(data);
    } catch (e) { console.error(e); }
  };

  const loadCases = async () => {
    try {
      const data = await listCases();
      setCases(data);
    } catch (e) { console.error(e); }
  };

  const handleCrawl = async () => {
    if (!urlInput) return;
    setLoading(true);
    setMessage("");
    try {
      await crawlUrl(urlInput, sourceType, year, institution || undefined);
      setMessage(`✓ 已提交爬取：${urlInput}`);
      setUrlInput("");
      setTimeout(loadDocuments, 2000);
    } catch (e: any) {
      setMessage(`✗ 提交失败：${e?.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setMessage("");
    try {
      await uploadDocument(file, sourceType, year, institution || undefined);
      setMessage(`✓ 已提交处理：${file.name}`);
      setTimeout(loadDocuments, 2000);
    } catch (err: any) {
      setMessage(`✗ 上传失败：${err?.message}`);
    } finally {
      setLoading(false);
      e.target.value = "";
    }
  };

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      done: "bg-green-100 text-green-700",
      pending: "bg-yellow-100 text-yellow-700",
      processing: "bg-blue-100 text-blue-700",
      failed: "bg-red-100 text-red-700",
      needs_review: "bg-purple-100 text-purple-700",
    };
    return `text-xs px-2 py-0.5 rounded-full ${colors[status] || "bg-gray-100 text-gray-600"}`;
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">管理后台</h1>

      {/* Tabs */}
      <div className="flex gap-4 border-b mb-6">
        {(["documents", "programs", "cases"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`pb-2 px-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? "border-blue-600 text-blue-600" : "border-transparent text-gray-500"
            }`}
          >
            {t === "documents" ? "📄 文档管理" : t === "programs" ? "🏫 院校画像" : "📊 案例库"}
          </button>
        ))}
      </div>

      {tab === "documents" && (
        <div>
          {/* Ingestion panel */}
          <div className="card p-5 mb-6">
            <h2 className="font-medium mb-4">导入资料</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="label">来源类型</label>
                <select value={sourceType} onChange={(e) => setSourceType(e.target.value)} className="input-field">
                  <option value="official_notice">官方招生通知</option>
                  <option value="department_page">学院官网页面</option>
                  <option value="advisor_page">导师主页</option>
                  <option value="experience_post">经验帖</option>
                  <option value="offer_screenshot">offer截图</option>
                  <option value="qq_group">QQ群消息</option>
                  <option value="unknown">未知/其他</option>
                </select>
              </div>
              <div>
                <label className="label">所属申请年份</label>
                <input type="number" value={year} onChange={(e) => setYear(Number(e.target.value))} className="input-field" />
              </div>
              <div>
                <label className="label">院校提示（选填）</label>
                <input value={institution} onChange={(e) => setInstitution(e.target.value)} className="input-field" placeholder="如：清华大学" />
              </div>
            </div>

            <div className="flex gap-4 flex-wrap">
              <div className="flex-1 flex gap-2">
                <input
                  value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)}
                  className="input-field flex-1"
                  placeholder="输入网页URL..."
                />
                <button onClick={handleCrawl} className="btn-primary whitespace-nowrap" disabled={loading || !urlInput}>
                  {loading ? "..." : "爬取网页"}
                </button>
              </div>
              <div>
                <label className="btn-primary cursor-pointer">
                  上传PDF/图片
                  <input type="file" accept=".pdf,image/*" className="hidden" onChange={handleFileUpload} />
                </label>
              </div>
            </div>

            {message && (
              <div className={`mt-3 text-sm p-2 rounded ${message.startsWith("✓") ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}>
                {message}
              </div>
            )}
          </div>

          {/* Document list */}
          <div className="card overflow-hidden">
            <div className="px-5 py-3 border-b bg-gray-50 flex justify-between items-center">
              <span className="font-medium text-sm">文档列表（{documents.length}）</span>
              <button onClick={loadDocuments} className="text-sm text-blue-600 hover:underline">刷新</button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500">
                  <tr>
                    <th className="px-4 py-2 text-left">ID</th>
                    <th className="px-4 py-2 text-left">来源</th>
                    <th className="px-4 py-2 text-left">类型</th>
                    <th className="px-4 py-2 text-left">状态</th>
                    <th className="px-4 py-2 text-left">可信度</th>
                    <th className="px-4 py-2 text-left">年份</th>
                    <th className="px-4 py-2 text-left">标题/URL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-gray-50">
                      <td className="px-4 py-2 text-gray-400">{doc.id}</td>
                      <td className="px-4 py-2">
                        <span className="text-xs bg-gray-100 px-1.5 py-0.5 rounded">{doc.source_type}</span>
                      </td>
                      <td className="px-4 py-2">{doc.doc_type}</td>
                      <td className="px-4 py-2">
                        <span className={statusBadge(doc.parse_status)}>{doc.parse_status}</span>
                      </td>
                      <td className="px-4 py-2">{(doc.credibility_score * 100).toFixed(0)}%</td>
                      <td className="px-4 py-2">{doc.application_year || "-"}</td>
                      <td className="px-4 py-2 max-w-xs truncate text-gray-600">
                        {doc.title || doc.url || doc.file_path || "-"}
                      </td>
                    </tr>
                  ))}
                  {documents.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                        暂无文档。使用上方表单导入资料。
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {tab === "programs" && (
        <div className="card overflow-hidden">
          <div className="px-5 py-3 border-b bg-gray-50 flex justify-between">
            <span className="font-medium text-sm">院校项目画像（{programs.length}）</span>
            <button onClick={loadPrograms} className="text-sm text-blue-600 hover:underline">刷新</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500">
                <tr>
                  <th className="px-4 py-2 text-left">学校</th>
                  <th className="px-4 py-2 text-left">院系</th>
                  <th className="px-4 py-2 text-left">方向</th>
                  <th className="px-4 py-2 text-left">类型</th>
                  <th className="px-4 py-2 text-left">城市</th>
                  <th className="px-4 py-2 text-left">排名门槛</th>
                  <th className="px-4 py-2 text-left">置信度</th>
                  <th className="px-4 py-2 text-left">证据数</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {programs.map((p) => (
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium">{p.school}</td>
                    <td className="px-4 py-2 text-gray-600 text-xs max-w-xs truncate">{p.department}</td>
                    <td className="px-4 py-2 text-gray-600">{p.direction}</td>
                    <td className="px-4 py-2">
                      <span className="text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">{p.program_type}</span>
                    </td>
                    <td className="px-4 py-2">{p.city || "-"}</td>
                    <td className="px-4 py-2">{p.rank_threshold_hint ? `前${(p.rank_threshold_hint * 100).toFixed(0)}%` : "-"}</td>
                    <td className="px-4 py-2">{(p.profile_confidence * 100).toFixed(0)}%</td>
                    <td className="px-4 py-2">{p.evidence_count}</td>
                  </tr>
                ))}
                {programs.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-gray-400">
                      暂无院校画像。请运行 <code>python scripts/seed_programs.py</code> 导入种子数据。
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === "cases" && (
        <div className="card overflow-hidden">
          <div className="px-5 py-3 border-b bg-gray-50 flex justify-between">
            <span className="font-medium text-sm">申请案例库（{cases.length}）</span>
            <button onClick={loadCases} className="text-sm text-blue-600 hover:underline">刷新</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500">
                <tr>
                  <th className="px-4 py-2 text-left">年份</th>
                  <th className="px-4 py-2 text-left">申请人背景</th>
                  <th className="px-4 py-2 text-left">目标院校</th>
                  <th className="px-4 py-2 text-left">目标院系</th>
                  <th className="px-4 py-2 text-left">结果</th>
                  <th className="px-4 py-2 text-left">可信度</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {cases.map((c) => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="px-4 py-2">{c.application_year}</td>
                    <td className="px-4 py-2 text-xs">
                      {c.applicant_school}（{c.applicant_school_tier}）
                      {c.applicant_rank_percentile && ` 前${(c.applicant_rank_percentile * 100).toFixed(0)}%`}
                      {c.applicant_has_paper && " 有论文"}
                    </td>
                    <td className="px-4 py-2 font-medium">{c.target_school}</td>
                    <td className="px-4 py-2 text-xs text-gray-600">{c.target_department}</td>
                    <td className="px-4 py-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        c.case_type === "success" ? "bg-green-100 text-green-700" :
                        c.case_type === "failure" ? "bg-red-100 text-red-700" :
                        "bg-yellow-100 text-yellow-700"
                      }`}>
                        {c.case_type === "success" ? "录取" : c.case_type === "failure" ? "未录取" : "部分"}
                      </span>
                      {c.camp_result && <span className="ml-1 text-xs text-gray-500">{c.camp_result}</span>}
                    </td>
                    <td className="px-4 py-2">{(c.credibility * 100).toFixed(0)}%</td>
                  </tr>
                ))}
                {cases.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-400">
                      暂无案例数据。
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
