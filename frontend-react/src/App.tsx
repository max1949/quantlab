import { useEffect } from "react";
import { Route, Routes, useNavigate } from "react-router-dom";
import { setUnauthorizedHandler } from "./api/client";
import { useAuth } from "./store/auth";
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
import NotFound from "./pages/NotFound";

export default function App() {
  const refreshMe = useAuth((s) => s.refreshMe);
  const ready = useAuth((s) => s.ready);
  const navigate = useNavigate();

  useEffect(() => {
    setUnauthorizedHandler(() => navigate("/login"));
    void refreshMe();
  }, [refreshMe, navigate]);

  if (!ready) {
    return (
      <div className="flex h-full items-center justify-center text-slate-400">
        加载中…
      </div>
    );
  }

  return (
    <>
      <Routes>
        {/* 公开层 */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/share/:token" element={<SharePage />} />

        {/* 带顶栏的页面 (公开可看 + 登录可看) */}
        <Route element={<Layout />}>
          <Route path="/feed" element={<Feed />} />
          <Route path="/u/:userId" element={<Researcher />} />
          <Route path="/leaderboards" element={<Leaderboards />} />

          {/* 受保护层 */}
          <Route element={<ProtectedRoute />}>
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="/app" element={<Dashboard />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:id" element={<ProjectDetail />} />
            <Route path="/reports/:id" element={<ReportDetail />} />
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
