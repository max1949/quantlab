import { useQuery } from "@tanstack/react-query";
import { getReferral } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { ErrorBox, PageTitle, Spinner, Stat } from "../components/ui";

export default function Referral() {
  const { dict } = useLocale();
  const t = dict.referral;
  const notify = useUi((s) => s.notify);
  const q = useQuery({ queryKey: ["referral"], queryFn: getReferral });

  if (q.isLoading) return <Spinner />;
  if (q.isError) return <ErrorBox message={apiErrorMessage(q.error)} />;

  const r = q.data!;
  const inviteUrl = `${window.location.origin}/app/?ref=${encodeURIComponent(r.code)}`;

  async function copy() {
    await navigator.clipboard.writeText(inviteUrl);
    notify(t.copied, "success");
  }

  return (
    <div className="mx-auto max-w-2xl">
      <PageTitle title={t.title} subtitle={t.subtitle} />

      <div className="card bg-brand-50/40">
        <p className="text-sm text-slate-500">{t.linkLabel}</p>
        <div className="mt-2 flex flex-col gap-2 sm:flex-row">
          <input className="input flex-1" value={inviteUrl} readOnly />
          <button className="btn-primary" onClick={copy}>
            {t.copy}
          </button>
        </div>
        <p className="mt-2 text-xs text-slate-400">
          {t.code}: {r.code}
        </p>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Stat label={t.invited} value={r.invited} />
        <Stat label={t.activated} value={r.activated} />
        <Stat label={t.pointsEarned} value={r.reward_points_earned} />
      </div>
    </div>
  );
}
