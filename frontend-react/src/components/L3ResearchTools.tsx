import { Link } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  getEntitlements,
  runOrthogonalize,
  runOverfitCheck,
  runRobustnessTest,
  trackEvent,
} from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import type { Dictionary } from "../i18n/dictionaries";
import type { Factor, FeatureState, OrthogonalizeResult, OverfitCheck, RobustnessTest } from "../api/types";

export default function L3ResearchTools({
  projectId,
  factors,
  selectedFactorId,
  symbol,
}: {
  projectId: string;
  factors: Factor[];
  selectedFactorId: string | null;
  symbol: string;
}) {
  const notify = useUi((s) => s.notify);
  const l3 = useLocale((s) => s.dict.l3Tools);
  const lk = useLocale((s) => s.dict.locked);
  const c = useLocale((s) => s.dict.common);
  const ent = useQuery({ queryKey: ["entitlements"], queryFn: getEntitlements });
  const orthFeat = ent.data?.features.find((f) => f.key === "factor_orthogonalize");
  const robustFeat = ent.data?.features.find((f) => f.key === "robustness_test");
  const overfitFeat = ent.data?.features.find((f) => f.key === "overfit_check");

  const controls = factors.filter((f) => f.id !== selectedFactorId).slice(0, 5);

  const orth = useMutation({
    mutationFn: () =>
      runOrthogonalize({
        target_factor_id: selectedFactorId!,
        control_factor_ids: controls.map((f) => f.id),
        symbol,
      }),
    onSuccess: () => {
      void trackEvent("orthogonalize_run", { project: projectId });
      notify(l3.orthDone, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, l3.orthFail), "error"),
  });

  const robust = useMutation({
    mutationFn: () => runRobustnessTest({ factor_id: selectedFactorId!, symbol }),
    onSuccess: () => {
      void trackEvent("robustness_run", { project: projectId });
      notify(l3.robustDone, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, l3.robustFail), "error"),
  });

  const overfit = useMutation({
    mutationFn: () => runOverfitCheck({ factor_id: selectedFactorId!, symbol }),
    onSuccess: () => {
      void trackEvent("overfit_check_run", { project: projectId });
      notify(l3.overfitDone, "success");
    },
    onError: (e) => notify(apiErrorMessage(e, l3.overfitFail), "error"),
  });

  return (
    <div className="card">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold">{l3.title}</h3>
          <p className="text-sm text-slate-500">{l3.subtitle}</p>
        </div>
        <span className="badge">{l3.badge}</span>
      </div>

      {!selectedFactorId ? (
        <p className="text-sm text-slate-400">{l3.needFactor}</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <ToolBox
            title={l3.orthTitle}
            desc={l3.orthDesc}
            feat={orthFeat}
            disabled={controls.length < 1}
            disabledText={l3.orthNeedTwo}
            running={orth.isPending}
            button={l3.orthBtn}
            onRun={() => orth.mutate()}
            lk={lk}
            c={c}
          >
            {orth.data && <OrthResult data={orth.data} l3={l3} />}
          </ToolBox>

          <ToolBox
            title={l3.robustTitle}
            desc={l3.robustDesc}
            feat={robustFeat}
            running={robust.isPending}
            button={l3.robustBtn}
            onRun={() => robust.mutate()}
            lk={lk}
            c={c}
          >
            {robust.data && <RobustResult data={robust.data} l3={l3} />}
          </ToolBox>

          <ToolBox
            title={l3.overfitTitle}
            desc={l3.overfitDesc}
            feat={overfitFeat}
            running={overfit.isPending}
            button={l3.overfitBtn}
            onRun={() => overfit.mutate()}
            lk={lk}
            c={c}
          >
            {overfit.data && <OverfitResult data={overfit.data} l3={l3} />}
          </ToolBox>
        </div>
      )}
    </div>
  );
}

function ToolBox({
  title,
  desc,
  feat,
  running,
  button,
  onRun,
  children,
  disabled = false,
  disabledText,
  lk,
  c,
}: {
  title: string;
  desc: string;
  feat?: FeatureState;
  running: boolean;
  button: string;
  onRun: () => void;
  children: React.ReactNode;
  disabled?: boolean;
  disabledText?: string;
  lk: Dictionary["locked"];
  c: Dictionary["common"];
}) {
  const locked = feat && !feat.allowed;
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <h4 className="font-medium text-slate-800">
        {title} {locked && "🔒"}
      </h4>
      <p className="mb-3 text-sm text-slate-500">{desc}</p>
      {locked ? (
        <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
          <p className="mb-2">{lk.needLevelTier(feat.min_level_name, feat.min_tier_name)}</p>
          <Link to="/pricing" className="btn-primary inline-block">
            {c.upgradePlans}
          </Link>
        </div>
      ) : disabled ? (
        <p className="text-sm text-slate-400">{disabledText}</p>
      ) : (
        <>
          <button className="btn-primary" disabled={running} onClick={onRun}>
            {running ? lk.running : button}
          </button>
          {children}
        </>
      )}
    </div>
  );
}

function OrthResult({ data, l3 }: { data: OrthogonalizeResult; l3: Dictionary["l3Tools"] }) {
  const result = data.result as { r2?: number; unique_ratio?: number; verdict?: string };
  return (
    <div className="mt-4 space-y-2 text-sm">
      <MiniStat label={l3.r2} value={fmtPct(result.r2)} />
      <MiniStat label={l3.uniqueRatio} value={fmtPct(result.unique_ratio)} />
      <p className="rounded-lg bg-white p-2 text-xs text-slate-600">{result.verdict}</p>
    </div>
  );
}

function RobustResult({ data, l3 }: { data: RobustnessTest; l3: Dictionary["l3Tools"] }) {
  const verdict = data.verdict as {
    grade?: string;
    positive_ratio?: number;
    peakiness?: number;
    notes?: string[];
  };
  return (
    <div className="mt-4 space-y-2 text-sm">
      <MiniStat label={l3.grade} value={verdict.grade ?? "—"} />
      <MiniStat label={l3.positiveRatio} value={fmtPct(verdict.positive_ratio)} />
      <MiniStat label={l3.peakiness} value={fmtNum(verdict.peakiness)} />
      <Notes notes={verdict.notes} />
    </div>
  );
}

function OverfitResult({ data, l3 }: { data: OverfitCheck; l3: Dictionary["l3Tools"] }) {
  return (
    <div className="mt-4 space-y-2 text-sm">
      <MiniStat label={l3.riskGrade} value={data.overfit.grade ?? "—"} />
      <MiniStat label={l3.riskScore} value={fmtNum(data.overfit.risk_score)} />
      <Notes notes={data.overfit.flags?.map((f) => f.message)} />
    </div>
  );
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-white px-3 py-2">
      <div className="text-xs text-slate-400">{label}</div>
      <div className="font-semibold text-slate-800">{value}</div>
    </div>
  );
}

function Notes({ notes }: { notes?: string[] }) {
  if (!notes?.length) return null;
  return (
    <ul className="space-y-1 text-xs text-slate-600">
      {notes.map((n) => (
        <li key={n} className="rounded bg-white p-2">
          {n}
        </li>
      ))}
    </ul>
  );
}

function fmtNum(v: number | null | undefined) {
  return v === null || v === undefined ? "—" : Number(v).toFixed(2);
}

function fmtPct(v: number | null | undefined) {
  return v === null || v === undefined ? "—" : `${(Number(v) * 100).toFixed(1)}%`;
}
