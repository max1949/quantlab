import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import {
  type ProjectCoachId,
  listActiveProjectCoaches,
  type ProjectCoachProgress,
} from "../lib/projectCoachPriority";
import { useLocale } from "../store/locale";
import FirstBacktestCoachPanel from "./FirstBacktestCoachPanel";
import FirstPaperOrderCoachPanel from "./FirstPaperOrderCoachPanel";
import FirstProjectCoachPanel from "./FirstProjectCoachPanel";
import FirstValidationCoachPanel from "./FirstValidationCoachPanel";
import MasterReplicationProjectCoachPanel from "./MasterReplicationProjectCoachPanel";

const EXPAND_KEY = "quantlab-project-coach-expanded";

type Props = ProjectCoachProgress & {
  backtestPending: boolean;
  validationPending: boolean;
  reportPending: boolean;
  onRunBacktest: () => void;
  onRunValidation: () => void;
  onGenerateReport: () => void;
};

function CoachById({
  id,
  props,
}: {
  id: ProjectCoachId;
  props: Props;
}) {
  switch (id) {
    case "first_project":
      return (
        <FirstProjectCoachPanel
          projectId={props.projectId}
          backtestDone={props.backtestDone}
          backtestPending={props.backtestPending}
          onRunBacktest={props.onRunBacktest}
        />
      );
    case "first_backtest":
      return (
        <FirstBacktestCoachPanel
          projectId={props.projectId}
          backtestDone={props.backtestDone}
          validationDone={props.validationDone}
          validationPending={props.validationPending}
          onRunValidation={props.onRunValidation}
        />
      );
    case "first_validation":
      return (
        <FirstValidationCoachPanel
          projectId={props.projectId}
          validationDone={props.validationDone}
          reportDone={props.reportDone}
          reportPending={props.reportPending}
          onGenerateReport={props.onGenerateReport}
        />
      );
    case "first_paper_order":
      return <FirstPaperOrderCoachPanel projectId={props.projectId} placement="project" />;
  }
}

export default function ProjectIncubationCoachStack(props: Props) {
  const p = useLocale((s) => s.dict.projectDetail);
  const labels = useLocale((s) => s.dict.projectCoachLabels);
  const [expanded, setExpanded] = useState(() => localStorage.getItem(EXPAND_KEY) === "1");

  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  const active = listActiveProjectCoaches(journey.data, props);
  const needsFold = active.length > 1;
  const visibleIds = expanded || !needsFold ? active : active.slice(0, 1);
  const hiddenIds = expanded || !needsFold ? [] : active.slice(1);

  return (
    <>
      <MasterReplicationProjectCoachPanel
        projectId={props.projectId}
        backtestDone={props.backtestDone}
        backtestPending={props.backtestPending}
        onRunBacktest={props.onRunBacktest}
      />
      {active.length === 0 ? null : (
        <div className="mb-4 space-y-4">
          {visibleIds.map((id) => (
            <CoachById key={id} id={id} props={props} />
          ))}

          {hiddenIds.length > 0 && (
            <div className="card border border-dashed border-slate-200 bg-slate-50/60 dark:border-slate-700 dark:bg-slate-900/40">
              <p className="text-xs font-medium text-slate-600 dark:text-slate-300">
                {p.projectCoachMore(hiddenIds.length)}
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
                {p.projectCoachExpand}
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
              {p.projectCoachCollapse}
            </button>
          )}
        </div>
      )}
    </>
  );
}
