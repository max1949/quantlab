import axios from "axios";
import { api } from "./client";
import type {
  Backtest,
  Certificate,
  ChallengeOut,
  ChallengeProgress,
  CostSensitivity,
  CrossSectionBacktest,
  DataQuality,
  FactorCatalog,
  VolRegime,
  Entitlements,
  Factor,
  FactorPreview,
  FactorScan,
  FactorScanCompare,
  FactorTemplateMeta,
  FormulaHelp,
  FormulaEvaluate,
  PythonEvaluate,
  TemplateEvaluate,
  Graph,
  LeaderRow,
  Plan,
  SubscriptionStatus,
  LeaderboardKind,
  Mentor,
  NextStep,
  OrthogonalizeResult,
  OverfitCheck,
  PaperSimulate,
  PortfolioOptimize,
  Project,
  Referral,
  ReportDetail,
  ReportSummary,
  ResearchJourney,
  ResearcherProfile,
  RobustnessTest,
  ShareCardPublic,
  ShareOut,
  Template,
  Token,
  User,
  UserType,
  Validation,
  ValidationDetail,
  BacktestDetail,
  Insight,
} from "./types";

// ---- auth ----
export async function fetchCaptcha(): Promise<{ token: string; svg: string }> {
  const { data } = await api.get<{ token: string; svg: string }>("/auth/captcha");
  return data;
}

export async function register(body: {
  email: string;
  username: string;
  password: string;
  user_type?: UserType;
  ref?: string | null;
  captcha_token?: string;
  captcha_answer?: string;
}): Promise<{ access_token: string; user: User }> {
  const { data } = await api.post<{ access_token: string; user: User }>(
    "/auth/register",
    body
  );
  return data;
}

export async function login(body: {
  identifier: string;
  password: string;
  captcha_token?: string;
  captcha_answer?: string;
}): Promise<Token> {
  const { data } = await api.post<Token>("/auth/login", body);
  return data;
}

export async function getMe(): Promise<User> {
  const { data } = await api.get<User>("/users/me");
  return data;
}

// ---- onboarding ----
export async function chooseType(user_type: UserType): Promise<User> {
  const { data } = await api.post<User>("/onboarding/choose-type", {
    user_type,
  });
  return data;
}

export async function getNextStep(): Promise<NextStep> {
  const { data } = await api.get<NextStep>("/onboarding/next");
  return data;
}

export async function getResearchJourney(): Promise<ResearchJourney> {
  const { data } = await api.get<ResearchJourney>("/onboarding/journey");
  return data;
}

export async function getMentor(): Promise<Mentor> {
  const { data } = await api.get<Mentor>("/ai/mentor/next");
  return data;
}

// ---- templates ----
export async function listTemplates(): Promise<Template[]> {
  const { data } = await api.get<Template[]>("/research/templates");
  return data;
}

export async function startTemplate(
  code: string,
  with_factor = true,
): Promise<{ project_id: string; factor_id: string | null; template_code: string }> {
  const { data } = await api.post(`/research/templates/${code}/start`, {
    with_factor,
  });
  return data;
}

// ---- projects ----
export async function listProjects(): Promise<Project[]> {
  const { data } = await api.get<Project[]>("/projects");
  return data;
}

export async function createProject(body: {
  title: string;
  symbol?: string;
  question?: string;
  description?: string;
  tags?: string[];
}): Promise<Project> {
  const { data } = await api.post<Project>("/projects", body);
  return data;
}

export async function getProject(id: string): Promise<Project> {
  const { data } = await api.get<Project>(`/projects/${id}`);
  return data;
}

export async function getGraph(id: string): Promise<Graph> {
  const { data } = await api.get<Graph>(`/projects/${id}/graph`);
  return data;
}

export interface ProjectQuality {
  passed: boolean;
  reasons: string[];
  scorecard: Record<string, number | string | null>;
  hints?: string[];
  orthogonal?: {
    target_factor: string;
    control_factors: string[];
    r2: number | null;
    unique_ratio: number | null;
    verdict: string;
    hint: string | null;
  } | null;
  thresholds?: {
    min_oos_sharpe: number;
    min_robustness_score: number;
    min_backtest_sharpe: number;
    min_sealed_holdout_sharpe: number;
    allowed_robustness_grades: string[];
  };
}

export async function getProjectQuality(id: string): Promise<ProjectQuality> {
  const { data } = await api.get<ProjectQuality>(`/projects/${id}/quality`);
  return data;
}

export async function publishProject(id: string): Promise<Project> {
  const { data } = await api.post<Project>(`/projects/${id}/publish`);
  return data;
}

// ---- factors ----
export async function listFactors(): Promise<Factor[]> {
  const { data } = await api.get<Factor[]>("/factors");
  return data;
}

export async function getFactorTemplates(): Promise<FactorTemplateMeta[]> {
  const { data } = await api.get<FactorTemplateMeta[]>("/factors/templates");
  return data;
}

export async function createTemplateFactor(body: {
  name: string;
  template_type: string;
  params: Record<string, number>;
  project_id?: string;
}): Promise<Factor> {
  const { data } = await api.post<Factor>("/factors/template", body);
  return data;
}

export async function evaluateTemplateFactor(body: {
  template_type: string;
  params: Record<string, number>;
  symbol: string;
  timeframe?: string;
}): Promise<TemplateEvaluate> {
  const { data } = await api.post<TemplateEvaluate>("/factors/template/evaluate", body);
  return data;
}

export async function runFactorScan(body: {
  symbol: string;
  symbols?: string[];
  template_type?: string;
  timeframe?: string;
  project_id?: string;
  steps?: number;
  search_mode?: "grid" | "random" | "refine";
  factor_ids?: string[];
}): Promise<FactorScan> {
  const { data } = await api.post<FactorScan>("/factors/scan", body);
  return data;
}

export async function listFactorScans(opts?: {
  projectId?: string;
  symbol?: string;
  templateType?: string;
  limit?: number;
}): Promise<FactorScan[]> {
  const { data } = await api.get<FactorScan[]>("/factors/scans", {
    params: {
      project_id: opts?.projectId,
      symbol: opts?.symbol,
      template_type: opts?.templateType,
      limit: opts?.limit,
    },
  });
  return data;
}

export async function getFactorScan(scanId: string): Promise<FactorScan> {
  const { data } = await api.get<FactorScan>(`/factors/scans/${scanId}`);
  return data;
}

export async function compareFactorScans(
  scanA: string,
  scanB: string,
): Promise<FactorScanCompare> {
  const { data } = await api.get<FactorScanCompare>("/factors/scans/compare", {
    params: { scan_a: scanA, scan_b: scanB },
  });
  return data;
}

export async function reviewFactorScan(scanId: string): Promise<Insight> {
  const { data } = await api.post<Insight>(`/ai/scans/${scanId}/review`);
  return data;
}

export async function reviewFactorScansBatch(scanIds: string[]): Promise<Insight> {
  const { data } = await api.post<Insight>("/ai/scans/review-batch", { scan_ids: scanIds });
  return data;
}

export async function applyFactorScan(
  scanId: string,
  body: { rank?: number; name?: string },
): Promise<Factor> {
  const { data } = await api.post<Factor>(`/factors/scans/${scanId}/apply`, body);
  return data;
}

export async function createStackFactor(body: {
  name: string;
  components: { factor_id: string; weight: number }[];
  project_id?: string;
}): Promise<Factor> {
  const { data } = await api.post<Factor>("/factors/stack", body);
  return data;
}

export async function previewFactor(factorId: string): Promise<FactorPreview> {
  const { data } = await api.post<FactorPreview>(`/factors/${factorId}/preview`);
  return data;
}

export async function getFormulaHelp(): Promise<FormulaHelp> {
  const { data } = await api.get<FormulaHelp>("/factors/formula/help");
  return data;
}

export async function createFormulaFactor(body: {
  name: string;
  expr: string;
  project_id?: string;
}): Promise<Factor> {
  const { data } = await api.post<Factor>("/factors/formula", body);
  return data;
}

export async function evaluateFormulaExpr(body: {
  expr: string;
  symbol: string;
  timeframe?: string;
}): Promise<FormulaEvaluate> {
  const { data } = await api.post<FormulaEvaluate>(
    "/factors/formula/evaluate",
    body,
  );
  return data;
}

export async function evaluatePythonSource(body: {
  source: string;
  symbol: string;
  timeframe?: string;
}): Promise<PythonEvaluate> {
  const { data } = await api.post<PythonEvaluate>("/factors/python/evaluate", body);
  return data;
}

export type PythonFactorHelp = {
  template: string;
  variables: string[];
  notes: string[];
};

export async function getPythonFactorHelp(): Promise<PythonFactorHelp> {
  const { data } = await api.get<PythonFactorHelp>("/factors/python/help");
  return data;
}

export async function createPythonFactor(body: {
  name: string;
  source: string;
  project_id?: string;
}): Promise<Factor> {
  const { data } = await api.post<Factor>("/factors/python", body);
  return data;
}

export type PaperSnapshot = {
  as_of_date: string;
  symbol: string;
  timeframe: string;
  bars: number;
  nav_end: number;
  metrics: Record<string, number>;
  equity_tail: { date?: string; nav: number }[];
};

export type PaperHistory = {
  factor_id: string;
  snapshots: PaperSnapshot[];
  latest_preview: {
    nav_end: number;
    symbol: string;
    metrics: Record<string, number>;
  } | null;
  decay?: {
    status: "ok" | "watch" | "alert";
    reasons: string[];
    baseline_sharpe?: number | null;
    paper_sharpe?: number | null;
  };
};

export async function getPaperHistory(factorId: string): Promise<PaperHistory> {
  const { data } = await api.get<PaperHistory>(`/factors/${factorId}/paper-history`);
  return data;
}

export async function refreshPaperSnapshot(factorId: string): Promise<{
  as_of_date: string;
  nav_end: number;
  metrics: Record<string, number>;
}> {
  const { data } = await api.post(`/factors/${factorId}/paper-track/refresh`);
  return data;
}

export async function getPaperPreview(factorId: string): Promise<Record<string, unknown>> {
  const { data } = await api.get(`/factors/${factorId}/paper-preview`);
  return data;
}

// ---- billing / membership ----
export async function getPlans(): Promise<Plan[]> {
  const { data } = await api.get<Plan[]>("/billing/plans");
  return data;
}

export async function getSubscription(): Promise<SubscriptionStatus> {
  const { data } = await api.get<SubscriptionStatus>("/billing/me");
  return data;
}

export async function getEntitlements(): Promise<Entitlements> {
  const { data } = await api.get<Entitlements>("/billing/entitlements");
  return data;
}

export async function redeemCode(code: string): Promise<{
  ok: boolean;
  tier: number;
  tier_name: string;
  expires_at: string | null;
  message: string;
}> {
  const { data } = await api.post("/billing/redeem", { code });
  return data;
}

export async function checkout(plan_code: string): Promise<{
  configured: boolean;
  plan_code: string;
  plan_name: string;
  price_cny: number;
  message: string;
}> {
  const { data } = await api.post("/billing/checkout", { plan_code });
  return data;
}

// ---- backtest / validation ----
export interface MarketDataset {
  symbol: string;
  timeframe: string;
  start_date: string;
  end_date: string;
  rows: number;
  effective_rows?: number | null;
  tier_cap?: number | null;
}

export async function listDatasets(): Promise<MarketDataset[]> {
  const { data } = await api.get<MarketDataset[]>("/datasets");
  return data;
}

export async function getDataQuality(
  symbol: string,
  timeframe: string,
): Promise<DataQuality> {
  const { data } = await api.get<DataQuality>("/datasets/quality", {
    params: { symbol, timeframe },
  });
  return data;
}

export async function getVolRegime(symbol: string, timeframe: string): Promise<VolRegime> {
  const { data } = await api.get<VolRegime>("/datasets/regime", {
    params: { symbol, timeframe },
  });
  return data;
}

export async function getFactorCatalog(params: {
  projectId?: string;
  symbol?: string;
  timeframe?: string;
}): Promise<FactorCatalog> {
  const { data } = await api.get<FactorCatalog>("/factors/catalog", {
    params: {
      project_id: params.projectId,
      symbol: params.symbol,
      timeframe: params.timeframe ?? "1d",
    },
  });
  return data;
}

export async function createBacktest(body: {
  factor_id: string;
  symbol: string;
  timeframe?: string;
}): Promise<Backtest> {
  const { data } = await api.post<Backtest>("/backtests", body);
  return data;
}

export async function listBacktests(): Promise<Backtest[]> {
  const { data } = await api.get<Backtest[]>("/backtests");
  return data;
}

export async function getBacktest(id: string): Promise<BacktestDetail> {
  const { data } = await api.get<BacktestDetail>(`/backtests/${id}`);
  return data;
}

export async function reviewValidation(validationId: string): Promise<Insight> {
  const { data } = await api.post<Insight>(`/ai/validations/${validationId}/review`);
  return data;
}

export async function summarizeBacktest(backtestId: string): Promise<Insight> {
  const { data } = await api.post<Insight>(`/ai/backtests/${backtestId}/summary`);
  return data;
}

export async function runCrossSectionBacktest(body: {
  factor_id: string;
  symbols?: string[];
  top_n?: number;
  long_short?: boolean;
  fee_rate?: number;
  slippage_bps?: number;
}): Promise<CrossSectionBacktest> {
  const { data } = await api.post<CrossSectionBacktest>(
    "/backtests/cross-section",
    body,
  );
  return data;
}

export async function runCostSensitivity(body: {
  factor_id: string;
  symbol: string;
  fee_rates?: number[];
  slippage_bps_values?: number[];
}): Promise<CostSensitivity> {
  const { data } = await api.post<CostSensitivity>(
    "/backtests/cost-sensitivity",
    body,
  );
  return data;
}

export async function createValidation(body: {
  factor_id: string;
  symbol: string;
  timeframe?: string;
}): Promise<Validation> {
  const { data } = await api.post<Validation>("/validations", body);
  return data;
}

export async function listValidations(): Promise<Validation[]> {
  const { data } = await api.get<Validation[]>("/validations");
  return data;
}

export async function getValidation(id: string): Promise<ValidationDetail> {
  const { data } = await api.get<ValidationDetail>(`/validations/${id}`);
  return data;
}

export async function runOrthogonalize(body: {
  target_factor_id: string;
  control_factor_ids: string[];
  symbol: string;
}): Promise<OrthogonalizeResult> {
  const { data } = await api.post<OrthogonalizeResult>(
    "/validations/orthogonalize",
    body,
  );
  return data;
}

export async function runRobustnessTest(body: {
  factor_id: string;
  symbol: string;
}): Promise<RobustnessTest> {
  const { data } = await api.post<RobustnessTest>("/validations/robustness", body);
  return data;
}

export async function runOverfitCheck(body: {
  factor_id: string;
  symbol: string;
}): Promise<OverfitCheck> {
  const { data } = await api.post<OverfitCheck>("/validations/overfit-check", body);
  return data;
}

export async function optimizePortfolio(body: {
  symbols?: string[];
  method?: string;
}): Promise<PortfolioOptimize> {
  const { data } = await api.post<PortfolioOptimize>("/portfolio/optimize", body);
  return data;
}

export async function paperSimulate(body: {
  symbols?: string[];
  weights: Record<string, number>;
  rebalance?: string;
}): Promise<PaperSimulate> {
  const { data } = await api.post<PaperSimulate>("/portfolio/paper-simulate", body);
  return data;
}

// ---- reports ----
export async function generateReport(body: {
  project_id?: string;
  factor_id?: string;
}): Promise<ReportDetail> {
  const { data } = await api.post<ReportDetail>("/research/reports/generate", body);
  return data;
}

export async function listMyReports(): Promise<ReportSummary[]> {
  const { data } = await api.get<ReportSummary[]>("/research/reports");
  return data;
}

export async function getReport(id: string): Promise<ReportDetail> {
  const { data } = await api.get<ReportDetail>(`/research/reports/${id}`);
  return data;
}

export async function getPublicReport(id: string): Promise<ReportDetail> {
  const { data } = await api.get<ReportDetail>(`/public/reports/${id}`);
  return data;
}

/** 登录用户优先私有接口；未公开报告对他人仍 404。 */
export async function getReportForViewer(id: string, loggedIn: boolean): Promise<ReportDetail> {
  if (!loggedIn) return getPublicReport(id);
  try {
    return await getReport(id);
  } catch (e) {
    if (axios.isAxiosError(e) && (e.response?.status === 404 || e.response?.status === 403)) {
      return getPublicReport(id);
    }
    throw e;
  }
}

export async function shareReport(id: string): Promise<ShareOut> {
  const { data } = await api.post<ShareOut>(`/research/reports/${id}/share`);
  return data;
}

export async function getShareCard(token: string): Promise<ShareCardPublic> {
  const { data } = await api.get<ShareCardPublic>(`/share/${token}`);
  return data;
}

export async function getFeed(): Promise<ReportSummary[]> {
  const { data } = await api.get<ReportSummary[]>("/public/feed");
  return data;
}

export async function getPublicFeed(sort: "latest" | "top" = "top"): Promise<ReportSummary[]> {
  const { data } = await api.get<ReportSummary[]>("/public/feed", { params: { sort } });
  return data;
}

// ---- academy tasks ----
export interface AcademyTask {
  id: string;
  code: string;
  title: string;
  description: string;
  category: string;
  min_level: number;
  min_level_label: string;
  xp_reward: number;
  order_index: number;
  completed: boolean;
  locked: boolean;
  completed_at: string | null;
}

export async function listTasks(): Promise<AcademyTask[]> {
  const { data } = await api.get<AcademyTask[]>("/tasks");
  return data;
}

export async function completeTask(code: string): Promise<{
  awarded_xp: number;
  leveled_up: boolean;
  user: User;
}> {
  const { data } = await api.post(`/tasks/${code}/complete`);
  return data;
}

// ---- social ----
export async function getMyProfile(): Promise<ResearcherProfile> {
  const { data } = await api.get<ResearcherProfile>("/researchers/me");
  return data;
}

export async function getResearcher(userId: string): Promise<ResearcherProfile> {
  const { data } = await api.get<ResearcherProfile>(`/researchers/${userId}`);
  return data;
}

export async function follow(userId: string): Promise<void> {
  await api.post(`/researchers/${userId}/follow`);
}

export async function unfollow(userId: string): Promise<void> {
  await api.delete(`/researchers/${userId}/follow`);
}

export async function getFollowingFeed(): Promise<ReportSummary[]> {
  const { data } = await api.get<ReportSummary[]>("/me/feed");
  return data;
}

export async function getReferral(): Promise<Referral> {
  const { data } = await api.get<Referral>("/me/referral");
  return data;
}

// ---- leaderboards ----
export async function getLeaderboard(kind: LeaderboardKind): Promise<LeaderRow[]> {
  const { data } = await api.get<LeaderRow[]>(`/leaderboards/${kind}`);
  return data;
}

// ---- challenges ----
export async function listChallenges(): Promise<ChallengeOut[]> {
  const { data } = await api.get<ChallengeOut[]>("/challenges");
  return data;
}

export async function enrollChallenge(code: string): Promise<ChallengeProgress> {
  const { data } = await api.post<ChallengeProgress>(`/challenges/${code}/enroll`);
  return data;
}

export async function challengeProgress(code: string): Promise<ChallengeProgress> {
  const { data } = await api.get<ChallengeProgress>(`/challenges/${code}/progress`);
  return data;
}

export async function getCertificate(code: string): Promise<Certificate> {
  const { data } = await api.get<Certificate>(`/challenges/${code}/certificate`);
  return data;
}

// ---- events (埋点, 允许匿名) ----
export async function trackEvent(
  event: string,
  props: Record<string, unknown> = {},
): Promise<void> {
  try {
    await api.post("/events", { event, props });
  } catch {
    // 埋点失败不影响主流程
  }
}
