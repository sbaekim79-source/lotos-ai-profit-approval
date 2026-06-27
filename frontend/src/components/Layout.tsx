import { useState, type ReactNode } from "react";
import { changePassword, type AuthUser } from "../api/client";
import { getErrorMessage } from "../error";

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

type LayoutProps = {
  activePage: Page;
  onNavigate: (page: Page) => void;
  user: AuthUser;
  onLogout: () => void;
  children: ReactNode;
};

const navItems: Array<{ id: Page; label: string }> = [
  { id: "dashboard", label: "Dashboard" },
  { id: "monthly", label: "Monthly" },
  { id: "upload", label: "Upload" },
  { id: "approvals", label: "Approvals" },
  { id: "quotes", label: "Quotes" },
  { id: "workflows", label: "Workflows" },
  { id: "operation-tests", label: "Operation Test" },
  { id: "masters", label: "Masters" },
  { id: "help", label: "Help" },
  { id: "admin", label: "Admin" },
];

export function Layout({ activePage, onNavigate, user, onLogout, children }: LayoutProps) {
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const role = user.role;

  async function submitPasswordChange() {
    try {
      setPasswordMessage("");
      await changePassword(currentPassword, newPassword);
      setPasswordMessage("비밀번호가 변경되었습니다.");
      setCurrentPassword("");
      setNewPassword("");
      setShowPasswordForm(false);
    } catch (error) {
      setPasswordMessage(getErrorMessage(error, "비밀번호 변경 실패"));
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <div className="brand">LOTOS AI Profit Approval System</div>
          <div className="subtitle">Profit Sheet approval workflow</div>
        </div>
        <nav className="nav-tabs" aria-label="Main navigation">
          {navItems
            .filter((item) => item.id !== "admin" || role === "ADMIN")
            .map((item) => (
            <button
              key={item.id}
              className={activePage === item.id ? "nav-tab active" : "nav-tab"}
              onClick={() => onNavigate(item.id)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="user-box">
          <div>
            <strong>{user.display_name}</strong>
            <span>{user.role}</span>
          </div>
          <button type="button" className="secondary-button" onClick={() => setShowPasswordForm((value) => !value)}>
            비밀번호 변경
          </button>
          <button type="button" className="secondary-button" onClick={onLogout}>
            로그아웃
          </button>
        </div>
      </header>
      {showPasswordForm && (
        <section className="password-panel">
          <label className="field">
            <span>Current Password</span>
            <input
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
            />
          </label>
          <label className="field">
            <span>New Password</span>
            <input
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
            />
          </label>
          <button type="button" onClick={submitPasswordChange}>
            변경
          </button>
          {passwordMessage && <div className="meta-line">{passwordMessage}</div>}
        </section>
      )}
      <main className="page">{children}</main>
    </div>
  );
}
