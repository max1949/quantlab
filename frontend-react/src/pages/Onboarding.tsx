import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { chooseType, trackEvent } from "../api/endpoints";
import { apiErrorMessage } from "../api/client";
import type { UserType } from "../api/types";

const types: { value: UserType; label: string; desc: string; emoji: string }[] = [
  {
    value: "newbie",
    label: "完全新手",
    desc: "没接触过量化, 想从零学会做研究",
    emoji: "🌱",
  },
  {
    value: "python",
    label: "Python 用户",
    desc: "有编程基础, 想快速验证研究想法",
    emoji: "🐍",
  },
  {
    value: "trader",
    label: "有交易经验",
    desc: "懂市场, 想把盘感系统化、可验证",
    emoji: "📈",
  },
];

export default function Onboarding() {
  const user = useAuth((s) => s.user);
  const setUser = useAuth((s) => s.setUser);
  const notify = useUi((s) => s.notify);
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
      notify("身份已确认, 给你定制好了研究路线", "success");
      navigate("/app", { replace: true });
    } catch (err) {
      notify(apiErrorMessage(err, "保存失败"), "error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-gradient-to-b from-white to-brand-50 px-4 py-12">
      <div className="w-full max-w-xl">
        <h1 className="text-center text-2xl font-bold text-slate-900">
          先了解一下你
        </h1>
        <p className="mt-2 text-center text-sm text-slate-500">
          选择最符合你的身份, 我们会给你定制研究节奏和模板。
        </p>

        <div className="mt-6 grid gap-3">
          {types.map((t) => (
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
                <span className="block font-semibold text-slate-800">
                  {t.label}
                </span>
                <span className="text-sm text-slate-500">{t.desc}</span>
              </span>
            </button>
          ))}
        </div>

        <button
          className="btn-primary mt-6 w-full py-3 text-base"
          onClick={confirm}
          disabled={loading}
        >
          {loading ? "保存中…" : "确认, 开始研究 →"}
        </button>
      </div>
    </div>
  );
}
