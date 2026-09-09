import { useEffect, useState } from "react";
import { getStats, getErrorMessage } from "../api";

function StatCard({ label, value, accent }) {
  return (
    <div className={"stat-card" + (accent ? " stat-card--accent" : "")}>
      <span className="stat-card__label">{label}</span>
      <span className="stat-card__value">{value}</span>
    </div>
  );
}

export default function Stats() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const { data } = await getStats();
      setStats(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return <div className="stats-page"><p className="muted">Loading stats...</p></div>;
  }

  if (error) {
    return (
      <div className="stats-page">
        <p className="form-error" role="alert">{error}</p>
        <button className="button button--secondary" onClick={load}>Try again</button>
      </div>
    );
  }

  const budgetUsedPct = stats.daily_budget_usd
    ? Math.min(100, Math.round((stats.today_cost_usd / stats.daily_budget_usd) * 100))
    : 0;

  return (
    <div className="stats-page">
      <div className="stats-header">
        <h1>Usage &amp; cost</h1>
        <button className="button button--secondary" onClick={load}>Refresh</button>
      </div>

      <div className="stat-grid">
        <StatCard label="Total requests" value={stats.total_requests} />
        <StatCard label="Cache hits" value={`${stats.cache_hits} (${Math.round(stats.cache_hit_rate * 100)}%)`} />
        <StatCard label="Total tokens" value={stats.total_tokens.toLocaleString()} />
        <StatCard label="Total est. cost" value={`$${stats.total_cost_usd.toFixed(4)}`} />
        <StatCard label="Saved by cache" value={`$${stats.cost_saved_by_cache_usd.toFixed(4)}`} accent />
        <StatCard label="Spent today" value={`$${stats.today_cost_usd.toFixed(4)}`} />
      </div>

      <div className="budget-panel">
        <div className="budget-panel__header">
          <span>Today's budget</span>
          <span>
            ${stats.today_cost_usd.toFixed(4)} of ${stats.daily_budget_usd.toFixed(2)}
          </span>
        </div>
        <div className="budget-bar">
          <div
            className={"budget-bar__fill" + (budgetUsedPct >= 100 ? " budget-bar__fill--full" : "")}
            style={{ width: `${budgetUsedPct}%` }}
          />
        </div>
        <p className="muted">
          {budgetUsedPct >= 100
            ? "Budget reached for today - new requests are routed to the lightweight model automatically."
            : `$${stats.budget_remaining_usd.toFixed(4)} remaining before requests get downgraded.`}
        </p>
      </div>
    </div>
  );
}
