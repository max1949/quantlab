import { useEffect } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import { trackEvent } from "../api/endpoints";

export default function Landing() {
  const user = useAuth((s) => s.user);
  const [params] = useSearchParams();
  const ref = params.get("ref");
  const l = useLocale((s) => s.dict.landing);

  useEffect(() => {
    void trackEvent("landing_view", { ref });
  }, [ref]);

  const registerHref = ref ? `/register?ref=${encodeURIComponent(ref)}` : "/register";

  const features = [
    { title: l.step1Title, desc: l.step1Desc },
    { title: l.step2Title, desc: l.step2Desc },
    { title: l.step3Title, desc: l.step3Desc },
    { title: l.step4Title, desc: l.step4Desc },
    { title: l.step5Title, desc: l.step5Desc, href: "/leaderboards?kind=paper_mastery" },
  ];

  return (
    <div className="-mx-4 -mt-6 bg-gradient-to-b from-white to-brand-50 dark:from-slate-950 dark:to-slate-900 sm:-mx-0 sm:mt-0">
      <section className="mx-auto max-w-4xl px-4 pb-10 pt-12 text-center">
        {ref && (
          <p className="mb-4 inline-block rounded-full bg-brand-100 px-4 py-1 text-sm text-brand-700 dark:bg-brand-900 dark:text-brand-200">
            🎉 {l.invited(ref)}
          </p>
        )}
        <h1 className="text-4xl font-bold leading-tight text-slate-900 dark:text-slate-100 sm:text-5xl">
          {l.heroTitle}
          <span className="text-brand-600"> {l.heroHighlight}</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg text-slate-600 dark:text-slate-400">
          {l.heroDesc}
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link to={user ? "/app" : registerHref} className="btn-primary px-6 py-3 text-base">
            {user ? l.ctaWork : `${l.cta} →`}
          </Link>
          <Link to="/leaderboards?kind=paper_mastery" className="btn px-6 py-3 text-base">
            {l.ctaMasters} →
          </Link>
          <Link to="/feed" className="btn-ghost px-6 py-3 text-base">
            {l.ctaBrowse}
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-4 pb-10">
        <div className="card border border-emerald-200 bg-gradient-to-r from-emerald-50/80 to-brand-50/40 dark:border-emerald-900 dark:from-emerald-950/30 dark:to-brand-950/20">
          <p className="text-center text-lg font-semibold text-emerald-900 dark:text-emerald-100">
            {l.masteryPathTitle}
          </p>
          <p className="mt-2 text-center text-sm text-slate-600 dark:text-slate-300">{l.masteryPathDesc}</p>
          <p className="mt-4 text-center text-xs font-medium tracking-wide text-brand-700 dark:text-brand-300">
            {l.masteryPathChain}
          </p>
          <div className="mt-4 flex justify-center">
            <Link
              to={user ? "/app" : registerHref}
              className="btn-primary text-sm"
            >
              {user ? l.ctaWork : `${l.cta} →`}
            </Link>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-5xl gap-4 px-4 pb-16 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {features.map((f) => {
          const inner = (
            <>
              <h3 className="font-semibold text-slate-800 dark:text-slate-100">{f.title}</h3>
              <p className="mt-2 text-sm text-slate-500">{f.desc}</p>
            </>
          );
          if ("href" in f && f.href) {
            return (
              <Link
                key={f.title}
                to={f.href}
                className="card transition hover:border-brand-300 hover:shadow-md dark:hover:border-brand-700"
              >
                {inner}
              </Link>
            );
          }
          return (
            <div key={f.title} className="card">
              {inner}
            </div>
          );
        })}
      </section>
    </div>
  );
}
