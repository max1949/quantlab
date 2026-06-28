import { useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";

const navItems = [
  { to: "/app", label: "工作台", auth: true },
  { to: "/feed", label: "研究广场", auth: false },
  { to: "/leaderboards", label: "榜单", auth: false },
  { to: "/challenges", label: "30天挑战", auth: true },
];

export default function Layout() {
  const user = useAuth((s) => s.user);
  const logout = useAuth((s) => s.logout);
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const items = navItems.filter((i) => !i.auth || user);

  return (
    <div className="flex min-h-full flex-col">
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to={user ? "/app" : "/"} className="flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-600 text-sm font-bold text-white">
              Q
            </span>
            <span className="text-lg font-semibold text-slate-800">
              QuantLab AI
            </span>
          </Link>

          <nav className="hidden items-center gap-1 md:flex">
            {items.map((i) => (
              <NavLink
                key={i.to}
                to={i.to}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-1.5 text-sm font-medium ${
                    isActive
                      ? "bg-brand-50 text-brand-700"
                      : "text-slate-600 hover:bg-slate-100"
                  }`
                }
              >
                {i.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setMenuOpen((v) => !v)}
                  className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-slate-100"
                >
                  <span className="grid h-7 w-7 place-items-center rounded-full bg-brand-100 text-xs font-bold text-brand-700">
                    {user.username.slice(0, 2).toUpperCase()}
                  </span>
                  <span className="hidden text-sm font-medium sm:inline">
                    {user.username}
                  </span>
                  <span className="badge">{user.level_label}</span>
                </button>
                {menuOpen && (
                  <div
                    className="absolute right-0 mt-2 w-44 rounded-xl border border-slate-200 bg-white py-1 shadow-lg"
                    onMouseLeave={() => setMenuOpen(false)}
                  >
                    <MenuLink to="/me" onClick={() => setMenuOpen(false)}>
                      我的主页
                    </MenuLink>
                    <MenuLink to="/projects" onClick={() => setMenuOpen(false)}>
                      我的项目
                    </MenuLink>
                    <MenuLink to="/me/following" onClick={() => setMenuOpen(false)}>
                      关注动态
                    </MenuLink>
                    <MenuLink to="/me/referral" onClick={() => setMenuOpen(false)}>
                      邀请好友
                    </MenuLink>
                    <button
                      onClick={() => {
                        logout();
                        setMenuOpen(false);
                        navigate("/");
                      }}
                      className="block w-full px-4 py-2 text-left text-sm text-rose-600 hover:bg-rose-50"
                    >
                      退出登录
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <>
                <Link to="/login" className="btn-ghost">
                  登录
                </Link>
                <Link to="/register" className="btn-primary">
                  免费注册
                </Link>
              </>
            )}
          </div>
        </div>

        {/* 移动端导航 */}
        <nav className="flex gap-1 overflow-x-auto border-t border-slate-100 px-4 py-2 md:hidden">
          {items.map((i) => (
            <NavLink
              key={i.to}
              to={i.to}
              className={({ isActive }) =>
                `whitespace-nowrap rounded-lg px-3 py-1.5 text-sm ${
                  isActive ? "bg-brand-50 text-brand-700" : "text-slate-600"
                }`
              }
            >
              {i.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-400">
        QuantLab AI · 量化研究员孵化器 · 研究过程重于结果
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
      className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-50"
    >
      {children}
    </Link>
  );
}
