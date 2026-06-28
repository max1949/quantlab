import { useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../store/auth";
import { trackEvent } from "../api/endpoints";

const features = [
  {
    title: "1. 选个研究模板",
    desc: "不用写代码, 从均线动量、波动率等模板一键开局。",
  },
  {
    title: "2. 跑回测 + 科学验证",
    desc: "系统自动做样本外检验、滚动回测、参数敏感性。",
  },
  {
    title: "3. 生成研究报告",
    desc: "AI 把结果写成有结论、有风险分析的研究报告。",
  },
  {
    title: "4. 分享 + 上榜",
    desc: "一键生成分享卡片, 积累研究信用分, 登上研究员榜单。",
  },
];

export default function Landing() {
  const user = useAuth((s) => s.user);
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const ref = params.get("ref");

  useEffect(() => {
    void trackEvent("landing_view", { ref });
  }, [ref]);

  const registerHref = ref ? `/register?ref=${encodeURIComponent(ref)}` : "/register";

  return (
    <div className="min-h-full bg-gradient-to-b from-white to-brand-50">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5">
        <div className="flex items-center gap-2">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-sm font-bold text-white">
            Q
          </span>
          <span className="text-lg font-semibold">QuantLab AI</span>
        </div>
        <div className="flex items-center gap-2">
          {user ? (
            <button className="btn-primary" onClick={() => navigate("/app")}>
              进入工作台
            </button>
          ) : (
            <>
              <Link to="/login" className="btn-ghost">
                登录
              </Link>
              <Link to={registerHref} className="btn-primary">
                免费开始
              </Link>
            </>
          )}
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-4 pb-10 pt-12 text-center">
        {ref && (
          <p className="mb-4 inline-block rounded-full bg-brand-100 px-4 py-1 text-sm text-brand-700">
            🎉 你的朋友 <b>{ref}</b> 邀请你一起做量化研究
          </p>
        )}
        <h1 className="text-4xl font-bold leading-tight text-slate-900 sm:text-5xl">
          5 分钟完成你的第一次
          <span className="text-brand-600">量化研究</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-slate-600">
          QuantLab AI 是量化研究员孵化器。完全不懂代码也能从模板开始,
          跑回测、做科学验证、生成研究报告, 并把成果分享给世界。
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link to={user ? "/app" : registerHref} className="btn-primary px-6 py-3 text-base">
            {user ? "进入工作台" : "免费开始研究 →"}
          </Link>
          <Link to="/feed" className="btn-ghost px-6 py-3 text-base">
            看看大家在研究什么
          </Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-4 px-4 pb-16 sm:grid-cols-2 lg:grid-cols-4">
        {features.map((f) => (
          <div key={f.title} className="card">
            <h3 className="font-semibold text-slate-800">{f.title}</h3>
            <p className="mt-2 text-sm text-slate-500">{f.desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
