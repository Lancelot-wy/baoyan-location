import axios from "axios";
import type {
  UserProfileCreate, UserProfileOut,
  ResearchExperienceCreate, PaperCreate,
  CompetitionCreate, InternshipCreate,
  PreferenceProfileCreate,
  FullRecommendationResponse,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 300000, // 5 min — generation calls LLM multiple times
});

// ─── Student API ───────────────────────────────────────────────────────────

export async function createStudentProfile(data: UserProfileCreate): Promise<UserProfileOut> {
  const res = await api.post("/students/", data);
  return res.data;
}

export async function updateStudentProfile(
  sessionId: string,
  data: Partial<UserProfileCreate>
): Promise<UserProfileOut> {
  const res = await api.put(`/students/${sessionId}`, data);
  return res.data;
}

export async function addResearchExperience(
  sessionId: string,
  data: ResearchExperienceCreate
) {
  const res = await api.post(`/students/${sessionId}/research`, data);
  return res.data;
}

export async function addPaper(sessionId: string, data: PaperCreate) {
  const res = await api.post(`/students/${sessionId}/papers`, data);
  return res.data;
}

export async function addCompetition(sessionId: string, data: CompetitionCreate) {
  const res = await api.post(`/students/${sessionId}/competitions`, data);
  return res.data;
}

export async function addInternship(sessionId: string, data: InternshipCreate) {
  const res = await api.post(`/students/${sessionId}/internships`, data);
  return res.data;
}

export async function setPreferences(sessionId: string, data: PreferenceProfileCreate) {
  const res = await api.put(`/students/${sessionId}/preferences`, data);
  return res.data;
}

// ─── Recommendation API ────────────────────────────────────────────────────

export async function generateRecommendations(sessionId: string) {
  const res = await api.post("/recommendations/generate", { session_id: sessionId });
  return res.data;
}

export async function getRecommendations(sessionId: string): Promise<FullRecommendationResponse> {
  const res = await api.get(`/recommendations/${sessionId}`);
  return res.data;
}

export async function pollRecommendations(
  sessionId: string,
  onDone: (data: FullRecommendationResponse) => void,
  onError: (err: string) => void,
  intervalMs = 2000,
  maxAttempts = 60
): Promise<void> {
  let attempts = 0;

  const poll = async () => {
    attempts++;
    try {
      const data = await getRecommendations(sessionId);
      if (data.status === "done") {
        onDone(data);
        return;
      }
      if (data.status === "failed") {
        onError(data.error || "推荐生成失败");
        return;
      }
      if (attempts >= maxAttempts) {
        onError("推荐生成超时，请刷新页面重试");
        return;
      }
      setTimeout(poll, intervalMs);
    } catch (err: any) {
      onError(err?.message || "网络错误");
    }
  };

  await poll();
}

// ─── Admin API ─────────────────────────────────────────────────────────────

export async function uploadDocument(
  file: File,
  sourceType?: string,
  applicationYear?: number,
  institutionHint?: string
) {
  const formData = new FormData();
  formData.append("file", file);
  if (sourceType) formData.append("source_type", sourceType);
  if (applicationYear) formData.append("application_year", String(applicationYear));
  if (institutionHint) formData.append("institution_hint", institutionHint);

  const res = await api.post("/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function crawlUrl(
  url: string,
  sourceType?: string,
  applicationYear?: number,
  institutionHint?: string
) {
  const res = await api.post("/documents/crawl", {
    url, source_type: sourceType,
    application_year: applicationYear,
    institution_hint: institutionHint,
  });
  return res.data;
}

export async function listDocuments(skip = 0, limit = 50) {
  const res = await api.get("/documents/", { params: { skip, limit } });
  return res.data;
}

export async function listPrograms(school?: string) {
  const res = await api.get("/programs/", { params: { school, limit: 200 } });
  return res.data;
}

export async function listCases(school?: string, year?: number) {
  const res = await api.get("/cases/", { params: { school, year, limit: 100 } });
  return res.data;
}
