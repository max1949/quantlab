import { useEffect, useId, useRef, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useLocale } from "../store/locale";
import LanguageSwitcher from "./LanguageSwitcher";
import ThemeSwitcher from "./ThemeSwitcher";
import { useLevelLabel } from "../i18n/useLevelLabel";

type NavItem = { to: string; label: string; auth?: boolean };
type ExternalLink = { href: string; label: string };

/**
 * Header capacity model (language-independent):
 * - Zone A Brand: shrink-0, stable width, never overlapped
 * - Zone B Primary: doctrine-critical IA only (Desk → Evidence → Paper → Projects → Challenge)
 * - Zone C More: secondary + external links (progressive disclosure, not overflow squeeze)
 * - Zone D Controls: theme/lang/user shrink-0 compact
 *
 * Root cause of EN overlap: every NavLink used shrink-0 + whitespace-nowrap inside a
 * flex-1 justify-center row, so English labels overflowed into Brand and Theme without
 * yielding width. Absolute positioning was NOT involved for Desk — it was flex overflow.
 */
export default function Layout() {
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const navigate = useNavigate();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [moreOpenMobile, setMoreOpenMobile] = useState(false);
  const t = useLocale((s) => s.dict);
  const levelName = useLevelLabel(user?.level ?? 0);
  const moreBtnId = useId();
  const morePanelId = useId();

  const primary: NavItem[] = user
    ? [
        { to: "/app", label: t.nav.workspace },
        { to: "/evidence", label: t.nav.evidenceOs || "证据系统" },
        { to: "/paper", label: t.nav.paperTrading || "模拟交易" },
        { to: "/projects", label: t.nav.myProjects },
        { to: "/challenges", label: t.nav.challenges },
      ]
    : [
        { to: "/feed", label: t.nav.feed },
        { to: "/leaderboards", label: t.nav.leaderboards },
        { to: "/pricing", label: t.nav.pricing },
      ];

  const secondary: NavItem[] = user
    ? [
        { to: "/feed", label: t.nav.feed },
        { to: "/leaderboards", label: t.nav.leaderboards },
        { to: "/orgs", label: t.nav.orgLibrary },
        { to: "/pricing", label: t.nav.pricing },
      ]
    : [];

  const external: ExternalLink[] = [
    { href: "https://ziyingke.com/", label: t.nav.aboutZiyingke },
    { href: "https://ai.ziyingke.com/", label: t.nav.decisionArena },
    { href: "https://t.ziyingke.com/", label: t.nav.tmos },
  ];

  const { pathname } = useLocation();
  const isHome = pathname === "/";
  const isAuthPage = pathname === "/login" || pathname === "/register";
  const moreActive = secondary.some(
    (i) => pathname === i.to || pathname.startsWith(`${i.to}/`),
  );

  return (
    <div className="flex min-h-full flex-col">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-950/90">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-2 px-2 sm:gap-3 sm:px-4">
          {/* Zone A — Brand (stable; never flex-shrink into nav) */}
          <Link
            to={user ? "/app" : "/"}
            className="flex min-w-0 shrink-0 items-center gap-1.5 sm:gap-2"
            aria-label={t.brand}
          >
            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-brand-600 text-sm font-bold text-white">
              Q
            </span>
            <span className="hidden max-w-[9.5rem] truncate text-base font-semibold tracking-tight text-slate-800 min-[380px]:inline sm:max-w-[11rem] sm:text-lg dark:text-slate-100">
              {t.brand}
            </span>
          </Link>

          {/* Zone B+C — Primary + More (desktop) */}
          <nav
            className="hidden min-w-0 flex-1 items-center gap-0.5 lg:flex"
            aria-label="Primary"
          >
            {primary.map((i) => (
              <HeaderNavLink key={i.to} to={i.to}>
                {i.label}
              </HeaderNavLink>
            ))}
            <MoreMenu
              open={moreOpen}
              setOpen={setMoreOpen}
              buttonId={moreBtnId}
              panelId={morePanelId}
              label={t.nav.more}
              active={moreActive}
              secondary={secondary}
              external={external}
            />
          </nav>

          {/* Zone D — Controls (always in top rail so mobile nav row stays clean) */}
          <div className="ml-auto flex shrink-0 items-center gap-1 sm:gap-2">
            <ThemeSwitcher compact />
            <LanguageSwitcher />
            {user ? (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => {
                    setUserMenuOpen((v) => !v);
                    setMoreOpen(false);
                  }}
                  className="flex max-w-[9rem] items-center gap-1 rounded-lg px-1 py-1 hover:bg-slate-100 sm:max-w-[12rem] sm:gap-1.5 sm:px-1.5 dark:hover:bg-slate-800"
                  aria-expanded={userMenuOpen}
                  aria-haspopup="menu"
                >
                  <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-brand-100 text-xs font-bold text-brand-700 dark:bg-brand-900 dark:text-brand-200">
                    {user.username.slice(0, 2).toUpperCase()}
                  </span>
                  <span className="hidden min-w-0 truncate text-sm font-medium md:inline">
                    {user.username}
                  </span>
                  <span className="badge hidden max-w-[4.5rem] truncate xl:inline">
                    {levelName}
                  </span>
                </button>
                {userMenuOpen ? (
                  <div
                    className="absolute right-0 z-40 mt-2 w-48 rounded-xl border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-700 dark:bg-slate-900"
                    role="menu"
                    onMouseLeave={() => setUserMenuOpen(false)}
                  >
                    <MenuLink to="/me" onClick={() => setUserMenuOpen(false)}>
                      {t.nav.myProfile}
                    </MenuLink>
                    <MenuLink to="/projects" onClick={() => setUserMenuOpen(false)}>
                      {t.nav.myProjects}
                    </MenuLink>
                    <MenuLink to="/evidence" onClick={() => setUserMenuOpen(false)}>
                      {t.nav.evidenceOs || "证据系统"}
                    </MenuLink>
                    <MenuLink to="/factor-scans" onClick={() => setUserMenuOpen(false)}>
                      {t.nav.factorScans || "参数扫描"}
                    </MenuLink>
                    <MenuLink to="/ai-strategy" onClick={() => setUserMenuOpen(false)}>
                      {t.nav.aiStrategyTool || "AI 研究工具"}
                    </MenuLink>
                    <MenuLink to="/me/following" onClick={() => setUserMenuOpen(false)}>
                      {t.nav.following}
                    </MenuLink>
                    <MenuLink to="/me/referral" onClick={() => setUserMenuOpen(false)}>
                      {t.nav.referral}
                    </MenuLink>
                    <button
                      type="button"
                      onClick={() => {
                        logout();
                        setUserMenuOpen(false);
                        navigate("/");
                      }}
                      className="block w-full px-4 py-2 text-left text-sm text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950"
                    >
                      {t.nav.logout}
                    </button>
                  </div>
                ) : null}
              </div>
            ) : (
              <>
                <Link to="/login" className="btn-ghost hidden sm:inline-flex">
                  {t.nav.login}
                </Link>
                <Link to="/register" className="btn-primary px-3 text-sm">
                  {t.nav.register}
                </Link>
              </>
            )}
          </div>
        </div>

        {/* Narrow / tablet / mobile — primary strip only (controls live in top rail) */}
        <div className="border-t border-slate-100 dark:border-slate-800 lg:hidden">
          <nav
            className="mx-auto flex max-w-7xl flex-wrap items-center gap-1 px-3 py-2 sm:px-4"
            aria-label="Primary mobile"
          >
            {primary.map((i) => (
              <HeaderNavLink key={i.to} to={i.to} dense>
                {i.label}
              </HeaderNavLink>
            ))}
            <MoreMenu
              open={moreOpenMobile}
              setOpen={setMoreOpenMobile}
              buttonId={`${moreBtnId}-m`}
              panelId={`${morePanelId}-m`}
              label={t.nav.more}
              active={moreActive}
              secondary={secondary}
              external={external}
              dense
            />
          </nav>
        </div>
      </header>

      <main
        className={
          isHome
            ? "flex-1"
            : isAuthPage
              ? "mx-auto flex w-full min-w-0 max-w-6xl flex-1 flex-col px-4 py-6"
              : "mx-auto w-full min-w-0 max-w-6xl flex-1 px-4 py-6"
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

function HeaderNavLink({
  to,
  children,
  dense,
}: {
  to: string;
  children: React.ReactNode;
  dense?: boolean;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `relative z-0 whitespace-nowrap rounded-lg font-medium transition ${
          dense ? "px-2.5 py-1.5 text-sm" : "px-2.5 py-1.5 text-sm"
        } ${
          isActive
            ? "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
            : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
        }`
      }
    >
      {children}
    </NavLink>
  );
}

function MoreMenu({
  open,
  setOpen,
  buttonId,
  panelId,
  label,
  active,
  secondary,
  external,
  dense,
}: {
  open: boolean;
  setOpen: (v: boolean | ((b: boolean) => boolean)) => void;
  buttonId: string;
  panelId: string;
  label: string;
  active: boolean;
  secondary: NavItem[];
  external: ExternalLink[];
  dense?: boolean;
}) {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, setOpen]);

  if (secondary.length === 0 && external.length === 0) return null;

  return (
    <div className="relative" ref={rootRef}>
      <button
        type="button"
        id={buttonId}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
        className={`whitespace-nowrap rounded-lg font-medium ${
          dense ? "px-2.5 py-1.5 text-sm" : "px-2.5 py-1.5 text-sm"
        } ${
          open || active
            ? "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
            : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
        }`}
      >
        {label}
        <span className="ml-1 inline-block text-[10px] opacity-70" aria-hidden>
          ▾
        </span>
      </button>
      {open ? (
        <div
          id={panelId}
          role="menu"
          aria-labelledby={buttonId}
          className="absolute left-0 z-40 mt-2 min-w-[12rem] rounded-xl border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-700 dark:bg-slate-900"
        >
          {secondary.map((i) => (
            <Link
              key={i.to}
              to={i.to}
              role="menuitem"
              onClick={() => setOpen(false)}
              className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              {i.label}
            </Link>
          ))}
          {secondary.length > 0 && external.length > 0 ? (
            <div className="my-1 border-t border-slate-100 dark:border-slate-800" />
          ) : null}
          {external.map((link) => (
            <a
              key={link.href}
              href={link.href}
              target="_blank"
              rel="noopener noreferrer"
              role="menuitem"
              onClick={() => setOpen(false)}
              className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              {link.label}
            </a>
          ))}
        </div>
      ) : null}
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
      role="menuitem"
      onClick={onClick}
      className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:text-slate-200 dark:hover:bg-slate-800"
    >
      {children}
    </Link>
  );
}
