import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../store/auth";

// 登录守卫 + onboarding 强制引导。
export default function ProtectedRoute() {
  const user = useAuth((s) => s.user);
  const location = useLocation();

  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location.pathname + location.search }}
      />
    );
  }

  // 未完成分流的用户, 强制去 onboarding (onboarding 页本身放行)。
  // 机构邀请链路：允许先接受邀请 / 查看团队页，再走新手分流。
  const onboardingExempt =
    location.pathname === "/onboarding" ||
    location.pathname.startsWith("/org-invite/") ||
    location.pathname.startsWith("/orgs/");

  if (!user.onboarding_done && !onboardingExempt) {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
