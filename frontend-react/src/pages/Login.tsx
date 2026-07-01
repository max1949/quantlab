import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { useLocale } from "../store/locale";
import { apiErrorMessage } from "../api/client";
import AuthShell from "../components/AuthShell";
import CaptchaField from "../components/CaptchaField";

export default function Login() {
  const login = useAuth((s) => s.login);
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
      <p className="mt-4 text-center text-sm text-slate-500">
        {auth.noAccount}{" "}
        <Link to="/register" className="font-medium text-brand-600">
          {nav.register}
        </Link>
      </p>
    </AuthShell>
  );
}
