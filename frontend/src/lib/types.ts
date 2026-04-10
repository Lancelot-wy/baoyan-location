// ─── Enums ────────────────────────────────────────────────────────────────────

export type SchoolTier = "985" | "211" | "双非" | "其他";
export type MajorCategory =
  | "计算机科学与技术" | "软件工程" | "人工智能"
  | "数据科学" | "电子信息" | "数学" | "物理" | "其他";
export type CurrentYear = "大三" | "大四" | "已毕业";
export type EnglishReadingLevel = "基础" | "可阅读英文文献" | "流利";
export type ResearchOrientation = "偏科研" | "偏工程" | "均衡";
export type UserRole = "旁观" | "辅助" | "独立模块" | "主负责";
export type VenueLevel = "CCF-A" | "CCF-B" | "CCF-C" | "SCI" | "EI" | "顶会" | "普通期刊" | "在投" | "其他";
export type PaperStatus = "已发表" | "在投" | "在写";
export type CompetitionCategory = "ACM" | "数学建模" | "信息安全" | "机器学习" | "数据挖掘" | "其他";
export type CompetitionLevel = "国际" | "国家" | "省级" | "校级";
export type CompetitionAward = "金" | "银" | "铜" | "一等" | "二等" | "三等" | "优秀" | "参与";
export type Relevance = "高度相关" | "部分相关" | "不相关";
export type CareerGoal = "就业" | "读博" | "考公" | "选调" | "出国" | "未定";
export type RiskAppetite = "冲刺" | "稳健" | "保守";
export type RecommendationTier = "冲刺" | "主申" | "保底";
export type ReasonType = "strength" | "weakness" | "risk" | "opportunity";

// ─── Request types ─────────────────────────────────────────────────────────

export interface UserProfileCreate {
  undergraduate_school: string;
  school_tier: SchoolTier;
  major_name: string;
  major_category: MajorCategory;
  current_year: CurrentYear;
  has_guaranteed_admission: boolean;
  gpa: number;
  gpa_full: number;
  major_rank: number;
  major_rank_total: number;
  comprehensive_rank?: number;
  comprehensive_rank_total?: number;
  has_disciplinary_issues: boolean;
  disciplinary_notes?: string;
  cet4_score?: number;
  cet6_score?: number;
  ielts_score?: number;
  toefl_score?: number;
  english_reading_level: EnglishReadingLevel;
  research_orientation: ResearchOrientation;
}

export interface ResearchExperienceCreate {
  start_date: string;        // YYYY-MM-DD
  end_date?: string;
  advisor_name: string;
  advisor_title?: string;
  advisor_institution: string;
  research_direction: string;
  is_long_term: boolean;
  user_role: UserRole;
  has_advisor_endorsement: boolean;
  notes?: string;
}

export interface PaperCreate {
  title: string;
  venue: string;
  venue_level: VenueLevel;
  status: PaperStatus;
  author_position: number;
  total_authors: number;
  research_direction: string;
  actual_contribution?: string;
  has_open_source: boolean;
  paper_url?: string;
  year: number;
}

export interface CompetitionCreate {
  name: string;
  category: CompetitionCategory;
  level: CompetitionLevel;
  award: CompetitionAward;
  is_team: boolean;
  team_size?: number;
  user_role?: string;
  relevance_to_application: Relevance;
  year: number;
}

export interface InternshipCreate {
  company: string;
  position: string;
  department?: string;
  start_date: string;
  end_date?: string;
  is_ongoing: boolean;
  relevance: Relevance;
  is_research_type: boolean;
  notes?: string;
}

export interface PreferenceProfileCreate {
  career_goal: CareerGoal;
  risk_appetite: RiskAppetite;
  accept_high_pressure_advisor: boolean;
  prioritize_city: boolean;
  prioritize_school_brand: boolean;
  prioritize_internship_resources: boolean;
  prioritize_phd_track: boolean;
  accept_cross_direction: boolean;
  preferred_cities: string[];
  excluded_cities: string[];
  care_about_living_cost: boolean;
  care_about_internet_industry: boolean;
  accept_remote_study: boolean;
  target_directions: string[];
  notes?: string;
}

// ─── Response types ────────────────────────────────────────────────────────

export interface UserProfileOut extends UserProfileCreate {
  id: number;
  session_id: string;
  rank_percentile: number;
  created_at: string;
  updated_at: string;
}

export interface RecommendationReason {
  id: number;
  reason_type: ReasonType;
  reason_text: string;
  confidence: number;
}

export interface RecommendationResultOut {
  id: number;
  school: string;
  department: string;
  direction: string;
  program_type: string;
  advisor_name?: string;
  tier: RecommendationTier;
  compatibility_score: number;
  admission_probability_low: number;
  admission_probability_high: number;
  career_fit_score?: number;
  phd_fit_score?: number;
  rank: number;
  evidence_summary: string;
  risk_summary: string;
  preparation_advice: string;
  is_suitable_for_reach: boolean;
  is_suitable_for_safe: boolean;
  employment_pros?: string;
  employment_cons?: string;
  phd_pros?: string;
  phd_cons?: string;
  reasons: RecommendationReason[];
}

export interface ProfileSummary {
  core_strengths: string[];
  core_weaknesses: string[];
  strategic_advice: string;
  timeline_advice: string;
  directions_to_avoid: string[];
  overall_assessment: string;
}

export interface FullRecommendationResponse {
  session_id: string;
  status: "processing" | "done" | "failed";
  results: RecommendationResultOut[];
  profile_summary?: ProfileSummary;
  error?: string;
}

// ─── Questionnaire step state ──────────────────────────────────────────────

export interface QuestionnaireState {
  step: number;
  session_id?: string;
  profile?: UserProfileCreate;
  research_experiences: ResearchExperienceCreate[];
  papers: PaperCreate[];
  competitions: CompetitionCreate[];
  internships: InternshipCreate[];
  preferences?: PreferenceProfileCreate;
}
