import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { completeTask, listTasks } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import { AUTO_ACADEMY_TASK_CODES, localizedAcademyTitle } from "../lib/academy";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { useUi } from "../store/ui";
import { Spinner } from "./ui";

export default function AcademyTasks() {
  const d = useLocale((s) => s.dict.dashboard);
  const mp = useLocale((s) => s.dict.masteryPath);
  const atl = useLocale((s) => s.dict.academyTaskLabels);
  const setUser = useAuth((s) => s.setUser);
  const notify = useUi((s) => s.notify);
  const qc = useQueryClient();

  const tasks = useQuery({ queryKey: ["academy-tasks"], queryFn: listTasks });

  const claim = useMutation({
    mutationFn: (code: string) => completeTask(code),
    onSuccess: (res) => {
      setUser(res.user);
      notify(d.academyClaimed, "success");
      void qc.invalidateQueries({ queryKey: ["academy-tasks"] });
    },
    onError: (e) => notify(apiErrorMessage(e), "error"),
  });

  if (tasks.isLoading) return <Spinner />;

  const rows = tasks.data ?? [];
  const done = rows.filter((t) => t.completed).length;

  return (
    <div className="card">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">{d.academyTitle}</h3>
          <p className="text-sm text-slate-500">{d.academySubtitle}</p>
        </div>
        <span className="badge">
          {done}/{rows.length}
        </span>
      </div>
      <ul className="space-y-2">
        {rows.map((t) => (
          <li
            key={t.id}
            className={`rounded-xl border px-3 py-2.5 ${
              t.completed
                ? "border-emerald-200 bg-emerald-50/50 dark:border-emerald-900 dark:bg-emerald-950/30"
                : t.locked
                  ? "border-slate-100 bg-slate-50/80 opacity-75 dark:border-slate-800 dark:bg-slate-900/40"
                  : t.code === "network-radar" && !t.completed
                    ? "border-brand-200 bg-brand-50/40 dark:border-brand-900 dark:bg-brand-950/20"
                    : "border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900"
            }`}
          >
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <div className="min-w-0">
                <p className="font-medium text-slate-800 dark:text-slate-100">
                  {t.completed && "✓ "}
                  {localizedAcademyTitle(t.code, t.title, atl)}
                  <span className="ml-2 text-xs font-normal text-brand-600">{d.academyXp(t.xp_reward)}</span>
                  {t.mastery_stage && (
                    <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-normal text-slate-500 dark:bg-slate-800 dark:text-slate-400">
                      {d.academyMasteryStage(
                        mp.stages[t.mastery_stage as keyof typeof mp.stages] ?? t.mastery_stage,
                      )}
                    </span>
                  )}
                </p>
                <p className="text-sm text-slate-500">
                  {atl[t.code as keyof typeof atl]?.description ?? t.description}
                </p>
                {t.locked && (
                  <p className="mt-1 text-xs text-amber-600">
                    {d.academyLocked} · {t.min_level_label}
                  </p>
                )}
              </div>
              {!t.completed && !t.locked && AUTO_ACADEMY_TASK_CODES.has(t.code) && (
                <span className="text-sm text-brand-600">{d.academyAuto}</span>
              )}
              {!t.completed && !t.locked && !AUTO_ACADEMY_TASK_CODES.has(t.code) && (
                <button
                  type="button"
                  className="btn-primary w-full shrink-0 sm:w-auto"
                  disabled={claim.isPending}
                  onClick={() => claim.mutate(t.code)}
                >
                  {d.academyClaim}
                </button>
              )}
              {t.completed && (
                <span className="text-sm font-medium text-emerald-600">{d.academyDone}</span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
