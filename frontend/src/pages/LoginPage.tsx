import type { FormEvent } from "react";
import { useState } from "react";
import { login, type AuthUser } from "../api/client";
import { getErrorMessage } from "../error";

type LoginPageProps = {
  onLogin: (user: AuthUser) => void;
};

export function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin1234");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      setLoading(true);
      setError("");
      const result = await login(username, password);
      onLogin(result.user);
    } catch (error) {
      setError(getErrorMessage(error, "로그인에 실패했습니다."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <form className="login-panel" onSubmit={submit}>
        <div>
          <div className="brand">LOTOS AI Profit Approval System</div>
          <div className="subtitle">Sign in to continue</div>
        </div>
        {error && <div className="error-box">{error}</div>}
        <label className="field">
          <span>Username</span>
          <input value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? "로그인 중..." : "Login"}
        </button>
        <div className="meta-line">
          초기 계정: admin / admin1234
        </div>
      </form>
    </div>
  );
}
