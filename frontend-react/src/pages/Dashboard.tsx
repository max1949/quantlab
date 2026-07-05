import { useState } from "react";
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
import ResearchJourneyRing from "../components/ResearchJourneyRing";
import MasteryGoalPanel from "../components/MasteryGoalPanel";
import DashboardCoachStack from "../components/DashboardCoachStack";
import OrgMemberCoachPanel from "../components/OrgMemberCoachPanel";
import ResearchRevisitCoachPanel from "../components/ResearchRevisitCoachPanel";
import PostCheckoutCoachPanel from "../components/PostCheckoutCoachPanel";
import QuickStartGuidePanel from "../components/QuickStartGuidePanel";
import FirstDashboardMentorPanel from "../components/FirstDashboardMentorPanel";
import FirstReportCoachPanel from "../components/FirstReportCoachPanel";
import FirstPaperOrderCoachPanel from "../components/FirstPaperOrderCoachPanel";
import MasteryOverviewPanel from "../components/MasteryOverviewPanel";
import ReputationCoachPanel from "../components/ReputationCoachPanel";
import ShareGrowthCoachPanel from "../components/ShareGrowthCoachPanel";
import MasteryGraduationPanel from "../components/MasteryGraduationPanel";
import BeginnerHandbookStrip from "../components/BeginnerHandbookStrip";

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
  const [firstMentorVisible, setFirstMentorVisible] = useState(false);

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

      <div className="mt-6">
        <PostCheckoutCoachPanel />
      </div>

      <div className="mt-6">
        <OrgMemberCoachPanel />
      </div>

      <div className="mt-6">
        <ResearchRevisitCoachPanel />
      </div>

      <div className="mt-6">
        <BeginnerHandbookStrip />
      </div>

      <div className="mt-6">
        <FirstDashboardMentorPanel onVisibilityChange={setFirstMentorVisible} />
      </div>

      <div className="mt-6">
        <QuickStartGuidePanel />
      </div>

      <div className="mt-6">
        <FirstReportCoachPanel />
      </div>

      <div className="mt-6">
        <FirstPaperOrderCoachPanel placement="dashboard" />
      </div>

      <div className="mt-6">
        <MasteryOverviewPanel />
      </div>

      <div className="mt-6">
        <ReputationCoachPanel />
      </div>

      <div className="mt-6">
        <ShareGrowthCoachPanel />
      </div>

      <div className="mt-6">
        <MasteryGraduationPanel />
      </div>

      {!firstMentorVisible && (
      <div className="mt-6 rounded-2xl bg-gradient-to-r from-brand-600 to-brand-500 p-6 text-white shadow-md">
        {nextStep.isLoading ? (
          <p>{d.planning}</p>
        ) : nextStep.data ? (
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-brand-100">{d.nextStep}</p>
              <h2 className="mt-1 text-xl font-bold">{nextStep.data.title}</h2>
              <p className="mt-1 text-sm text-brand-50">{nextStep.data.action}</p>
              {nextStep.data.regime_pick?.coach_hint && (
                <p className="mt-2 rounded-lg bg-white/15 px-3 py-2 text-xs text-brand-50">
                  {d.regimeCoach(
                    nextStep.data.regime_pick.regime_label ?? "",
                    nextStep.data.regime_pick.template_title,
                    nextStep.data.regime_pick.fit_verdict,
                    nextStep.data.regime_pick.fit_score,
                  )}
                  <span className="opacity-90"> — {nextStep.data.regime_pick.coach_hint}</span>
                </p>
              )}
            </div>
            <button
              className="btn whitespace-nowrap bg-white text-brand-700 hover:bg-brand-50"
              onClick={() =>
                navigate(
                  stageToRoute(
                    nextStep.data!.stage,
                    nextStep.data!.recommended_template,
                    nextStep.data!.active_project_id,
                    nextStep.data!.regime_pick?.symbol,
                  ),
                )
              }
            >
              {stageToCtaLabel(nextStep.data.stage, stages)}
            </button>
          </div>
        ) : null}
      </div>
      )}

      <div className="mt-6">
        <DashboardCoachStack />
      </div>

      <div className="mt-6">
        <MasteryGoalPanel />
      </div>

      <div className="mt-6">
        <ResearchJourneyRing />
      </div>

      {mentor.data && !firstMentorVisible && (
        <div className="mt-4 card border-brand-100 bg-brand-50/40">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex items-start gap-3">
              <span className="text-2xl">🤖</span>
              <div>
                <p className="font-semibold text-slate-800">
                  {d.aiMentor} · {mentor.data.title}
                </p>
                <p className="mt-1 text-sm text-slate-600">{mentor.data.message}</p>
                {mentor.data.regime_pick?.template_title && (
                  <p className="mt-2 rounded-lg border border-violet-200 bg-violet-50/60 px-2.5 py-1.5 text-xs text-violet-900 dark:border-violet-900 dark:bg-violet-950/30 dark:text-violet-100">
                    {d.mentorRegime(
                      mentor.data.regime_pick.symbol,
                      mentor.data.regime_pick.regime_label ?? "",
                      mentor.data.regime_pick.template_title,
                      mentor.data.regime_pick.fit_verdict,
                      mentor.data.regime_pick.fit_score,
                    )}
                  </p>
                )}
                {mentor.data.attention_alerts && mentor.data.attention_alerts.length > 0 && (
                  <div className="mt-2 rounded-lg border border-rose-200 bg-rose-50/60 px-2.5 py-1.5 text-xs text-rose-900 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-100">
                    <p className="font-medium">{d.mentorAttentionTitle}</p>
                    {mentor.data.attention_alerts.slice(0, 2).map((a) => (
                      <p key={`${a.kind}-${a.title}`} className="mt-1 opacity-90">
                        {a.title} — {a.message}
                      </p>
                    ))}
                  </div>
                )}
                <p className="mt-2 text-xs text-slate-400">{mentor.data.disclaimer}</p>
              </div>
            </div>
            {mentor.data.stage === "create_project" && mentor.data.recommended_template && (
              <button
                type="button"
                className="btn shrink-0 text-sm"
                onClick={() =>
                  navigate(
                    stageToRoute(
                      mentor.data!.stage,
                      mentor.data!.recommended_template,
                      null,
                      mentor.data!.regime_pick?.symbol,
                    ),
                  )
                }
              >
                {stageToCtaLabel(mentor.data.stage, stages)}
              </button>
            )}
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
