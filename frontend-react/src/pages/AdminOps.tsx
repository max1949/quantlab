import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  fetchOpsAudit,
  fetchOpsExecutionCompliance,
  dispatchSlaAlerts,
  fetchOpsHealth,
  fetchOpsMetrics,
  isAdminForbidden,
  syncOpsExecutionOrders,
} from "../api/adminOps";
import { apiErrorMessage } from "../api/client";
import { getAdminKey, setAdminKey } from "../lib/adminKey";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { ErrorBox, PageTitle, Spinner, Stat } from "../components/ui";

export default function AdminOps() {
  const a = useLocale((s) => s.dict.adminOps);
  const notify = useUi((s) => s.notify);
  const [keyInput, setKeyInput] = useState(getAdminKey() ?? "");
  const [unlocked, setUnlocked] = useState(Boolean(getAdminKey()));
  const [auditFilter, setAuditFilter] = useState("");
  const qc = useQueryClient();

  const metrics = useQuery({
    queryKey: ["admin-ops-metrics"],
    queryFn: () => fetchOpsMetrics(true),
    enabled: unlocked,
    retry: false,
  });

  const health = useQuery({
    queryKey: ["admin-ops-health"],
    queryFn: fetchOpsHealth,
    enabled: unlocked,
    retry: false,
  });

  const audit = useQuery({
    queryKey: ["admin-ops-audit", auditFilter],
    queryFn: () => fetchOpsAudit(80, auditFilter || undefined),
    enabled: unlocked,
    retry: false,
  });

  const compliance = useQuery({
    queryKey: ["admin-ops-compliance"],
    queryFn: fetchOpsExecutionCompliance,
    enabled: unlocked,
    retry: false,
  });

  const authError =
    (metrics.isError && isAdminForbidden(metrics.error)) ||
    (health.isError && isAdminForbidden(health.error));

  const gatewaySync = useMutation({
    mutationFn: syncOpsExecutionOrders,
    onSuccess: (r) => {
      notify(a.gatewaySyncDone(r.updated), "success");
      void qc.invalidateQueries({ queryKey: ["admin-ops-metrics"] });
    },
    onError: (e) => notify(apiErrorMessage(e, a.gatewaySyncFail), "error"),
  });

  const slaDispatch = useMutation({
    mutationFn: () => dispatchSlaAlerts(true),
    onSuccess: (r) => {
      if (r.sent > 0) notify(a.slaDispatchDone(r.sent), "success");
      else notify(a.slaDispatchSkipped(r.reason ?? "none"), "info");
    },
    onError: (e) => notify(apiErrorMessage(e, a.slaDispatchFail), "error"),
  });

  function unlock() {
    const trimmed = keyInput.trim();
    if (!trimmed) return;
    setAdminKey(trimmed);
    setUnlocked(true);
    void qc.invalidateQueries({ queryKey: ["admin-ops-metrics"] });
    void qc.invalidateQueries({ queryKey: ["admin-ops-health"] });
    void qc.invalidateQueries({ queryKey: ["admin-ops-audit"] });
  }

  function lock() {
    setAdminKey(null);
    setUnlocked(false);
    setKeyInput("");
    qc.removeQueries({ queryKey: ["admin-ops-metrics"] });
    qc.removeQueries({ queryKey: ["admin-ops-health"] });
    qc.removeQueries({ queryKey: ["admin-ops-audit"] });
  }

  if (!unlocked || authError) {
    return (
      <div className="mx-auto max-w-md">
        <PageTitle title={a.title} subtitle={a.subtitle} />
        <div className="card">
          <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">
            {a.keyLabel}
          </label>
          <input
            type="password"
            className="input mb-3 w-full"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            placeholder={a.keyPlaceholder}
            onKeyDown={(e) => e.key === "Enter" && unlock()}
          />
          {authError && <ErrorBox message={a.keyInvalid} />}
          <button type="button" className="btn w-full" onClick={unlock}>
            {a.unlock}
          </button>
        </div>
      </div>
    );
  }

  if (metrics.isLoading || health.isLoading) return <Spinner />;

  const err = metrics.error ?? health.error ?? audit.error;
  if (err) {
    return <ErrorBox message={apiErrorMessage(err, a.loadFail)} />;
  }

  const m = metrics.data!;
  const h = health.data!;
  const funnel = m.funnel;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <PageTitle title={a.title} subtitle={a.dashboardSubtitle} />
        <button type="button" className="btn text-sm" onClick={lock}>
          {a.lock}
        </button>
      </div>

      <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label={a.registered} value={m.registered_users} />
        <Stat label={a.rcr} value={`${(m.rcr * 100).toFixed(1)}%`} />
        <Stat label={a.activeSubs} value={m.active_subscriptions} />
        <Stat label={a.published} value={m.published_projects} />
      </div>

      {m.institutional && (
        <>
          <div className="mb-6 grid gap-4 sm:grid-cols-3">
            <Stat label={a.instOrgs} value={m.institutional.total_orgs} />
            <Stat label={a.instMembers} value={m.institutional.total_org_members} />
            <Stat label={a.instSharedFactors} value={m.institutional.shared_org_factors} />
            <Stat label={a.instPaperOrders} value={m.institutional.paper_orders ?? 0} />
            <Stat label={a.instVnpyOrders} value={m.institutional.vnpy_orders ?? 0} />
            <Stat label={a.instQmtOrders} value={m.institutional.qmt_orders ?? 0} />
            <Stat label={a.instRoutedOrders} value={m.institutional.routed_gateway_orders ?? 0} />
            <Stat label={a.instSlaAlerts} value={m.institutional.execution_sla_alerts ?? 0} />
          </div>
          {m.institutional.gateway_health && (
            <div className="mb-6 card">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <h2 className="font-semibold text-slate-800 dark:text-slate-100">{a.gatewayHealthTitle}</h2>
                <button
                  type="button"
                  className="btn text-sm"
                  disabled={gatewaySync.isPending}
                  onClick={() => gatewaySync.mutate()}
                >
                  {gatewaySync.isPending ? a.gatewaySyncing : a.gatewaySync}
                </button>
              </div>
              <div className="flex flex-wrap gap-2 text-sm">
                {m.institutional.gateway_health.map((g) => (
                  <span
                    key={g.channel}
                    className="rounded-full border border-slate-200 px-3 py-1 dark:border-slate-700"
                  >
                    {g.channel}:{" "}
                    {!g.configured
                      ? a.gatewayStub
                      : g.ok
                        ? a.gatewayUp
                        : a.gatewayDown}
                  </span>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {compliance.data && (
        <div className="mb-6 card">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold text-slate-800 dark:text-slate-100">{a.complianceTitle}</h2>
            <button
              type="button"
              className="btn text-sm"
              disabled={slaDispatch.isPending}
              onClick={() => slaDispatch.mutate()}
            >
              {slaDispatch.isPending ? a.slaDispatching : a.slaDispatch}
            </button>
          </div>
          <p className="mb-3 text-sm text-slate-500">
            {compliance.data.alert_count > 0
              ? a.complianceAlerts(compliance.data.alert_count)
              : a.complianceNone}
          </p>
          {compliance.data.sla_alerts.length > 0 && (
            <ul className="mb-3 space-y-1 text-xs text-slate-600 dark:text-slate-300">
              {compliance.data.sla_alerts.slice(0, 8).map((alert, i) => (
                <li
                  key={`${alert.code}-${i}`}
                  className={
                    alert.severity === "critical"
                      ? "text-rose-600 dark:text-rose-400"
                      : "text-amber-700 dark:text-amber-300"
                  }
                >
                  [{alert.severity}] {alert.message}
                </li>
              ))}
            </ul>
          )}
          {compliance.data.stale_orders.length > 0 && (
            <p className="text-xs text-slate-500">
              {a.complianceStale}: {compliance.data.stale_orders.length}
            </p>
          )}
        </div>
      )}

      <div className="mb-6 card">
        <h2 className="mb-3 font-semibold text-slate-800 dark:text-slate-100">{a.funnelTitle}</h2>
        <div className="grid gap-2 text-sm sm:grid-cols-5">
          <FunnelStep label={a.funnelRegistered} value={funnel.registered} />
          <FunnelStep label={a.funnelProject} value={funnel.project} />
          <FunnelStep label={a.funnelBacktest} value={funnel.backtest_success} />
          <FunnelStep label={a.funnelReport} value={funnel.report} />
          <FunnelStep label={a.funnelShare} value={funnel.share} />
        </div>
      </div>

      <div className="mb-6 card">
        <h2 className="mb-3 font-semibold text-slate-800 dark:text-slate-100">{a.healthTitle}</h2>
        <div className="grid gap-3 sm:grid-cols-3">
          <HealthPill label="Database" ok={h.database.ok} detail={h.database.error} />
          <HealthPill label="Redis" ok={h.redis.ok} detail={h.redis.error} />
          <HealthPill
            label="Celery"
            ok={h.celery.ok}
            detail={
              h.celery.ok
                ? a.workers(h.celery.workers ?? 0)
                : h.celery.error
            }
          />
        </div>
        <p className="mt-2 text-xs text-slate-500">
          {a.overallStatus}: <span className="font-medium">{h.status}</span>
        </p>
      </div>

      <div className="card">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-semibold text-slate-800 dark:text-slate-100">{a.auditTitle}</h2>
          <div className="flex items-center gap-2">
            <select
              className="input text-sm"
              value={auditFilter}
              onChange={(e) => setAuditFilter(e.target.value)}
            >
              <option value="">{a.auditFilterAll}</option>
              <option value="org">{a.auditFilterOrg}</option>
              <option value="project">{a.auditFilterProject}</option>
              <option value="backtest">{a.auditFilterBacktest}</option>
            </select>
            <button
              type="button"
              className="btn text-sm"
              onClick={() => void audit.refetch()}
            >
              {a.refresh}
            </button>
          </div>
        </div>
        {audit.isLoading ? (
          <Spinner />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs text-slate-500 dark:border-slate-700">
                  <th className="py-2 pr-3">{a.auditTime}</th>
                  <th className="py-2 pr-3">{a.auditAction}</th>
                  <th className="py-2 pr-3">{a.auditResource}</th>
                  <th className="py-2">{a.auditDetail}</th>
                </tr>
              </thead>
              <tbody>
                {(audit.data ?? []).map((row) => (
                  <tr
                    key={row.id}
                    className="border-b border-slate-100 dark:border-slate-800"
                  >
                    <td className="py-2 pr-3 whitespace-nowrap text-xs text-slate-500">
                      {new Date(row.created_at).toLocaleString()}
                    </td>
                    <td className="py-2 pr-3 font-mono text-xs">{row.action}</td>
                    <td className="py-2 pr-3 text-xs">
                      {row.resource_type}
                      {row.resource_id ? ` · ${row.resource_id.slice(0, 8)}` : ""}
                    </td>
                    <td className="py-2 text-xs text-slate-600 dark:text-slate-300">
                      {summarizeDetail(row.detail)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {(audit.data ?? []).length === 0 && (
              <p className="py-4 text-sm text-slate-500">{a.auditEmpty}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function FunnelStep({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-slate-200 px-3 py-2 dark:border-slate-700">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold text-slate-800 dark:text-slate-100">{value}</p>
    </div>
  );
}

function HealthPill({
  label,
  ok,
  detail,
}: {
  label: string;
  ok: boolean;
  detail?: string;
}) {
  return (
    <div
      className={`rounded-lg border px-3 py-2 text-sm ${
        ok
          ? "border-emerald-200 bg-emerald-50/60 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100"
          : "border-rose-200 bg-rose-50/60 text-rose-900 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-100"
      }`}
    >
      <p className="font-medium">{label}</p>
      <p className="text-xs opacity-90">{ok ? "OK" : detail ?? "down"}</p>
    </div>
  );
}

function summarizeDetail(detail: Record<string, unknown>): string {
  const parts: string[] = [];
  for (const k of ["symbol", "sharpe", "title", "robustness_score"]) {
    if (k in detail && detail[k] != null) {
      parts.push(`${k}=${String(detail[k])}`);
    }
  }
  return parts.length > 0 ? parts.join(" · ") : "—";
}
