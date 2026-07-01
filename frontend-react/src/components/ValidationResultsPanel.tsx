import { useQuery } from "@tanstack/react-query";
import { getValidation, listValidations } from "../api/endpoints";
import { useLocale } from "../store/locale";
import { GradeBadge, Spinner } from "./ui";

type Props = {
  factorId: string | null;
  enabled: boolean;
};

export default function ValidationResultsPanel({ factorId, enabled }: Props) {
  const v = useLocale((s) => s.dict.validationPanel);

  const list = useQuery({
    queryKey: ["validations"],
    queryFn: listValidations,
    enabled: enabled && Boolean(factorId),
  });

  const latestId =
    list.data
      ?.filter((x) => x.factor_id === factorId && x.status === "success")
      .sort((a, b) => b.created_at.localeCompare(a.created_at))[0]?.id ?? null;

  const detail = useQuery({
    queryKey: ["validation", latestId],
    queryFn: () => getValidation(latestId!),
    enabled: Boolean(latestId),
  });

  if (!enabled || !factorId) return null;
  if (list.isLoading) return <Spinner />;
  if (!latestId) {
    return (
      <div className="card border-amber-200 bg-amber-50/40 dark:border-amber-900 dark:bg-amber-950/20">
        <p className="text-sm text-amber-800 dark:text-amber-200">{v.empty}</p>
      </div>
    );
  }
  if (detail.isLoading) return <Spinner />;
  if (!detail.data) return null;

  const d = detail.data;
  const oos = d.oos as Record<string, unknown> | null;
  const isSharpe = (oos?.in_sample as { sharpe?: number } | undefined)?.sharpe;
  const oosSharpe = (oos?.out_of_sample as { sharpe?: number } | undefined)?.sharpe;
  const degradation = oos?.sharpe_degradation as number | null | undefined;
  const wf = d.walk_forward as { folds?: unknown[]; summary?: Record<string, number | null> } | null;
  const rob = d.robustness as {
    score?: number;
    grade?: string;
    notes?: string[];
    sealed_holdout?: { metrics?: { sharpe?: number }; skipped?: boolean };
  } | null;
  const sealedSharpe = rob?.sealed_holdout?.skipped
    ? null
    : rob?.sealed_holdout?.metrics?.sharpe;

  return (
    <div className="card">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-slate-800 dark:text-slate-100">{v.title}</h3>
        {rob?.grade && <GradeBadge grade={rob.grade} />}
      </div>
      <p className="mb-4 text-sm text-slate-500">{v.subtitle}</p>

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label={v.isSharpe} value={fmtSharpe(isSharpe)} />
        <Metric label={v.oosSharpe} value={fmtSharpe(oosSharpe)} highlight={oosSharpe != null && oosSharpe <= 0} />
        <Metric label={v.degradation} value={degradation != null ? degradation.toFixed(2) : "—"} />
        <Metric
          label={v.robustness}
          value={rob?.score != null ? `${rob.score}/100` : "—"}
        />
      </div>

      {wf?.summary && (
        <p className="mb-3 text-sm text-slate-600 dark:text-slate-300">
          {v.wfSummary(
            wf.folds?.length ?? 0,
            Math.round((wf.summary.positive_ratio ?? 0) * 100),
          )}
        </p>
      )}

      {sealedSharpe != null && (
        <p className="mb-3 text-sm text-slate-600 dark:text-slate-300">
          {v.sealedHoldout(sealedSharpe.toFixed(2))}
        </p>
      )}

      {rob?.notes && rob.notes.length > 0 && (
        <ul className="list-inside list-disc space-y-1 text-sm text-slate-600 dark:text-slate-300">
          {rob.notes.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Metric({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-lg border px-3 py-2 ${
        highlight
          ? "border-rose-200 bg-rose-50/60 dark:border-rose-900 dark:bg-rose-950/30"
          : "border-slate-200 bg-slate-50/50 dark:border-slate-700 dark:bg-slate-900/40"
      }`}
    >
      <p className="text-xs text-slate-500">{label}</p>
      <p className="text-lg font-semibold text-slate-800 dark:text-slate-100">{value}</p>
    </div>
  );
}

function fmtSharpe(v: number | null | undefined): string {
  if (v == null) return "—";
  return v.toFixed(2);
}
