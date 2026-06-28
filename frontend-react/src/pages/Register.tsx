import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useUi } from "../store/ui";
import { apiErrorMessage } from "../api/client";
import { trackEvent } from "../api/endpoints";
import AuthShell from "../components/AuthShell";
import type { UserType } from "../api/types";

const types: { value: UserType; label: string; desc: string }[] = [
  { value: "newbie", label: "完全新手", desc: "没接触过量化, 从模板起步" },
  { value: "python", label: "Python 用户", desc: "有编程基础, 想做研究" },
  { value: "trader", label: "有交易经验", desc: "懂市场, 想系统化验证想法" },
];

export default function Register() {
  const register = useAuth((s) => s.register);
  const notify = useUi((s) => s.notify);
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const ref = params.get("ref");

  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [userType, setUserType] = useState<UserType>("newbie");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await register({ email, username, password, user_type: userType, ref });
      void trackEvent("register_done", { user_type: userType, ref });
      notify("注册成功, 开始你的研究吧!", "success");
      navigate("/onboarding", { replace: true });
    } catch (err) {
      setError(apiErrorMessage(err, "注册失败"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title="加入 QuantLab AI"
      subtitle={ref ? `由 ${ref} 邀请加入` : "5 分钟完成第一次研究"}
    >
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="label">邮箱</label>
          <input
            type="email"
            className="input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label">用户名 (字母/数字/下划线, 3-50 位)</label>
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
          <label className="label">密码 (至少 8 位)</label>
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
          <label className="label">你的身份</label>
          <div className="grid gap-2">
            {types.map((t) => (
              <button
                type="button"
                key={t.value}
                onClick={() => setUserType(t.value)}
                className={`rounded-lg border px-3 py-2 text-left text-sm transition ${
                  userType === t.value
                    ? "border-brand-500 bg-brand-50"
                    : "border-slate-200 hover:bg-slate-50"
                }`}
              >
                <span className="font-medium">{t.label}</span>
                <span className="ml-2 text-slate-400">{t.desc}</span>
              </button>
            ))}
          </div>
        </div>
        {error && <p className="text-sm text-rose-600">{error}</p>}
        <button className="btn-primary w-full" disabled={loading}>
          {loading ? "注册中…" : "免费注册"}
        </button>
      </form>
      <p className="mt-4 text-center text-sm text-slate-500">
        已有账号?{" "}
        <Link to="/login" className="font-medium text-brand-600">
          去登录
        </Link>
      </p>
    </AuthShell>
  );
}
