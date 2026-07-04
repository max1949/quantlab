import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import { useLocale } from "../store/locale";
import type { AttentionAlert } from "../api/types";

const SEVERITY_STYLES: Record<string, string> = {
  alert:
    "border-rose-200 bg-rose-50/70 dark:border-rose-900 dark:bg-rose-950/30",
  watch:
    "border-amber-200 bg-amber-50/70 dark:border-amber-900 dark:bg-amber-950/30",
  info: "border-sky-200 bg-sky-50/70 dark:border-sky-900 dark:bg-sky-950/30",
};

function AlertRow({ alert }: { alert: AttentionAlert }) {
  const d = useLocale((s) => s.dict.attentionAlerts);
  const style = SEVERITY_STYLES[alert.severity] ?? SEVERITY_STYLES.info;
  const cta =
    alert.action === "templates"
      ? d.ctaTemplates
      : alert.action === "revalidate"
        ? d.ctaRevalidate
        : d.ctaProject;

  return (
    <li className={`rounded-lg border px-3 py-2.5 text-sm ${style}`}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-medium text-slate-800 dark:text-slate-100">
            {d.severityBadge(alert.severity)} {alert.title}
          </p>
          <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">{alert.message}</p>
        </div>
        <Link
          to={alert.cta_path}
          className="btn shrink-0 whitespace-nowrap text-xs"
        >
          {cta}
        </Link>
      </div>
    </li>
  );
}

export default function AttentionAlertsPanel() {
  const d = useLocale((s) => s.dict.attentionAlerts);
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: getResearchJourney });

  const alerts = journey.data?.attention_alerts ?? [];
  if (!journey.isLoading && alerts.length === 0) return null;

  return (
    <div className="card border border-amber-100 bg-gradient-to-r from-amber-50/40 to-white dark:border-amber-900 dark:from-amber-950/20 dark:to-slate-900">
      <div className="mb-3">
        <h3 className="font-semibold text-slate-800 dark:text-slate-100">{d.title}</h3>
        <p className="text-xs text-slate-500">{d.subtitle}</p>
      </div>
      {journey.isLoading ? (
        <p className="text-sm text-slate-400">{d.loading}</p>
      ) : (
        <ul className="space-y-2">
          {alerts.map((a) => (
            <AlertRow key={`${a.kind}-${a.project_id ?? a.symbol ?? a.title}`} alert={a} />
          ))}
        </ul>
      )}
    </div>
  );
}
