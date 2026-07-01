import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import { chooseType, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
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
      notify(o.saved, "success");
      navigate("/app", { replace: true });
    } catch (err) {
      notify(apiErrorMessage(err, o.saveFail), "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-gradient-to-b from-white to-brand-50 px-4 py-12">
      <div className="w-full max-w-xl">
        <h1 className="text-center text-2xl font-bold text-slate-900">{o.title}</h1>
        <p className="mt-2 text-center text-sm text-slate-500">{o.subtitle}</p>

        <div className="mt-6 grid gap-3">
          {TYPE_META.map((t) => {
            const info = o.types[t.key];
            return (
              <button
                key={t.value}
                onClick={() => setSelected(t.value)}
                className={`flex items-center gap-4 rounded-2xl border p-4 text-left transition ${
                  selected === t.value
                    ? "border-brand-500 bg-brand-50 ring-2 ring-brand-100"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
              >
                <span className="text-3xl">{t.emoji}</span>
                <span>
                  <span className="block font-semibold text-slate-800">{info.label}</span>
                  <span className="text-sm text-slate-500">{info.desc}</span>
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
