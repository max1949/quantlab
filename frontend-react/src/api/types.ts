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
  active_project_id: string | null;
}

export interface JourneyStep {
  key: string;
  label: string;
  done: boolean;
  challenge_milestones: ChallengeMilestoneLink[];
}

export interface ChallengeMilestoneLink {
  code: string;
  day: number;
  title: string;
  completed: boolean;
}

export interface ResearchJourney {
  done_count: number;
  total: number;
  steps: JourneyStep[];
  active_project_id: string | null;
  challenge_enrolled: boolean;
  challenge_code: string | null;
  challenge_completed_count: number;
  challenge_total: number;
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
  min_level?: number;
  min_tier?: number;
  allowed?: boolean;
  lock_hint?: string | null;
  suitable_for?: string;
  factor_template_label?: string;
  factor_note?: string;
  how_it_works?: string;
  learning_steps?: string[];
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
  academy_rewards?: AcademyReward[];
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

export interface ParamHelp {
  tip: string;
  low_hint: string;
  high_hint: string;
  suggested: string;
}

export interface ParamSpec {
  name: string;
  default: number;
  min: number;
  max: number;
  label: string;
  help?: ParamHelp | null;
}

export interface FactorTemplateMeta {
  code: string;
  label: string;
  description: string;
  how_it_works?: string;
  params: ParamSpec[];
  requires: string[];
  min_level?: number;
  min_tier?: number;
  allowed?: boolean;
}

export interface Plan {
  code: string;
  name: string;
  tier: number;
  price_cny: number;
  period_days: number;
  tagline: string;
  features: string[];
}

export interface SubscriptionStatus {
  tier: number;
  tier_name: string;
  plan_code: string;
  expires_at: string | null;
  is_paid: boolean;
}

export interface FeatureState {
  key: string;
  label: string;
  allowed: boolean;
  level_ok: boolean;
  tier_ok: boolean;
  min_level: number;
  min_level_name: string;
  min_tier: number;
  min_tier_name: string;
}

export interface MarketDataEntitlement {
  allowed_timeframes: string[];
  limits: Record<string, { max_bars: number | null; label: string }>;
  summary: string;
}

export interface Entitlements {
  level: number;
  level_name: string;
  tier: number;
  tier_name: string;
  features: FeatureState[];
  market_data: MarketDataEntitlement;
}

export interface FormulaHelp {
  variables: string[];
  functions: { name: string; desc: string }[];
  examples: string[];
}

export interface FactorPreview {
  factor_id: string;
  name: string;
  kind: string;
  sample_rows: number;
  stats: Record<string, number | null>;
  academy_rewards?: AcademyReward[];
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

export interface AcademyReward {
  code: string;
  title: string;
  awarded_xp: number;
  leveled_up: boolean;
}

export interface Backtest {
  id: string;
  factor_id: string;
  symbol: string;
  status: string;
  metrics: Record<string, number> | null;
  created_at: string;
  finished_at: string | null;
  academy_rewards?: AcademyReward[];
}

export interface BacktestDetail extends Backtest {
  equity_curve?: { date: string; equity: number | null }[] | null;
  report?: Record<string, unknown> | null;
  error?: string | null;
}

export interface Insight {
  id: string;
  kind: string;
  target_type: string;
  target_id: string;
  source: string;
  model: string | null;
  content: string;
  analysis: Record<string, unknown>;
  created_at: string;
}

export interface CrossSectionBacktest {
  factor_id: string;
  factor_name: string;
  symbols: string[];
  top_n: number;
  long_short: boolean;
  metrics: Record<string, number | null>;
  equity_curve: { date: string; equity: number | null }[];
  latest_weights: Record<string, number | null>;
}

export interface CostSensitivityPoint {
  fee_rate: number;
  slippage_bps: number;
  metrics: Record<string, number | null>;
}

export interface CostSensitivity {
  factor_id: string;
  factor_name: string;
  symbol: string;
  results: CostSensitivityPoint[];
}

export interface OrthogonalizeResult {
  target_factor_id: string;
  target_factor_name: string;
  control_factors: { id: string; name: string }[];
  symbol: string;
  result: Record<string, unknown>;
}

export interface RobustnessTest {
  factor_id: string;
  factor_name: string;
  symbol: string;
  sensitivity: Record<string, unknown>;
  verdict: Record<string, unknown>;
}

export interface OverfitCheck {
  factor_id: string;
  factor_name: string;
  symbol: string;
  oos: Record<string, unknown>;
  walk_forward: Record<string, unknown>;
  sensitivity: Record<string, unknown>;
  overfit: {
    risk_score?: number;
    grade?: string;
    flags?: { level: string; message: string }[];
    inputs?: Record<string, number | null>;
    [key: string]: unknown;
  };
}

export interface PortfolioOptimize {
  symbols: string[];
  method: string;
  weights: Record<string, number | null>;
  expected: Record<string, number | null>;
  asset_stats: Record<string, Record<string, number | null>>;
}

export interface PaperSimulate {
  symbols: string[];
  weights: Record<string, number>;
  rebalance: string;
  metrics: Record<string, number | null>;
  equity_curve: { date: string; equity: number | null }[];
}

export interface Validation {
  id: string;
  factor_id: string;
  symbol: string;
  status: string;
  robustness: Record<string, unknown> | null;
  created_at: string;
  finished_at: string | null;
  academy_rewards?: AcademyReward[];
}

export interface ValidationDetail extends Validation {
  oos: Record<string, unknown> | null;
  walk_forward: Record<string, unknown> | null;
  sensitivity: Record<string, unknown> | null;
  oos_ratio: number;
  n_splits: number;
  error: string | null;
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
  oos_sharpe?: number | null;
  robustness_score?: number | null;
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
  academy_rewards?: AcademyReward[];
}

export interface ShareOut {
  token: string;
  share_path: string;
  card: ShareCard;
  views: number;
  academy_rewards?: AcademyReward[];
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
  journey_key?: string | null;
  journey_label?: string | null;
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
