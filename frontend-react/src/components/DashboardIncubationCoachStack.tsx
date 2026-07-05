import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import {
  type IncubationCoachId,
  listActiveIncubationCoaches,
} from "../lib/incubationCoachPriority";
import { useLocale } from "../store/locale";
import FirstDashboardMentorPanel from "./FirstDashboardMentorPanel";
import FirstPaperOrderCoachPanel from "./FirstPaperOrderCoachPanel";
import FirstReportCoachPanel from "./FirstReportCoachPanel";
import MasteryGraduationPanel from "./MasteryGraduationPanel";
import MasteryOverviewPanel from "./MasteryOverviewPanel";
import OrgMemberCoachPanel from "./OrgMemberCoachPanel";
import PostCheckoutCoachPanel from "./PostCheckoutCoachPanel";
import QuickStartGuidePanel from "./QuickStartGuidePanel";
import ResearchRevisitCoachPanel from "./ResearchRevisitCoachPanel";
import ReputationCoachPanel from "./ReputationCoachPanel";
import ShareGrowthCoachPanel from "./ShareGrowthCoachPanel";

const EXPAND_KEY = "quantlab-incubation-coach-expanded";

type Props = {
  onFirstMentorVisibilityChange?: (visible: boolean) => void;
};

function CoachById({ id }: { id: IncubationCoachId }) {
  switch (id) {
    case "checkout":
      return <PostCheckoutCoachPanel />;
    case "graduation":
      return <MasteryGraduationPanel />;
    case "first_paper_order":
      return <FirstPaperOrderCoachPanel placement="dashboard" />;
    case "first_report":
      return <FirstReportCoachPanel />;
    case "org_member":
      return <OrgMemberCoachPanel />;
    case "reputation":
      return <ReputationCoachPanel />;
    case "share_growth":
      return <ShareGrowthCoachPanel />;
    case "first_mentor":
      return <FirstDashboardMentorPanel />;
    case "quickstart":
      return <QuickStartGuidePanel />;
    case "revisit":
      return <ResearchRevisitCoachPanel />;
    case "mastery_overview":
      return <MasteryOverviewPanel />;
  }
}

export default function DashboardIncubationCoachStack({ onFirstMentorVisibilityChange }: Props) {
  const d = useLocale((s) => s.dict.dashboard);
  const labels = useLocale((s) => s.dict.incubationCoachLabels);
  const [searchParams] = useSearchParams();
  const [expanded, setExpanded] = useState(() => localStorage.getItem(EXPAND_KEY) === "1");
  const [firstMentorVisible, setFirstMentorVisible] = useState(false);

  const checkoutPlan =
    searchParams.get("checkout") === "success" ? searchParams.get("plan") : null;

  const journey = useQuery({
    queryKey: ["research-journey", checkoutPlan ?? "default"],
    queryFn: () => getResearchJourney({ checkoutPlan: checkoutPlan ?? undefined }),
  });

  const active = listActiveIncubationCoaches(journey.data, {
    checkoutActive: Boolean(checkoutPlan),
    firstMentorVisible,
  });

  const handleMentorVisibility = (visible: boolean) => {
    setFirstMentorVisible(visible);
    onFirstMentorVisibilityChange?.(visible);
  };

  if (active.length === 0) {
    return (
      <FirstDashboardMentorPanel onVisibilityChange={handleMentorVisibility} />
    );
  }

  const needsFold = active.length > 1;
  const visibleIds = expanded || !needsFold ? active : active.slice(0, 1);
  const hiddenIds = expanded || !needsFold ? [] : active.slice(1);

  return (
    <div className="space-y-4">
      {visibleIds.map((id) =>
        id === "first_mentor" ? (
          <FirstDashboardMentorPanel key={id} onVisibilityChange={handleMentorVisibility} />
        ) : (
          <CoachById key={id} id={id} />
        ),
      )}

      {hiddenIds.length > 0 && (
        <div className="card border border-dashed border-slate-200 bg-slate-50/60 dark:border-slate-700 dark:bg-slate-900/40">
          <p className="text-xs font-medium text-slate-600 dark:text-slate-300">
            {d.incubationCoachMore(hiddenIds.length)}
          </p>
          <ul className="mt-2 space-y-1 text-xs text-slate-500 dark:text-slate-400">
            {hiddenIds.map((id) => (
              <li key={id} className="truncate">
                {labels[id](journey.data!)}
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="btn mt-3 text-xs"
            onClick={() => {
              setExpanded(true);
              localStorage.setItem(EXPAND_KEY, "1");
            }}
          >
            {d.incubationCoachExpand}
          </button>
        </div>
      )}

      {needsFold && expanded && (
        <button
          type="button"
          className="text-xs font-medium text-slate-500 hover:text-brand-600"
          onClick={() => {
            setExpanded(false);
            localStorage.removeItem(EXPAND_KEY);
          }}
        >
          {d.incubationCoachCollapse}
        </button>
      )}
    </div>
  );
}
