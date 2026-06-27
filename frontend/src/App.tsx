import { useEffect, useState } from "react";
import {
  clearAuthSession,
  getAccessToken,
  getCurrentRole,
  getMe,
  getStoredAuthUser,
  type AuthUser,
} from "./api/client";
import { AdminPage } from "./pages/AdminPage";
import { Layout } from "./components/Layout";
import { DashboardPage } from "./pages/DashboardPage";
import { UploadPage } from "./pages/UploadPage";
import { ApprovalListPage } from "./pages/ApprovalListPage";
import { MasterPage } from "./pages/MasterPage";
import { MonthlyPerformancePage } from "./pages/MonthlyPerformancePage";
import { QuotePage } from "./pages/QuotePage";
import { WorkflowPage } from "./pages/WorkflowPage";
import { OperationTestPage } from "./pages/OperationTestPage";
import { LoginPage } from "./pages/LoginPage";
import { HelpPage } from "./pages/HelpPage";

type Page =
  | "dashboard"
  | "monthly"
  | "upload"
  | "approvals"
  | "quotes"
  | "workflows"
  | "operation-tests"
  | "masters"
  | "help"
  | "admin";

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [role, setRole] = useState(getCurrentRole());
  const [user, setUser] = useState<AuthUser | null>(getStoredAuthUser());
  const [checkingSession, setCheckingSession] = useState(Boolean(getAccessToken()));

  useEffect(() => {
    function handleUserChange() {
      const nextRole = getCurrentRole();
      setRole(nextRole);
      if (nextRole !== "ADMIN" && page === "admin") {
        setPage("dashboard");
      }
    }
    window.addEventListener("lotos-user-change", handleUserChange);
    return () => window.removeEventListener("lotos-user-change", handleUserChange);
  }, [page]);

  useEffect(() => {
    async function restoreSession() {
      if (!getAccessToken()) {
        setCheckingSession(false);
        return;
      }
      try {
        const currentUser = await getMe();
        setUser(currentUser);
        setRole(currentUser.role);
      } catch {
        clearAuthSession();
        setUser(null);
      } finally {
        setCheckingSession(false);
      }
    }
    restoreSession();
  }, []);

  function handleLogout() {
    clearAuthSession();
    setUser(null);
    setPage("dashboard");
    window.dispatchEvent(new CustomEvent("lotos-user-change"));
  }

  if (checkingSession) {
    return <div className="login-page"><div className="login-panel">세션 확인 중...</div></div>;
  }

  if (!user) {
    return <LoginPage onLogin={(nextUser) => {
      setUser(nextUser);
      setRole(nextUser.role);
      window.dispatchEvent(new CustomEvent("lotos-user-change"));
    }} />;
  }

  return (
    <Layout activePage={page} onNavigate={setPage} user={user} onLogout={handleLogout}>
      {page === "dashboard" && <DashboardPage />}
      {page === "monthly" && <MonthlyPerformancePage />}
      {page === "upload" && <UploadPage />}
      {page === "approvals" && <ApprovalListPage />}
      {page === "quotes" && <QuotePage />}
      {page === "workflows" && <WorkflowPage />}
      {page === "operation-tests" && <OperationTestPage />}
      {page === "masters" && <MasterPage />}
      {page === "help" && <HelpPage />}
      {page === "admin" && role === "ADMIN" && <AdminPage />}
    </Layout>
  );
}
