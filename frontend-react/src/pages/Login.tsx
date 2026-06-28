import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { apiErrorMessage } from "../api/client";
import AuthShell from "../components/AuthShell";

export default function Login() {
  const login = useAuth((s) => s.login);
  const notify = useUi((s) => s.notify);
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/app";

  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const user = await login(identifier, password);
      notify(`欢迎回来, ${user.username}`, "success");
      navigate(user.onboarding_done ? from : "/onboarding", { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, "登录失败"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell title="登录 QuantLab AI" subtitle="继续你的量化研究之旅">
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">邮箱或用户名</label>
          <input
            className="input"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            autoFocus
            required
          />
        </div>
        <div>
          <label className="label">密码</label>
          <input
            type="password"
            className="input"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button className="btn-primary w-full" disabled={loading}>
          {loading ? "登录中…" : "登录"}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-500">
        还没有账号?{" "}
        <Link to="/register" className="font-medium text-brand-600">
          免费注册
        </Link>
      </p>
    </AuthShell>
  );
}
