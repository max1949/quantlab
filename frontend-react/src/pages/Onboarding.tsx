import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import { chooseType, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import HandbookExportButtons from "../components/HandbookExportButtons";
import {
  FIRST_MENTOR_WELCOME_KEY,
  FOCUS_QUICKSTART_KEY,
  ORG_INVITE_ACCEPTED_ORG_KEY,
  ORG_INVITE_PENDING_KEY,
  FIRST_ORG_MEMBER_WELCOME_KEY,
} from "../lib/onboardingFocus";
import type { UserType } from "../api/types";

const TYPE_META: { value: UserType; key: "newbie" | "python" | "trader"; emoji: string }[] = [
  { value: "newbie", key: "newbie", emoji: "🌱" },
  { value: "python", key: "python", emoji: "🐍" },
  { value: "trader", key: "trader", emoji: "📈" },
];

export default function Onboarding() {
  const user = useAuth((s) => s.user);
  const setUser = useAuth((s) => s.setUser);
  const notify = useUi((s) => s.notify);
  const o = useLocale((s) => s.dict.onboarding);
  const h = useLocale((s) => s.dict.beginnerHandbook);
  const navigate = useNavigate();
  const [selected, setSelected] = useState<UserType>(
    (user?.user_type as UserType) ?? "newbie",
  );
  const [loading, setLoading] = useState(false);

  async function confirm() {
    setLoading(true);
    try {
      const updated = await chooseType(selected);
      setUser(updated);
      void trackEvent("onboarding_done", { user_type: selected });
      sessionStorage.setItem(FOCUS_QUICKSTART_KEY, "1");
      sessionStorage.setItem(FIRST_MENTOR_WELCOME_KEY, "1");
      notify(o.saved, "success");
      const acceptedOrg = sessionStorage.getItem(ORG_INVITE_ACCEPTED_ORG_KEY);
      if (acceptedOrg) {
        sessionStorage.removeItem(ORG_INVITE_ACCEPTED_ORG_KEY);
        sessionStorage.setItem(FIRST_ORG_MEMBER_WELCOME_KEY, acceptedOrg);
        navigate(`/orgs/${acceptedOrg}`, { replace: true });
        return;
      }
      const pendingInvite = sessionStorage.getItem(ORG_INVITE_PENDING_KEY);
      if (pendingInvite) {
        navigate(`/org-invite/${pendingInvite}`, { replace: true });
        return;
      }
      navigate("/app", { replace: true });
    } catch (err) {
      notify(apiErrorMessage(err, o.saveFail), "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-gradient-to-b from-white to-brand-50 px-4 py-12 dark:from-slate-950 dark:to-brand-950/30">
      <div className="w-full max-w-xl">
        <h1 className="text-center text-2xl font-bold text-slate-900 dark:text-slate-50">{o.title}</h1>
        <p className="mt-2 text-center text-sm text-slate-500 dark:text-slate-400">{o.subtitle}</p>

        <div className="mt-5 rounded-2xl border border-indigo-200 bg-indigo-50/60 p-4 dark:border-indigo-900 dark:bg-indigo-950/30">
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-800 dark:text-indigo-200">
            📄 {h.title}
          </p>
          <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">{o.handbookHint}</p>
          <div className="mt-3">
            <HandbookExportButtons compact />
          </div>
        </div>

        <div className="mt-6 grid gap-3">
          {TYPE_META.map((t) => {
            const info = o.types[t.key];
            return (
              <button
                key={t.value}
                onClick={() => setSelected(t.value)}
                className={`flex items-center gap-4 rounded-2xl border p-4 text-left transition ${
                  selected === t.value
                    ? "border-brand-500 bg-brand-50 ring-2 ring-brand-100 dark:bg-brand-950/40 dark:ring-brand-900"
                    : "border-slate-200 bg-white hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800"
                }`}
              >
                <span className="text-3xl">{t.emoji}</span>
                <span>
                  <span className="block font-semibold text-slate-800 dark:text-slate-100">{info.label}</span>
                  <span className="text-sm text-slate-500 dark:text-slate-400">{info.desc}</span>
                </span>
              </button>
            );
          })}
        </div>

        <button
          className="btn-primary mt-6 w-full py-3 text-base"
          onClick={confirm}
          disabled={loading}
        >
          {loading ? o.saving : o.confirm}
        </button>
      </div>
    </div>
  );
}
