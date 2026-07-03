import axios from "axios";
import { getAdminKey } from "../lib/adminKey";

const adminApi = axios.create({
  baseURL: "/api/v1/admin/ops",
  timeout: 30000,
});

adminApi.interceptors.request.use((config) => {
  const key = getAdminKey();
  if (key) {
    config.headers = config.headers ?? {};
    config.headers["X-Admin-Key"] = key;
  }
  return config;
});

export interface OpsMetrics {
  registered_users: number;
  test_accounts_excluded: number;
  rcr: number;
  rcr_users: number;
  activation: number;
  share_rate: number;
  funnel: {
    registered: number;
    project: number;
    backtest_success: number;
    report: number;
    share: number;
  };
  event_counts: Record<string, number>;
  active_subscriptions: number;
  published_projects: number;
  public_reports: number;
  retention_day7: number | null;
  retention_note: string;
  institutional?: {
    total_orgs: number;
    total_org_members: number;
    shared_org_factors: number;
    paper_orders?: number;
    vnpy_orders?: number;
    qmt_orders?: number;
  };
}

export interface OpsHealth {
  status: string;
  database: { ok: boolean; error?: string };
  redis: { ok: boolean; error?: string };
  celery: { ok: boolean; error?: string; workers?: number };
}

export interface AuditEventRow {
  id: string;
  actor_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  detail: Record<string, unknown>;
  ip: string | null;
  created_at: string;
}

export async function fetchOpsMetrics(excludeTest = true): Promise<OpsMetrics> {
  const { data } = await adminApi.get<OpsMetrics>("/metrics", {
    params: { exclude_test: excludeTest },
  });
  return data;
}

export async function fetchOpsHealth(): Promise<OpsHealth> {
  const { data } = await adminApi.get<OpsHealth>("/health");
  return data;
}

export async function fetchOpsAudit(limit = 50, actionPrefix?: string): Promise<AuditEventRow[]> {
  const { data } = await adminApi.get<AuditEventRow[]>("/audit", {
    params: { limit, action_prefix: actionPrefix || undefined },
  });
  return data;
}

export function isAdminForbidden(err: unknown): boolean {
  return axios.isAxiosError(err) && err.response?.status === 403;
}
