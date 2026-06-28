import { api } from "./client";
import type {
  Backtest,
  Certificate,
  ChallengeOut,
  ChallengeProgress,
  Factor,
  Graph,
  LeaderRow,
  LeaderboardKind,
  Mentor,
  NextStep,
  Project,
  Referral,
  ReportDetail,
  ReportSummary,
  ResearcherProfile,
  ShareCardPublic,
  ShareOut,
  Template,
  Token,
  User,
  UserType,
  Validation,
} from "./types";

// ---- auth ----
export async function register(body: {
  email: string;
  username: string;
  password: string;
  user_type?: UserType;
  ref?: string | null;
}): Promise<User> {
  const { data } = await api.post<User>("/auth/register", body);
  return data;
}

export async function login(body: {
  identifier: string;
  password: string;
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

export async function publishProject(id: string): Promise<Project> {
  const { data } = await api.post<Project>(`/projects/${id}/publish`);
  return data;
}

// ---- factors ----
export async function listFactors(): Promise<Factor[]> {
  const { data } = await api.get<Factor[]>("/factors");
  return data;
}

// ---- backtest / validation ----
export async function createBacktest(body: {
  factor_id: string;
  symbol: string;
}): Promise<Backtest> {
  const { data } = await api.post<Backtest>("/backtests", body);
  return data;
}

export async function createValidation(body: {
  factor_id: string;
  symbol: string;
}): Promise<Validation> {
  const { data } = await api.post<Validation>("/validations", body);
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

export async function shareReport(id: string): Promise<ShareOut> {
  const { data } = await api.post<ShareOut>(`/research/reports/${id}/share`);
  return data;
}

export async function getShareCard(token: string): Promise<ShareCardPublic> {
  const { data } = await api.get<ShareCardPublic>(`/share/${token}`);
  return data;
}

export async function getFeed(): Promise<ReportSummary[]> {
  const { data } = await api.get<ReportSummary[]>("/research/feed");
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
