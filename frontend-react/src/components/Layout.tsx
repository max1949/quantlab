import { useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import LanguageSwitcher from "./LanguageSwitcher";
import ThemeSwitcher from "./ThemeSwitcher";
import { useLevelLabel } from "../i18n/useLevelLabel";

const EXTERNAL = [
  { href: "https://ziyingke.com/", key: "aboutZiyingke" as const },
  { href: "https://ai.ziyingke.com/", key: "decisionArena" as const },
];

export default function Layout() {
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const t = useLocale((s) => s.dict);
  const levelName = useLevelLabel(user?.level ?? 0);

  const navItems = [
    { to: "/app", label: t.nav.workspace, auth: true },
    { to: "/feed", label: t.nav.feed, auth: false },
    { to: "/leaderboards", label: t.nav.leaderboards, auth: false },
    { to: "/challenges", label: t.nav.challenges, auth: true },
    { to: "/pricing", label: t.nav.pricing, auth: false },
  ];

  const items = navItems.filter((i) => !i.auth || user);
  const { pathname } = useLocation();
  const isHome = pathname === "/";
  const isAuthPage = pathname === "/login" || pathname === "/register";

  return (
    <div className="flex min-h-full flex-col">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-2 px-3 py-3 sm:px-4">
          <Link to={user ? "/app" : "/"} className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-sm font-bold text-white">
              Q
            </span>
            <span className="text-lg font-semibold text-slate-800 dark:text-slate-100">
              {t.brand}
            </span>
          </Link>

          <nav className="hidden min-w-0 flex-1 items-center justify-center gap-0.5 lg:flex">
            {items.map((i) => (
              <NavLink
                key={i.to}
                to={i.to}
                className={({ isActive }) =>
                  `shrink-0 whitespace-nowrap rounded-lg px-2 py-1.5 text-xs font-medium sm:px-2.5 sm:text-sm ${
                    isActive
                      ? "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  }`
                }
              >
                {i.label}
              </NavLink>
            ))}
            {EXTERNAL.map((link) => (
              <a
                key={link.href}
                href={link.href}
                target="_blank"
                rel="noopener noreferrer"
                className="shrink-0 whitespace-nowrap rounded-lg px-2 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 sm:px-2.5 sm:text-sm"
              >
                {t.nav[link.key]}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <div className="hidden sm:flex sm:items-center sm:gap-2">
              <ThemeSwitcher />
              <LanguageSwitcher />
            </div>
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setMenuOpen((v) => !v)}
                  className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-brand-100 text-xs font-bold text-brand-700 dark:bg-brand-900 dark:text-brand-200">
                    {user.username.slice(0, 2).toUpperCase()}
                  </span>
                  <span className="hidden text-sm font-medium sm:inline">
                    {user.username}
                  </span>
                  {user && (
                    <span className="badge hidden max-w-[5.5rem] truncate whitespace-nowrap sm:inline">
                      {levelName}
                    </span>
                  )}
                </button>
                {menuOpen && (
                  <div
                    className="absolute right-0 mt-2 w-44 rounded-xl border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-700 dark:bg-slate-900"
                    onMouseLeave={() => setMenuOpen(false)}
                  >
                    <MenuLink to="/me" onClick={() => setMenuOpen(false)}>
                      {t.nav.myProfile}
                    </MenuLink>
                    <MenuLink to="/projects" onClick={() => setMenuOpen(false)}>
                      {t.nav.myProjects}
                    </MenuLink>
                    <MenuLink to="/experiments" onClick={() => setMenuOpen(false)}>
                      {t.nav.myExperiments}
                    </MenuLink>
                    <MenuLink to="/me/following" onClick={() => setMenuOpen(false)}>
                      {t.nav.following}
                    </MenuLink>
                    <MenuLink to="/me/referral" onClick={() => setMenuOpen(false)}>
                      {t.nav.referral}
                    </MenuLink>
                    <button
                      onClick={() => {
                        logout();
                        setMenuOpen(false);
                        navigate("/");
                      }}
                      className="block w-full px-4 py-2 text-left text-sm text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950"
                    >
                      {t.nav.logout}
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <Link to="/login" className="btn-ghost hidden sm:inline-flex">
                  {t.nav.login}
                </Link>
                <Link to="/register" className="btn-primary">
                  {t.nav.register}
                </Link>
              </>
            )}
          </div>
        </div>

        <nav className="flex gap-1 overflow-x-auto border-t border-slate-100 px-4 py-2 dark:border-slate-800 lg:hidden">
          {items.map((i) => (
            <NavLink
              key={i.to}
              to={i.to}
              className={({ isActive }) =>
                `shrink-0 whitespace-nowrap rounded-lg px-3 py-1.5 text-sm ${
                  isActive
                    ? "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
                    : "text-slate-600 dark:text-slate-300"
                }`
              }
            >
              {i.label}
            </NavLink>
          ))}
          {EXTERNAL.map((link) => (
            <a
              key={link.href}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 whitespace-nowrap rounded-lg px-3 py-1.5 text-sm text-slate-600 dark:text-slate-300"
            >
              {t.nav[link.key]}
            </a>
          ))}
          <div className="ml-auto flex shrink-0 items-center gap-2">
            <ThemeSwitcher />
            <LanguageSwitcher />
          </div>
        </nav>
      </header>

      <main
        className={
          isHome
            ? "flex-1"
            : isAuthPage
              ? "mx-auto flex w-full max-w-6xl flex-1 flex-col px-4 py-6"
              : "mx-auto w-full max-w-6xl flex-1 px-4 py-6"
        }
      >
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-400 dark:border-slate-800">
        {t.footer}
      </footer>
    </div>
  );
}

function MenuLink({
  to,
  children,
  onClick,
}: {
  to: string;
  children: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
    >
      {children}
    </Link>
  );
}
