/* eslint-disable react/prop-types */
import { useEffect, useState } from "react";
import { apiClient } from "../api/client.js";

function percent(value) {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "—";
}

export default function Debrief({ data, instanceId }) {
  const [view, setView] = useState(data);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => setView(data), [data]);
  const team = view?.team;
  if (!team) return <section className="components-empty"><h2>Your team has not entered the runtime yet</h2><p>The debrief will appear after a round has been advanced.</p></section>;
  const latest = team.rounds[team.rounds.length - 1];
  async function download() {
    setDownloading(true); setError("");
    try {
      const response = await apiClient.get(`/instances/${instanceId}/debrief/download`, { responseType: "blob" });
      const url = URL.createObjectURL(response.data); const anchor = document.createElement("a"); anchor.href = url; anchor.download = `mis-sim-debrief-${instanceId}.txt`; anchor.click(); URL.revokeObjectURL(url);
    } catch { setError("The debrief could not be downloaded."); }
    finally { setDownloading(false); }
  }
  if (!latest) return <div className="debrief-page"><section className="components-empty"><h2>No results yet</h2><p>Your first round runs at the deadline. Advance a locked round before opening the report.</p></section></div>;
  const score = latest.score || {}; const scorecard = latest.scorecard || {}; const changes = latest.state_changes || {}; const financials = latest.financials || {}; const debt = latest.technical_debt || {}; const freshness = latest.data_freshness || changes.data_freshness || {};
  return <div className="debrief-page">
    <section className="components-context"><div><p className="eyebrow">Business status report</p><p className="components-muted">{team.name} · through round {team.latest_round}</p></div><button type="button" className="components-primary" onClick={download} disabled={downloading}>{downloading ? "Preparing…" : "Download report"}</button></section>
    <section className="debrief-score"><div><p className="eyebrow">Firm score</p><strong>{percent(score.firm_score)}</strong></div>{Object.entries(scorecard).filter(([key]) => key !== "financial_partial").map(([key, value]) => <div key={key}><span>{key.replaceAll("_", " ")}</span><strong>{percent(value)}</strong></div>)}</section>
    <section className="debrief-causal"><div className="components-panel-heading"><div><h2>What changed</h2><p className="components-muted">The round result records what arrived, what was adopted, and what fired.</p></div><span className="components-muted">Round {latest.round}</span></div><div className="debrief-grid"><article><h3>State changes</h3><p>Arrived: {changes.arrived?.length ? changes.arrived.join(", ") : "none"}</p><p>Retired: {changes.retired?.length ? changes.retired.join(", ") : "none"}</p><p>Rollout changes: {changes.changed_rollouts?.length || 0}</p></article><article><h3>Signals and events</h3><p>Events: {latest.events.length ? latest.events.map((event) => event.label || event.key).join(", ") : "none"}</p><p>Prevented: {latest.prevented_events.length || 0}</p><p>Responses: {latest.responses?.length ? latest.responses.map((response) => `${response.option} (${response.rationale_tag})${response.note ? ` — ${response.note}` : ""}`).join("; ") : "none"}</p></article><article><h3>Financial result</h3><p>Capital spend: {financials.capital_spend ?? "—"}</p><p>Run-rate: {financials.opex_runrate ?? "—"}</p><p>Technical debt: {debt.closing ?? "—"}</p><p>Fresh data coverage: {typeof freshness.coverage === "number" ? `${Math.round(freshness.coverage * 100)}%` : "—"}</p></article></div></section>
    {score.capabilities?.length > 0 && <section className="debrief-capabilities"><h2>Capability explanation</h2><div className="debrief-capability-list">{score.capabilities.map((item) => <article key={item.capability}><strong>{item.capability.replaceAll("_", " ")}</strong><span>{percent(item.realised)} realised</span><span>Throttled by {item.throttle?.replaceAll("_", " ") || "—"}</span></article>)}</div></section>}
    {error && <p className="components-error" role="alert">{error}</p>}
  </div>;
}
