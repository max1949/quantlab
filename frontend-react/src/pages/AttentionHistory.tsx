import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getAttentionAlertHistory,
  restoreAttentionAlert,
} from "../api/endpoints";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { PageTitle, Spinner } from "../components/ui";

export default function AttentionHistory() {
  const t = useLocale((s) => s.dict.attentionHistory);
  const notify = useUi((s) => s.notify);
  const qc = useQueryClient();

  const history = useQuery({
    queryKey: ["attention-alert-history"],
    queryFn: getAttentionAlertHistory,
  });

  const restore = useMutation({
    mutationFn: restoreAttentionAlert,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: ["attention-alert-history"] });
      void qc.invalidateQueries({ queryKey: ["research-journey"] });
      void qc.invalidateQueries({ queryKey: ["mentor"] });
      notify(t.restoreDone, "success");
    },
  });

  const items = history.data?.items ?? [];
  const cooldown = history.data?.cooldown_days ?? 7;

  return (
    <div>
      <PageTitle title={t.title} subtitle={t.subtitle(cooldown)} />

      <p className="mb-4 text-sm text-slate-500">
        <Link to="/app" className="text-brand-600 hover:underline">
          {t.backWorkspace}
        </Link>
      </p>

      {history.isLoading ? (
        <Spinner />
      ) : items.length === 0 ? (
        <div className="card py-10 text-center text-sm text-slate-500">{t.empty}</div>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.alert_key} className="card">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="font-medium text-slate-800 dark:text-slate-100">
                    {item.kind_label}
                    {item.ref_label ? ` · ${item.ref_label}` : ""}
                  </p>
                  <p className="mt-1 text-xs text-slate-500">
                    {t.dismissedAt(new Date(item.dismissed_at).toLocaleString())}
                  </p>
                  <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">
                    {item.days_remaining > 0
                      ? t.expiresIn(item.days_remaining)
                      : t.expiresSoon}
                  </p>
                </div>
                <button
                  type="button"
                  className="btn shrink-0 text-xs"
                  disabled={restore.isPending}
                  onClick={() => restore.mutate(item.alert_key)}
                >
                  {t.restore}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
