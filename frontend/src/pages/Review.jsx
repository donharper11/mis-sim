/* eslint-disable react/prop-types */
import { useEffect, useState } from "react";
import { apiClient } from "../api/client.js";
import { StatusBadge } from "../components/index.js";

function money(value) {
  return typeof value === "number" && Number.isFinite(value) ? `$${value.toLocaleString()}` : "—";
}

export default function Review({ data, instanceId }) {
  const [view, setView] = useState(data);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => setView(data), [data]);
  const team = view?.team;
  if (!team) return <section className="components-empty"><h2>Your team has not entered the runtime yet</h2><p>Review will appear here after the team runtime is initialized.</p></section>;
  async function lockRound() {
    if (team.revision === null || team.locked_revision !== null) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.post(`/instances/${instanceId}/review/lock`, { expected_revision: team.revision });
      setView(response.data);
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The round could not be locked.");
    } finally { setSaving(false); }
  }
  const locked = team.locked_revision !== null || team.status === "locked";
  return <div className="review-page">
    <section className="components-context"><div><p className="eyebrow">What you are committing to this round</p><p className="components-muted">{team.name} · Round {team.current_round}</p></div></section>
    {locked && <section className="review-banner"><strong>This round is locked.</strong><span>Decisions reopen when the round advances.</span></section>}
    <section className="review-table"><div className="components-panel-heading"><div><h2>Decision sheet</h2><p className="components-muted">Every decision this round, grouped by category</p></div>{locked ? <StatusBadge status="complete" label="Locked" /> : <StatusBadge status="partly-done" label="Draft" />}</div><div className="detail-table-wrap"><table className="detail-table"><thead><tr><th>Area</th><th>Changes</th><th>Capital</th><th>Run-rate effect</th></tr></thead><tbody>{team.lines.map((line) => <tr key={line.category}><td>{line.category}</td><td>{line.changes}</td><td>{money(line.capital)}</td><td>{line.operating ? `+$${line.operating.toLocaleString()}/round` : "$0/round"}</td></tr>)}</tbody></table></div><div className="review-totals"><p><b>Capital committed</b> {money(team.capital_spend)} of {money(team.capital_available)} · Remaining {money(team.capital_remaining)}</p><p><b>Run-rate after this round</b> {money(team.run_rate_after)} per round · was {money(team.run_rate_before)}</p></div></section>
    <section className="review-mirror"><h2>Before you lock</h2><p>These do not stop you. They are what a careful reader would notice.</p>{team.warnings.length ? <ul>{team.warnings.map((warning) => <li key={warning}>{warning}</li>)}</ul> : <p className="components-muted">No computed warnings for this round.</p>}</section>
    {!locked && <section className="review-actions"><button type="button" className="components-primary" disabled={saving || team.revision === null} onClick={lockRound}>{saving ? "Locking…" : "Lock round"}</button>{error && <p className="components-error" role="alert">{error}</p>}</section>}
  </div>;
}
