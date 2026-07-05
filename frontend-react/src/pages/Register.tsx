import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import { apiErrorMessage } from "../api/client";
import { trackEvent } from "../api/endpoints";
import AuthShell from "../components/AuthShell";
import CaptchaField from "../components/CaptchaField";
import type { UserType } from "../api/types";

export default function Register() {
  const register = useAuth((s) => s.register);
  const notify = useUi((s) => s.notify);
  const auth = useLocale((s) => s.dict.auth);
  const nav = useLocale((s) => s.dict.nav);
  const locale = useLocale((s) => s.locale);
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const ref = params.get("ref");

  const types: { value: UserType; label: string; desc: string }[] =
    locale === "zh"
      ? [
          { value: "newbie", label: "完全新手", desc: "没接触过量化, 从模板起步" },
          { value: "python", label: "Python 用户", desc: "有编程基础, 想做研究" },
          { value: "trader", label: "有交易经验", desc: "懂市场, 想系统化验证想法" },
        ]
      : [
          { value: "newbie", label: "Complete beginner", desc: "Start from templates" },
          { value: "python", label: "Python user", desc: "Code-ready researcher path" },
          { value: "trader", label: "Experienced trader", desc: "Validate ideas systematically" },
        ];

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [userType, setUserType] = useState<UserType>("newbie");
  const [captchaAnswer, setCaptchaAnswer] = useState("");
  const [captchaToken, setCaptchaToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { welcomeEmailHint } = await register({
        email,
        username,
        password,
        user_type: userType,
        ref,
        captcha_token: captchaToken,
        captcha_answer: captchaAnswer,
      });
      void trackEvent("register_done", { user_type: userType, ref });
      notify(auth.registerSuccess, "success");
      if (welcomeEmailHint) {
        notify(welcomeEmailHint, "info");
      }
      navigate("/onboarding", { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, auth.registerFailed));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title={auth.registerTitle}
      subtitle={ref ? `${ref}` : auth.registerSubtitle}
    >
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">{auth.email}</label>
          <input
            type="email"
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label">{auth.username}</label>
          <input
            className="input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            minLength={3}
            pattern="[A-Za-z0-9_]+"
            required
          />
        </div>
        <div>
          <label className="label">{auth.password}</label>
          <input
            type="password"
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />
        </div>
        <div>
          <label className="label">{locale === "zh" ? "你的身份" : "Your profile"}</label>
          <div className="grid gap-2">
            {types.map((t) => (
              <button
                type="button"
                key={t.value}
                onClick={() => setUserType(t.value)}
                className={`rounded-lg border px-3 py-2 text-left text-sm transition ${
                  userType === t.value
                    ? "border-brand-500 bg-brand-50 dark:bg-brand-950"
                    : "border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
                }`}
              >
                <span className="font-medium">{t.label}</span>
                <span className="ml-2 text-slate-400">{t.desc}</span>
              </button>
            ))}
          </div>
        </div>
        <CaptchaField
          answer={captchaAnswer}
          onAnswer={setCaptchaAnswer}
          token={captchaToken}
          onToken={setCaptchaToken}
        />
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button className="btn-primary w-full" disabled={loading}>
          {loading ? auth.signingUp : nav.register}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-500">
        {auth.hasAccount}{" "}
        <Link to="/login" className="font-medium text-brand-600">
          {auth.signIn}
        </Link>
      </p>
    </AuthShell>
  );
}
