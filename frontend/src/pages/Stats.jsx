import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getStats, getErrorMessage } from "../api";

// One color per thing, everywhere: small = teal, big = amber, cache = blue.
// (Checked for color-blind safety on the dark background.)
const COLORS = {
  small: "#2aa392",
  big: "#c8831f",
  cache: "#7088c8",
  grid: "#2a373d",
  text: "#8fa0a6",
  surface: "#161f23",
};

const tooltipStyle = {
  background: "#1d282d",
  border: "1px solid #2a373d",
  borderRadius: 6,
  color: "#e9edee",
  fontSize: 13,
};

const money = (n, digits = 6) => `$${Number(n).toFixed(digits)}`;

// Axis shows "Mon", "Tue"... (fits on a phone). The tooltip shows the full date.
function weekday(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString(undefined, { weekday: "short" });
}

function fullDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

// Tooltip title: use the full date instead of the short axis label.
const tooltipTitle = (label, payload) => payload?.[0]?.payload?.full ?? label;

function StatCard({ label, value, hint, accent }) {
  return (
    <div className={"stat-card" + (accent ? " stat-card--accent" : "")}>
      <span className="stat-card__label">{label}</span>
      <span className="stat-card__value">{value}</span>
      {hint && <span className="stat-card__hint">{hint}</span>}
    </div>
  );
}

function ChartCard({ title, subtitle, children }) {
  return (
    <section className="chart-card">
      <h2 className="chart-card__title">{title}</h2>
      <p className="chart-card__subtitle">{subtitle}</p>
      <div className="chart-card__plot">{children}</div>
    </section>
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

  const days = stats.daily.map((d) => ({ ...d, label: weekday(d.date), full: fullDate(d.date) }));
  const used = Math.min(100, Math.round(stats.budget_used_percent));
  const budgetState = used >= 100 ? "full" : used >= stats.budget_warn_percent ? "warn" : "ok";

  return (
    <div className="stats-page">
      <div className="stats-header">
        <h1>Usage &amp; cost</h1>
        <button className="button button--secondary" onClick={load}>Refresh</button>
      </div>

      <div className="stat-grid">
        <StatCard label="Total requests" value={stats.total_requests} hint={`${stats.small_calls} small · ${stats.big_calls} big`} />
        <StatCard label="Cache hits" value={stats.cache_hits} hint={`${Math.round(stats.cache_hit_rate * 100)}% of requests`} />
        <StatCard label="Escalated to big" value={stats.retries} hint="small model wasn't confident" />
        <StatCard label="Total tokens" value={stats.total_tokens.toLocaleString()} />
        <StatCard label="Estimated cost" value={money(stats.total_cost_usd)} hint={`${money(stats.baseline_cost_usd)} if always big`} />
        <StatCard
          label="Saved vs always-big"
          value={`${Math.round(stats.saved_pct * 100)}%`}
          hint={`routing ${money(stats.saved_by_routing_usd)} · cache ${money(stats.saved_by_cache_usd)}`}
          accent
        />
      </div>

      {stats.total_requests === 0 ? (
        <p className="muted">No data yet. Ask a few questions in Chat, then come back to see the charts.</p>
      ) : (
        <>
          <div className="charts-grid">
            <ChartCard title="Requests per day" subtitle="Where each question was answered, last 7 days">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={days} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                  <CartesianGrid stroke={COLORS.grid} vertical={false} />
                  <XAxis dataKey="label" tick={{ fill: COLORS.text, fontSize: 12 }} axisLine={{ stroke: COLORS.grid }} tickLine={false} />
                  <YAxis allowDecimals={false} tick={{ fill: COLORS.text, fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} labelFormatter={tooltipTitle} />
                  <Legend wrapperStyle={{ fontSize: 12, color: COLORS.text }} />
                  <Bar dataKey="small_calls" name="Small model" stackId="a" fill={COLORS.small} stroke={COLORS.surface} strokeWidth={2} isAnimationActive={false} />
                  <Bar dataKey="big_calls" name="Big model" stackId="a" fill={COLORS.big} stroke={COLORS.surface} strokeWidth={2} isAnimationActive={false} />
                  <Bar dataKey="cache_hits" name="Cache" stackId="a" fill={COLORS.cache} stroke={COLORS.surface} strokeWidth={2} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Cost per day" subtitle="What you paid vs. what always using the big model would cost">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={days} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
                  <CartesianGrid stroke={COLORS.grid} vertical={false} />
                  <XAxis dataKey="label" tick={{ fill: COLORS.text, fontSize: 12 }} axisLine={{ stroke: COLORS.grid }} tickLine={false} />
                  <YAxis tickFormatter={(v) => money(v, 4)} width={64} tick={{ fill: COLORS.text, fontSize: 12 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.04)" }} formatter={(v) => money(v)} labelFormatter={tooltipTitle} />
                  <Legend wrapperStyle={{ fontSize: 12, color: COLORS.text }} />
                  <Bar dataKey="cost_usd" name="Actual cost" fill={COLORS.small} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                  <Bar dataKey="baseline_usd" name="If always big" fill={COLORS.big} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          <details className="table-view">
            <summary>View the same data as a table</summary>
            <div className="table-view__scroll">
              <table>
                <thead>
                  <tr>
                    <th>Day</th><th>Small</th><th>Big</th><th>Cache</th><th>Actual cost</th><th>If always big</th>
                  </tr>
                </thead>
                <tbody>
                  {days.map((d) => (
                    <tr key={d.date}>
                      <td>{d.full}</td><td>{d.small_calls}</td><td>{d.big_calls}</td><td>{d.cache_hits}</td>
                      <td>{money(d.cost_usd)}</td><td>{money(d.baseline_usd)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </>
      )}

      <div className="budget-panel">
        <div className="budget-panel__header">
          <span>Today's budget</span>
          <span>{money(stats.today_cost_usd)} of {money(stats.daily_budget_usd, 4)}</span>
        </div>
        <div className="budget-bar">
          <div className={"budget-bar__fill budget-bar__fill--" + budgetState} style={{ width: `${used}%` }} />
        </div>
        <p className="muted">
          {budgetState === "full"
            ? "Budget reached for today. New requests use the small model automatically."
            : budgetState === "warn"
            ? `${used}% used. At 100%, requests switch to the small model.`
            : `${money(stats.budget_remaining_usd)} left before requests switch to the small model.`}
        </p>
      </div>
    </div>
  );
}