import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import { apiErrorMessage } from "../api/client";
import { getSsoConfig } from "../api/endpoints";
import AuthShell from "../components/AuthShell";
import CaptchaField from "../components/CaptchaField";

export default function Login() {
  const login = useAuth((s) => s.login);
  const loginWithToken = useAuth((s) => s.loginWithToken);
  const notify = useUi((s) => s.notify);
  const auth = useLocale((s) => s.dict.auth);
  const nav = useLocale((s) => s.dict.nav);
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/app";

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [captchaAnswer, setCaptchaAnswer] = useState("");
  const [captchaToken, setCaptchaToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const sso = useQuery({ queryKey: ["sso-config"], queryFn: getSsoConfig });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const ssoToken = params.get("sso_token");
    const ssoError = params.get("sso_error");
    if (ssoToken) {
      window.history.replaceState({}, "", window.location.pathname);
      void loginWithToken(ssoToken)
        .then((user) => {
          notify(auth.welcomeBack(user.username), "success");
          navigate(user.onboarding_done ? from : "/onboarding", { replace: true });
        })
        .catch((err) => setError(apiErrorMessage(err, auth.loginFailed)));
    } else if (ssoError) {
      window.history.replaceState({}, "", window.location.pathname);
      setError(auth.ssoFailed);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const user = await login(identifier, password, captchaToken, captchaAnswer);
      notify(auth.welcomeBack(user.username), "success");
      navigate(user.onboarding_done ? from : "/onboarding", { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, auth.loginFailed));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell title={auth.loginTitle} subtitle={auth.loginSubtitle}>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">{auth.identifier}</label>
          <input
            className="input"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            autoFocus
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
            required
          />
        </div>
        <CaptchaField
          answer={captchaAnswer}
          onAnswer={setCaptchaAnswer}
          token={captchaToken}
          onToken={setCaptchaToken}
        />
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button className="btn-primary w-full" disabled={loading}>
          {loading ? auth.signingIn : auth.signIn}
        </button>
      </form>
      {sso.data?.enabled && (
        <div className="mt-4">
          <div className="mb-3 flex items-center gap-3 text-xs text-slate-400">
            <span className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
            {auth.ssoDivider}
            <span className="h-px flex-1 bg-slate-200 dark:bg-slate-700" />
          </div>
          <a className="btn w-full text-center" href="/api/v1/auth/sso/login">
            {auth.ssoSignIn}
          </a>
        </div>
      )}
      <p className="mt-4 text-center text-sm text-slate-500">
        {auth.noAccount}{" "}
        <Link to="/register" className="font-medium text-brand-600">
          {nav.register}
        </Link>
      </p>
    </AuthShell>
  );
}
