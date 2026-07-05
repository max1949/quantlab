import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getResearchJourney } from "../api/endpoints";
import type { ResearchJourney } from "../api/types";
import { useLocale } from "../store/locale";
import AttentionAlertsPanel from "./AttentionAlertsPanel";
import ChallengePaperCoachPanel from "./ChallengePaperCoachPanel";
import UpgradeCoachPanel from "./UpgradeCoachPanel";
import MarketDataCoachPanel from "./MarketDataCoachPanel";

const MAX_VISIBLE = 2;
const EXPAND_KEY = "quantlab-coach-stack-expanded";

type CoachKind = "attention" | "challenge" | "upgrade" | "market";

function coachKindsFromJourney(journey: ResearchJourney | undefined): CoachKind[] {
  if (!journey) return [];
  const kinds: CoachKind[] = [];
  if (journey.attention_alerts.length > 0) kinds.push("attention");
  if (journey.challenge_paper_coaching) kinds.push("challenge");
  if (journey.upgrade_coaching) kinds.push("upgrade");
  if (journey.market_data_coaching) kinds.push("market");
  return kinds;
}

function CoachPanel({ kind }: { kind: CoachKind }) {
  switch (kind) {
    case "attention":
      return <AttentionAlertsPanel />;
    case "challenge":
      return <ChallengePaperCoachPanel />;
    case "upgrade":
      return <UpgradeCoachPanel />;
    case "market":
      return <MarketDataCoachPanel />;
  }
}

export default function DashboardCoachStack() {
  const d = useLocale((s) => s.dict.dashboard);
  const [expanded, setExpanded] = useState(() => localStorage.getItem(EXPAND_KEY) === "1");
  const journey = useQuery({ queryKey: ["research-journey"], queryFn: () => getResearchJourney() });

  const kinds = coachKindsFromJourney(journey.data);
  if (kinds.length === 0) return null;

  const needsFold = kinds.length > MAX_VISIBLE;
  const visible = expanded || !needsFold ? kinds : kinds.slice(0, MAX_VISIBLE);
  const hidden = expanded || !needsFold ? [] : kinds.slice(MAX_VISIBLE);

  const summaryLine = (kind: CoachKind): string => {
    const j = journey.data;
    if (!j) return "…";
    switch (kind) {
      case "attention":
        return d.coachStackAttention(j.attention_alerts.length);
      case "challenge":
        return d.coachStackChallenge(j.challenge_paper_coaching?.message ?? "");
      case "upgrade":
        return d.coachStackUpgrade(j.upgrade_coaching?.message ?? "");
      case "market":
        return d.coachStackMarket(j.market_data_coaching?.message ?? "");
    }
  };

  return (
    <div className="space-y-4">
      {visible.map((kind) => (
        <CoachPanel key={kind} kind={kind} />
      ))}

      {hidden.length > 0 && (
        <div className="card border border-dashed border-slate-200 bg-slate-50/60 dark:border-slate-700 dark:bg-slate-900/40">
          <p className="text-xs font-medium text-slate-600 dark:text-slate-300">
            {d.coachStackMore(hidden.length)}
          </p>
          <ul className="mt-2 space-y-1 text-xs text-slate-500 dark:text-slate-400">
            {hidden.map((kind) => (
              <li key={kind} className="truncate">
                {summaryLine(kind)}
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
            {d.coachStackExpand}
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
          {d.coachStackCollapse}
        </button>
      )}
    </div>
  );
}
