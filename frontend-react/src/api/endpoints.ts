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
  ExecutionConfig,
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
  PaperMasteryMeta,
  Plan,
  SubscriptionStatus,
  LeaderboardKind,
  Mentor,
  NextStep,
  OrgCatalog,
  OrgBilling,
  OrgBillingLedgerEntry,
  OrgFactorShare,
  OrgInvite,
  OrgInvitePreview,
  OrgMember,
  OrthogonalizeResult,
  ResearchOrg,
  OverfitCheck,
  PaperSimulate,
  PaperOrder,
  PaperOrderEvent,
  OrgPaperOrder,
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
  TemplateRegimePicks,
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

export async function getSsoConfig(): Promise<{ enabled: boolean }> {
  const { data } = await api.get<{ enabled: boolean }>("/auth/sso/config");
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

export async function getResearchJourney(opts?: {
  checkoutPlan?: string;
}): Promise<ResearchJourney> {
  const { data } = await api.get<ResearchJourney>("/onboarding/journey", {
    params: opts?.checkoutPlan ? { checkout_plan: opts.checkoutPlan } : undefined,
  });
  return data;
}

export async function dismissAttentionAlert(alert_key: string): Promise<{
  alert_key: string;
  cooldown_days: number;
  dismissed_at: string;
}> {
  const { data } = await api.post("/onboarding/attention-alerts/dismiss", { alert_key });
  return data;
}

export async function getAttentionAlertHistory(): Promise<{
  cooldown_days: number;
  items: Array<{
    alert_key: string;
    kind: string;
    kind_label: string;
    ref_label: string | null;
    dismissed_at: string;
    expires_at: string;
    days_remaining: number;
  }>;
}> {
  const { data } = await api.get("/onboarding/attention-alerts/history");
  return data;
}

export async function restoreAttentionAlert(alert_key: string): Promise<{
  alert_key: string;
  restored: boolean;
}> {
  const { data } = await api.post("/onboarding/attention-alerts/restore", { alert_key });
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

export async function getTemplateRegimePicks(symbol = "RB"): Promise<TemplateRegimePicks> {
  const { data } = await api.get<TemplateRegimePicks>("/research/templates/regime-picks", {
    params: { symbol },
  });
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
  paper_ready?: boolean;
  paper_reasons?: string[];
  paper_scorecard?: Record<string, number | string | null>;
  paper_thresholds?: Record<string, number | string | null>;
  factor_id?: string | null;
  symbol?: string | null;
  regime?: Record<string, unknown> | null;
  mastery?: {
    stage: string;
    stage_index: number;
    total_stages: number;
    next_action: string;
    progress_pct: number;
    decay_attention?: boolean;
    decay_status?: string | null;
  };
  paper_decay?: {
    status: string;
    reasons: string[];
    baseline_sharpe?: number | null;
    paper_sharpe?: number | null;
  } | null;
  coaching_tips?: Array<{ title: string; tip: string; action: string }>;
  attention_coaching?: Array<{ title: string; tip: string; action: string }>;
  feed_preview?: {
    publish_ready: boolean;
    paper_graduated: boolean;
    paper_tracking: boolean;
  };
  academy_milestones?: Array<{
    code: string;
    title: string;
    mastery_stage: string;
    xp_reward: number;
    completed: boolean;
  }>;
  academy_stage_tasks?: Array<{
    code: string;
    title: string;
    mastery_stage: string;
    xp_reward: number;
    completed: boolean;
  }>;
  academy_next_tasks?: Array<{
    code: string;
    title: string;
    mastery_stage: string;
    xp_reward: number;
    completed: boolean;
  }>;
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
  pay_url?: string | null;
  org_id?: string | null;
}> {
  const { data } = await api.post("/billing/checkout", { plan_code });
  return data;
}

export async function getBillingHistory(limit = 20): Promise<OrgBillingLedgerEntry[]> {
  const { data } = await api.get<OrgBillingLedgerEntry[]>("/billing/history", { params: { limit } });
  return data;
}

export async function downloadBillingHistoryCsv(): Promise<void> {
  const { data } = await api.get<Blob>("/billing/history/export", { responseType: "blob" });
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = "billing-history.csv";
  a.click();
  URL.revokeObjectURL(url);
}

function downloadBlob(data: Blob, filename: string): void {
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export async function downloadBillingInvoicePdf(ledgerId: string): Promise<void> {
  const { data } = await api.get<Blob>(`/billing/history/${ledgerId}/invoice.pdf`, {
    responseType: "blob",
  });
  downloadBlob(data, `billing-${ledgerId}.pdf`);
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

export async function getVolRegime(
  symbol: string,
  timeframe: string,
  factorId?: string,
): Promise<VolRegime> {
  const { data } = await api.get<VolRegime>("/datasets/regime", {
    params: { symbol, timeframe, factor_id: factorId },
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

export async function getPublicFeed(
  sort: "latest" | "top" = "top",
  graduatedOnly = false,
): Promise<ReportSummary[]> {
  const { data } = await api.get<ReportSummary[]>("/public/feed", {
    params: { sort, graduated_only: graduatedOnly || undefined },
  });
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
  mastery_stage?: string | null;
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

export async function getPaperMasteryMeta(): Promise<PaperMasteryMeta> {
  const { data } = await api.get<PaperMasteryMeta>("/leaderboards/meta/paper-mastery");
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

// ---- organizations (institutional) ----
export async function listOrgs(): Promise<ResearchOrg[]> {
  const { data } = await api.get<ResearchOrg[]>("/orgs");
  return data;
}

export async function createOrg(name: string): Promise<ResearchOrg> {
  const { data } = await api.post<ResearchOrg>("/orgs", { name });
  return data;
}

export async function getOrg(orgId: string): Promise<ResearchOrg> {
  const { data } = await api.get<ResearchOrg>(`/orgs/${orgId}`);
  return data;
}

export async function listOrgMembers(orgId: string): Promise<OrgMember[]> {
  const { data } = await api.get<OrgMember[]>(`/orgs/${orgId}/members`);
  return data;
}

export async function addOrgMember(
  orgId: string,
  body: { username: string; role: string },
): Promise<OrgMember> {
  const { data } = await api.post<OrgMember>(`/orgs/${orgId}/members`, body);
  return data;
}

export async function updateOrgMemberRole(
  orgId: string,
  userId: string,
  role: string,
): Promise<OrgMember> {
  const { data } = await api.patch<OrgMember>(`/orgs/${orgId}/members/${userId}`, { role });
  return data;
}

export async function removeOrgMember(orgId: string, userId: string): Promise<void> {
  await api.delete(`/orgs/${orgId}/members/${userId}`);
}

export async function listOrgInvites(orgId: string): Promise<OrgInvite[]> {
  const { data } = await api.get<OrgInvite[]>(`/orgs/${orgId}/invites`);
  return data;
}

export async function revokeOrgInvite(orgId: string, inviteId: string): Promise<void> {
  await api.delete(`/orgs/${orgId}/invites/${inviteId}`);
}

export interface OrgActivity {
  id: string;
  action: string;
  actor_id: string | null;
  resource_type: string;
  resource_id: string;
  detail: Record<string, unknown>;
  created_at: string;
}

export async function getOrgActivity(orgId: string, limit = 50): Promise<OrgActivity[]> {
  const { data } = await api.get<OrgActivity[]>(`/orgs/${orgId}/activity`, {
    params: { limit },
  });
  return data;
}

export async function createOrgInvite(
  orgId: string,
  body: { role?: string; expires_in_days?: number; max_uses?: number },
): Promise<OrgInvite> {
  const { data } = await api.post<OrgInvite>(`/orgs/${orgId}/invites`, body);
  return data;
}

export async function previewOrgInvite(token: string): Promise<OrgInvitePreview> {
  const { data } = await api.get<OrgInvitePreview>(`/orgs/invites/${token}`);
  return data;
}

export async function acceptOrgInvite(token: string): Promise<ResearchOrg> {
  const { data } = await api.post<ResearchOrg>(`/orgs/invites/${token}/accept`);
  return data;
}

export async function listOrgFactors(orgId: string): Promise<OrgFactorShare[]> {
  const { data } = await api.get<OrgFactorShare[]>(`/orgs/${orgId}/factors`);
  return data;
}

export async function shareFactorToOrg(
  orgId: string,
  factorId: string,
  note = "",
): Promise<OrgFactorShare> {
  const { data } = await api.post<OrgFactorShare>(
    `/orgs/${orgId}/factors/${factorId}/share`,
    { note },
  );
  return data;
}

export async function getOrgCatalog(
  orgId: string,
  params?: { symbol?: string; timeframe?: string },
): Promise<OrgCatalog> {
  const { data } = await api.get<OrgCatalog>(`/orgs/${orgId}/catalog`, { params });
  return data;
}

export async function getOrgBilling(orgId: string): Promise<OrgBilling> {
  const { data } = await api.get<OrgBilling>(`/orgs/${orgId}/billing`);
  return data;
}

export interface OrgBillingProfile {
  company_name: string;
  tax_id: string;
  address: string;
  configured: boolean;
}

export async function getOrgBillingProfile(orgId: string): Promise<OrgBillingProfile> {
  const { data } = await api.get<OrgBillingProfile>(`/orgs/${orgId}/billing/profile`);
  return data;
}

export async function setOrgBillingProfile(
  orgId: string,
  profile: { company_name: string; tax_id: string; address: string },
): Promise<OrgBillingProfile> {
  const { data } = await api.put<OrgBillingProfile>(`/orgs/${orgId}/billing/profile`, profile);
  return data;
}

export async function getOrgBillingHistory(orgId: string, limit = 20): Promise<OrgBillingLedgerEntry[]> {
  const { data } = await api.get<OrgBillingLedgerEntry[]>(`/orgs/${orgId}/billing/history`, {
    params: { limit },
  });
  return data;
}

export async function downloadOrgBillingHistoryCsv(orgId: string): Promise<void> {
  const { data } = await api.get<Blob>(`/orgs/${orgId}/billing/history/export`, {
    responseType: "blob",
  });
  const url = URL.createObjectURL(data);
  const a = document.createElement("a");
  a.href = url;
  a.download = `org-${orgId}-billing.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

export async function downloadOrgBillingInvoicePdf(orgId: string, ledgerId: string): Promise<void> {
  const { data } = await api.get<Blob>(`/orgs/${orgId}/billing/history/${ledgerId}/invoice.pdf`, {
    responseType: "blob",
  });
  downloadBlob(data, `org-${orgId}-billing-${ledgerId}.pdf`);
}

export async function orgBillingCheckout(
  orgId: string,
  plan_code: string,
): Promise<{
  configured: boolean;
  plan_code: string;
  plan_name: string;
  price_cny: number;
  message: string;
  pay_url?: string | null;
}> {
  const { data } = await api.post(`/orgs/${orgId}/billing/checkout`, { plan_code });
  return data;
}

export async function orgBillingRedeem(
  orgId: string,
  code: string,
): Promise<{
  ok: boolean;
  tier: number;
  tier_name: string;
  expires_at: string | null;
  seats: number;
  message: string;
}> {
  const { data } = await api.post(`/orgs/${orgId}/billing/redeem`, { code });
  return data;
}

export async function getOrgSsoDomains(orgId: string): Promise<{ domains: string[] }> {
  const { data } = await api.get(`/orgs/${orgId}/sso-domains`);
  return data;
}

export async function setOrgSsoDomains(orgId: string, domains: string[]): Promise<{ domains: string[] }> {
  const { data } = await api.put(`/orgs/${orgId}/sso-domains`, { domains });
  return data;
}

// ---- execution (institutional paper / vn.py / QMT) ----
export async function getExecutionConfig(): Promise<ExecutionConfig> {
  const { data } = await api.get<ExecutionConfig>("/execution/config");
  return data;
}

export async function checkExecutionRisk(body: {
  symbol: string;
  notional_cny: number;
  channel?: string;
  factor_id?: string;
  acknowledge_risk?: boolean;
}): Promise<{ allowed: boolean; message: string; channel: string; regime?: VolRegime; risk: Record<string, string> }> {
  const { data } = await api.post("/execution/risk-check", body);
  return data;
}

export async function submitPaperOrder(body: {
  symbol: string;
  side: string;
  notional_cny: number;
  channel?: string;
  factor_id?: string;
  signal_value?: number;
  note?: string;
  acknowledge_risk?: boolean;
}): Promise<PaperOrder> {
  const { data } = await api.post<PaperOrder>("/execution/paper/orders", body);
  return data;
}

export async function listPaperOrders(limit = 20): Promise<PaperOrder[]> {
  const { data } = await api.get<PaperOrder[]>("/execution/paper/orders", { params: { limit } });
  return data;
}

export async function listPaperOrderEvents(orderId: string): Promise<PaperOrderEvent[]> {
  const { data } = await api.get<PaperOrderEvent[]>(`/execution/paper/orders/${orderId}/events`);
  return data;
}

export async function listOrgExecutionOrders(orgId: string, limit = 20): Promise<OrgPaperOrder[]> {
  const { data } = await api.get<OrgPaperOrder[]>(`/orgs/${orgId}/execution/orders`, { params: { limit } });
  return data;
}

export async function refreshPaperOrder(orderId: string): Promise<PaperOrder> {
  const { data } = await api.post<PaperOrder>(`/execution/paper/orders/${orderId}/refresh`);
  return data;
}

export async function refreshOrgExecutionOrders(orgId: string): Promise<{ checked: number; updated: number }> {
  const { data } = await api.post(`/orgs/${orgId}/execution/refresh`);
  return data;
}

export interface OrgExecutionCompliance {
  generated_at: string;
  scope: string;
  kill_switch: boolean;
  sla_stale_minutes: number;
  order_summary: Record<string, number>;
  stale_orders: Array<Record<string, unknown>>;
  sla_alerts: Array<{
    code: string;
    severity: string;
    message: string;
    channel?: string;
    order_id?: string;
    age_minutes?: number;
  }>;
  alert_count: number;
}

export async function fetchOrgExecutionCompliance(orgId: string): Promise<OrgExecutionCompliance> {
  const { data } = await api.get<OrgExecutionCompliance>(`/orgs/${orgId}/execution/compliance`);
  return data;
}

export interface OrgTeamAttentionItem {
  user_id: string;
  username: string;
  role: string;
  alert_key: string;
  kind: string;
  kind_label: string;
  title: string;
  message: string;
  severity: string;
  symbol: string | null;
  project_id: string | null;
  cta_path: string;
}

export interface OrgTeamAttentionRollup {
  member_count: number;
  members_with_alerts: number;
  total_alerts: number;
  summary: string;
  items: OrgTeamAttentionItem[];
}

export async function fetchOrgTeamAttentionRollup(orgId: string): Promise<OrgTeamAttentionRollup> {
  const { data } = await api.get<OrgTeamAttentionRollup>(`/orgs/${orgId}/research/attention-alerts`);
  return data;
}

export async function getOrgAlertWebhook(
  orgId: string,
): Promise<{ webhook_url: string; secret_configured: boolean }> {
  const { data } = await api.get<{ webhook_url: string; secret_configured: boolean }>(
    `/orgs/${orgId}/execution/alert-webhook`,
  );
  return data;
}

export async function setOrgAlertWebhook(
  orgId: string,
  webhookUrl: string,
  webhookSecret?: string,
): Promise<{ webhook_url: string; secret_configured: boolean }> {
  const { data } = await api.put<{ webhook_url: string; secret_configured: boolean }>(
    `/orgs/${orgId}/execution/alert-webhook`,
    {
      webhook_url: webhookUrl,
      webhook_secret: webhookSecret || undefined,
    },
  );
  return data;
}

export async function dispatchOrgSlaAlerts(
  orgId: string,
  force = false,
): Promise<{ sent: number; skipped: boolean; reason?: string }> {
  const { data } = await api.post(`/orgs/${orgId}/execution/alerts/dispatch`, null, {
    params: { force },
  });
  return data;
}

export interface OrgSlaAlertDelivery {
  id: string;
  scope: string;
  org_id: string | null;
  status: string;
  trigger: string;
  alert_count: number;
  skipped_reason: string | null;
  http_status: number | null;
  error_message: string | null;
  webhook_url: string;
  signed: boolean;
  created_at: string;
}

export async function fetchOrgAlertDeliveries(
  orgId: string,
  limit = 20,
): Promise<OrgSlaAlertDelivery[]> {
  const { data } = await api.get<OrgSlaAlertDelivery[]>(
    `/orgs/${orgId}/execution/alert-deliveries`,
    { params: { limit } },
  );
  return data;
}

export async function retryOrgFailedAlertDeliveries(orgId: string): Promise<{ retried: number }> {
  const { data } = await api.post<{ retried: number }>(
    `/orgs/${orgId}/execution/alert-deliveries/retry`,
  );
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
