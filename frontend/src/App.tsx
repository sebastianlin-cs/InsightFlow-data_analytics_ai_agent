import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactElement } from "react";
import { getToken } from "./api/client";
import { Layout } from "./components/Layout";
import { AgentChatPage } from "./pages/AgentChatPage";
import { DatasetDetailPage } from "./pages/DatasetDetailPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { WorkspacePage } from "./pages/WorkspacePage";

function RequireAuth({ children }: { children: ReactElement }) {
  if (!getToken()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function DefaultRoute() {
  return <Navigate to={getToken() ? "/workspace" : "/login"} replace />;
}

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<DefaultRoute />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/workspace" element={<RequireAuth><WorkspacePage /></RequireAuth>} />
        <Route path="/datasets/:datasetId" element={<RequireAuth><DatasetDetailPage /></RequireAuth>} />
        <Route path="/sessions/:sessionId" element={<RequireAuth><AgentChatPage /></RequireAuth>} />
        <Route path="*" element={<DefaultRoute />} />
      </Route>
    </Routes>
  );
}
