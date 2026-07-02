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
  if (!user.onboarding_done && location.pathname !== "/onboarding") {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
