// 与后端 (FastAPI /api/v1) schema 对齐的前端类型定义。

export type UserType = "newbie" | "python" | "trader" | "unset";

export interface User {
  id: string;
  email: string;
  username: string;
  level: number;
  level_label: string;
  experience: number;
  experience_to_next_level: number | null;
  research_score: number;
  reward_points: number;
  research_contribution_score: number;
  user_type: string;
  user_type_label: string;
  onboarding_done: boolean;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface NextStep {
  user_type: string;
  user_type_label: string;
  intro: string;
  stage: string;
  title: string;
  action: string;
  cta_path: string;
  recommended_template: string | null;
}

export interface Mentor {
  stage: string;
  title: string;
  action: string;
  cta_path: string;
  message: string;
  recommended_template: string | null;
  disclaimer: string;
}

export interface Template {
  code: string;
  title: string;
  symbol: string;
  factor_template: string;
  default_params: Record<string, number>;
  hypothesis: string;
  description: string;
  tags: string[];
}

export interface StartTemplateResult {
  project_id: string;
  factor_id: string | null;
  template_code: string;
}

export interface Project {
  id: string;
  owner_id: string;
  title: string;
  symbol: string;
  question: string;
  description: string;
  status: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface GraphNode {
  id: string;
  kind: string;
  label: string;
  ref_type: string | null;
  ref_id: string | null;
  detail: Record<string, unknown>;
  order: number;
}

export interface GraphEdge {
  from: string;
  to: string;
  label: string;
}

export interface Graph {
  project_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface Factor {
  id: string;
  owner_id: string;
  project_id: string | null;
  name: string;
  kind: string;
  template_type: string | null;
  spec: Record<string, unknown>;
  version: number;
  created_at: string;
}

export interface Backtest {
  id: string;
  factor_id: string;
  symbol: string;
  status: string;
  metrics: Record<string, number> | null;
  created_at: string;
  finished_at: string | null;
}

export interface Validation {
  id: string;
  factor_id: string;
  symbol: string;
  status: string;
  robustness: Record<string, unknown> | null;
  created_at: string;
  finished_at: string | null;
}

export interface ReportSummary {
  id: string;
  owner_id: string;
  project_id: string | null;
  factor_id: string;
  symbol: string;
  title: string;
  grade: string | null;
  stages: Record<string, unknown>;
  is_public: boolean;
  created_at: string;
}

export interface ReportDetail extends ReportSummary {
  factor_version: number;
  summary: string;
  hypothesis: string;
  methodology: string;
  result: string;
  risk_analysis: string;
  improvement_suggestion: string;
  narrative: Record<string, unknown>;
  based_on: Record<string, unknown>;
}

export interface ShareOut {
  token: string;
  share_path: string;
  card: ShareCard;
  views: number;
}

export interface ShareCard {
  title?: string;
  researcher?: string;
  researcher_level?: number;
  symbol?: string;
  grade?: string | null;
  summary?: string;
  hypothesis?: string;
  [key: string]: unknown;
}

export interface ShareCardPublic {
  token: string;
  card: ShareCard;
  views: number;
  created_at: string;
}

export interface ResearcherProfile {
  user_id: string;
  username: string;
  level: number;
  level_label: string;
  research_score: number;
  reward_points: number;
  research_contribution_score: number;
  experience: number;
  project_count: number;
  factor_count: number;
  validation_count: number;
  effective_validation_count: number;
  report_count: number;
  followers: number;
  following: number;
  is_following: boolean;
  tags: string[];
  joined_at: string;
}

export interface LeaderRow {
  rank: number;
  user_id: string;
  username: string;
  level: number;
  metric_label: string;
  metric_value: number;
}

export interface Referral {
  code: string;
  share_path: string;
  invited: number;
  activated: number;
  reward_points_earned: number;
}

export interface Milestone {
  day: number;
  code: string;
  title: string;
  completed: boolean;
  reward_points: number;
}

export interface ChallengeProgress {
  code: string;
  title: string;
  days: number;
  completed_count: number;
  total: number;
  percent: number;
  milestones: Milestone[];
  enrolled_at: string;
  newly_awarded_points: number;
  reward_points: number;
  certificate_code: string | null;
  completed_at: string | null;
}

export interface ChallengeOut {
  id: string;
  code: string;
  title: string;
  description: string;
  days: number;
  milestones: unknown[];
}

export interface Certificate {
  certificate_code: string;
  challenge_title: string;
  username: string;
  completed_at: string | null;
}

export type LeaderboardKind =
  | "researcher"
  | "contributor"
  | "newcomer"
  | "improved";
