import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { useLevelLabel } from "../i18n/useLevelLabel";
import {
  getMentor,
  getNextStep,
  listMyReports,
  listProjects,
} from "../api/endpoints";
import { stageToCtaLabel, stageToRoute } from "../lib/nav";
import { GradeBadge, PageTitle, Spinner, Stat } from "../components/ui";
import AcademyTasks from "../components/AcademyTasks";

export default function Dashboard() {
  const user = useAuth((s) => s.user)!;
  const navigate = useNavigate();
  const d = useLocale((s) => s.dict.dashboard);
  const stages = useLocale((s) => s.dict.stages);
  const levelName = useLevelLabel(user.level);

  const nextStep = useQuery({ queryKey: ["next-step"], queryFn: getNextStep });
  const mentor = useQuery({ queryKey: ["mentor"], queryFn: getMentor });
  const projects = useQuery({ queryKey: ["projects"], queryFn: listProjects });
  const reports = useQuery({ queryKey: ["my-reports"], queryFn: listMyReports });

  return (
    <div>
      <PageTitle
        title={d.welcome(user.username)}
        subtitle={nextStep.data?.intro ?? d.subtitle}
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat label={d.creditScore} value={user.research_contribution_score.toFixed(1)} />
        <Stat label={d.rewardPoints} value={user.reward_points} />
        <Stat label={d.arenaScore} value={user.research_score.toFixed(1)} />
        <Stat label={d.level} value={levelName} />
      </div>

      <div className="mt-6 rounded-2xl bg-gradient-to-r from-brand-600 to-brand-500 p-6 text-white shadow-md">
        {nextStep.isLoading ? (
          <p>{d.planning}</p>
        ) : nextStep.data ? (
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-brand-100">{d.nextStep}</p>
              <h2 className="mt-1 text-xl font-bold">{nextStep.data.title}</h2>
              <p className="mt-1 text-sm text-brand-50">{nextStep.data.action}</p>
            </div>
            <button
              className="btn whitespace-nowrap bg-white text-brand-700 hover:bg-brand-50"
              onClick={() =>
                navigate(
                  stageToRoute(
                    nextStep.data!.stage,
                    nextStep.data!.recommended_template,
                    nextStep.data!.active_project_id,
                  ),
                )
              }
            >
              {stageToCtaLabel(nextStep.data.stage, stages)}
            </button>
          </div>
        ) : null}
      </div>

      {mentor.data && (
        <div className="mt-4 card border-brand-100 bg-brand-50/40">
          <div className="flex items-start gap-3">
            <span className="text-2xl">🤖</span>
            <div>
              <p className="font-semibold text-slate-800">
                {d.aiMentor} · {mentor.data.title}
              </p>
              <p className="mt-1 text-sm text-slate-600">{mentor.data.message}</p>
              <p className="mt-2 text-xs text-slate-400">{mentor.data.disclaimer}</p>
            </div>
          </div>
        </div>
      )}

      <div className="mt-6">
        <AcademyTasks />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="card">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-semibold">{d.myProjects}</h3>
            <Link to="/projects" className="text-sm text-brand-600">
              {d.allProjects}
            </Link>
          </div>
          {projects.isLoading ? (
            <Spinner />
          ) : projects.data && projects.data.length > 0 ? (
            <ul className="space-y-2">
              {projects.data.slice(0, 5).map((p) => (
                <li key={p.id}>
                  <Link
                    to={`/projects/${p.id}`}
                    className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-slate-50"
                  >
                    <span className="truncate font-medium text-slate-700">{p.title}</span>
                    <span className="badge">{p.status}</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-4 text-sm text-slate-400">
              {d.noProjects}{" "}
              <Link to="/templates" className="text-brand-600">
                {d.fromTemplate}
              </Link>
            </p>
          )}
        </div>

        <div className="card">
          <h3 className="mb-3 font-semibold">{d.myReports}</h3>
          {reports.isLoading ? (
            <Spinner />
          ) : reports.data && reports.data.length > 0 ? (
            <ul className="space-y-2">
              {reports.data.slice(0, 5).map((r) => (
                <li key={r.id}>
                  <Link
                    to={`/reports/${r.id}`}
                    className="flex items-center justify-between rounded-lg px-3 py-2 hover:bg-slate-50"
                  >
                    <span className="truncate font-medium text-slate-700">{r.title}</span>
                    <GradeBadge grade={r.grade} />
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-4 text-sm text-slate-400">{d.noReports}</p>
          )}
        </div>
      </div>
    </div>
  );
}
