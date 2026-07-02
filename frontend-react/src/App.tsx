import { useEffect } from "react";
import { Route, Routes, useNavigate } from "react-router-dom";
import { setUnauthorizedHandler } from "./api/client";
import { useAuth } from "./store/auth";
import { useLocale } from "./store/locale";
import { useTheme } from "./store/theme";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Toasts from "./components/Toasts";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Onboarding from "./pages/Onboarding";
import Dashboard from "./pages/Dashboard";
import Templates from "./pages/Templates";
import Projects from "./pages/Projects";
import ProjectDetail from "./pages/ProjectDetail";
import ReportDetail from "./pages/ReportDetail";
import SharePage from "./pages/SharePage";
import Feed from "./pages/Feed";
import Researcher from "./pages/Researcher";
import MyProfile from "./pages/MyProfile";
import Referral from "./pages/Referral";
import Following from "./pages/Following";
import Leaderboards from "./pages/Leaderboards";
import Challenges from "./pages/Challenges";
import Pricing from "./pages/Pricing";
import NotFound from "./pages/NotFound";

export default function App() {
  const refreshMe = useAuth((s) => s.refreshMe);
  const ready = useAuth((s) => s.ready);
  const navigate = useNavigate();
  const loadingText = useLocale((s) => s.dict.loading);
  const initTheme = useTheme((s) => s.init);

  useEffect(() => {
    initTheme();
    setUnauthorizedHandler(() => navigate("/login"));
    void refreshMe();
  }, [refreshMe, navigate, initTheme]);

  if (!ready) {
    return (
      <div className="flex h-full items-center justify-center text-slate-400">
        {loadingText}
      </div>
    );
  }

  return (
    <>
      <Routes>
        <Route path="/share/:token" element={<SharePage />} />

        {/* 带顶栏：未登录也能看到完整导航 */}
        <Route element={<Layout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/feed" element={<Feed />} />
          <Route path="/reports/:id" element={<ReportDetail />} />
          <Route path="/u/:userId" element={<Researcher />} />
          <Route path="/leaderboards" element={<Leaderboards />} />
          <Route path="/pricing" element={<Pricing />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/app" element={<Dashboard />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/challenges" element={<Challenges />} />
            <Route path="/me" element={<MyProfile />} />
            <Route path="/me/referral" element={<Referral />} />
            <Route path="/me/following" element={<Following />} />
          </Route>
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
      <Toasts />
    </>
  );
}
