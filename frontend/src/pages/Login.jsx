import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, guestLogin, getErrorMessage } from "../api";
import { useAuth } from "../AuthContext";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { signIn } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (!username.trim() || !password) {
      setError("Enter both a username and a password.");
      return;
    }

    setLoading(true);
    try {
      const { data } = await login(username.trim(), password);
      signIn(data.access_token);
      navigate("/chat");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

    async function handleGuest() {
    setError("");
    setLoading(true);
    try {
      const { data } = await guestLogin();
      signIn(data.access_token);
      navigate("/chat");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="auth-screen">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-card__mark" aria-hidden="true" />
        <h1 className="auth-card__title">Sign in to SpendSmart AI</h1>
        <p className="auth-card__subtitle">Sign in, or try the demo with no signup.</p>

        <label className="field">
          <span className="field__label">Username</span>
          <input
            className="field__input"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoFocus
          />
        </label>

        <label className="field">
          <span className="field__label">Password</span>
          <input
            className="field__input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>

        {error && <p className="form-error" role="alert">{error}</p>}

        <button className="button button--primary button--full" type="submit" disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>

        <button
          className="button button--secondary button--full"
          type="button"
          onClick={handleGuest}
          disabled={loading}
          style={{ marginTop: 10 }}
        >
          Try demo (5 free questions)
        </button>
      </form>
    </div>
  );
}
