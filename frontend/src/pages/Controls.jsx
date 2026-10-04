/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client.js";
import { OptionCard } from "../components/index.js";

const meta = {
  strategy: { title: "Strategy", eyebrow: "Declare the trade-offs that guide your decisions", description: "Choose one declared strategy. The engine uses it when it evaluates capability fit and events." },
  governance: { title: "Governance", eyebrow: "Make ownership visible", description: "Assign accountable owners and sponsors for the capabilities your team is changing." },
  security: { title: "Data Policies", eyebrow: "Set the information boundary", description: "Choose the six policy switches and, when needed, add a security component to the current sheet." },
  services: { title: "Services", eyebrow: "Choose the platform foundation", description: "Select firm-wide services and a deployment placement. Prices and lead times come from the casepack." },
  people: { title: "People", eyebrow: "Fund capacity and adoption", description: "Add staff capacity or communicate the change to the units that will carry it." },
  challenges: { title: "Challenges", eyebrow: "Respond to the inbox", description: "Select a response and a rationale tag. Responses are evaluated by the engine at advance." },
  budget: { title: "Budget", eyebrow: "Make the capital case", description: "Request additional capital from the CFO with a concise, evidence-based justification." },
};

function SelectField({ label, value, options, onChange, disabled = false }) {
  return <label className="controls-field"><span>{label}</span><select value={value || ""} disabled={disabled} onChange={(event) => onChange(event.target.value)}><option value="">Choose…</option>{options.map((option) => <option key={option.key || option} value={option.key || option}>{option.label || option}</option>)}</select></label>;
}

function TextField({ label, value, onChange, type = "text", min, maxLength, placeholder, disabled = false }) {
  return <label className="controls-field"><span>{label}</span><input type={type} value={value ?? ""} min={min} maxLength={maxLength} placeholder={placeholder} disabled={disabled} onChange={(event) => onChange(event.target.value)} /></label>;
}

/* ---------- Extracted panels ---------- */

const policyLabels = {
  data_collection: "What customer data do we collect?",
  data_retention: "How long do we keep data?",
  data_access: "Who can access customer records?",
  access_logging: "Do we log who accesses data?",
  data_egress: "Can data leave our systems?",
  staff_monitoring: "Do we monitor employee activity?",
};

export function StrategyPanel({ view, instanceId, onSaved }) {
  const [viewState, setViewState] = useState(view);
  useEffect(() => setViewState(view), [view]);
  const [selection, setSelection] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const team = viewState?.team;
  const readOnly = !team || team.revision === null || team.locked_revision !== null;

  // team.strategy reflects the checkpoint (last advanced round), not the current
  // sheet.  The pending declare_strategy command lives in selected_commands.
  const pendingStrategy = team?.selected_commands?.find((c) => c.op === "declare_strategy")?.strategy;
  const effectiveStrategy = pendingStrategy || team?.strategy || null;

  useEffect(() => {
    if (effectiveStrategy && !selection.strategy) {
      setSelection((prior) => ({ ...prior, strategy: effectiveStrategy }));
    }
  }, [effectiveStrategy]); // eslint-disable-line react-hooks/exhaustive-deps

  function selected(key, fallback = "") { return selection[key] ?? fallback; }
  function set(key, value) { setSelection((prior) => ({ ...prior, [key]: value })); }

  async function save() {
    const strategy = selected("strategy");
    if (readOnly || !strategy) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/controls/strategy`, { version: 1, expected_revision: team.revision, commands: [{ key: "strategy_declaration", op: "declare_strategy", strategy }] });
      setViewState(response.data);
      if (onSaved) onSaved(response.data);
      setSelection({});
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The strategy decision could not be saved.");
    } finally { setSaving(false); }
  }

  const locked = team?.locked_revision !== null;
  const currentRound = team?.current_round || 1;

  return <div className="controls-page">
    {locked && <section className="review-banner"><strong>This round is locked.</strong><span>Decisions reopen when the instructor advances the round.</span></section>}
    {effectiveStrategy && <section className="controls-panel" style={{ padding: "var(--space-md) var(--space-lg)" }}><p style={{ margin: 0 }}><strong>Current strategy:</strong> <span className="dashboard-context__chip">{effectiveStrategy}</span></p></section>}
    {!effectiveStrategy && <section className="controls-panel" style={{ padding: "var(--space-md) var(--space-lg)" }}><p style={{ margin: 0 }}><strong>Current strategy:</strong> Not yet declared</p></section>}
    {currentRound > 2 && effectiveStrategy && <section className="review-banner"><strong>Strategy is locked after round 2.</strong><span>You declared "{effectiveStrategy}" and it cannot be changed.</span></section>}
    <div className="option-card-grid">{(viewState?.strategies || []).map((item) => <OptionCard key={item.key} title={item.label} detail={item.values.map((v) => v.replaceAll("_", " ")).join(", ")} selected={selected("strategy", effectiveStrategy) === item.key} disabled={readOnly || (currentRound > 2 && !!effectiveStrategy)} onSelect={() => set("strategy", item.key)} />)}</div>
    <section className="controls-actions"><button type="button" className="components-primary" disabled={readOnly || saving || !selected("strategy") || (currentRound > 2 && !!effectiveStrategy)} title={locked ? "This round is locked" : (currentRound > 2 && !!effectiveStrategy) ? "Strategy is locked after round 2" : undefined} onClick={save}>{saving ? "Saving…" : "Save strategy"}</button>{error && <p className="components-error" role="alert">{error}</p>}</section>
  </div>;
}

export function PeoplePanel({ view, instanceId, onSaved }) {
  const [viewState, setViewState] = useState(view);
  useEffect(() => setViewState(view), [view]);
  const [selection, setSelection] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const team = viewState?.team;
  const readOnly = !team || team.revision === null || team.locked_revision !== null;

  function selected(key, fallback = "") { return selection[key] ?? fallback; }
  function set(key, value) { setSelection((prior) => ({ ...prior, [key]: value })); }

  function commands() {
    const result = [];
    if (selected("hire")) result.push({ key: `hire_${selected("hire")}`, op: "hire", option: selected("hire") });
    if (selected("unit") && selected("communication")) result.push({ key: `communicate_${selected("unit")}`, op: "communicate", org_unit: selected("unit"), option: selected("communication") });
    return result;
  }

  async function save() {
    const payload = commands();
    if (readOnly || !payload.length) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/controls/people`, { version: 1, expected_revision: team.revision, commands: payload });
      setViewState(response.data);
      if (onSaved) onSaved(response.data);
      setSelection({});
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The people decision could not be saved.");
    } finally { setSaving(false); }
  }

  return <div className="controls-page">
    <p className="components-muted">Your firm needs IT staff to build, deploy, and support systems.</p>
    <section className="controls-panel"><h2>Hire staff</h2><SelectField label="Hiring option" value={selected("hire")} options={viewState?.hiring_options || []} onChange={(value) => set("hire", value)} disabled={readOnly} /></section>
    <section className="controls-panel"><h2>Communicate change to a business unit</h2><div className="controls-grid"><SelectField label="Unit" value={selected("unit")} options={viewState?.people_units || []} onChange={(value) => set("unit", value)} disabled={readOnly} /><SelectField label="Method" value={selected("communication")} options={viewState?.communication_options || []} onChange={(value) => set("communication", value)} disabled={readOnly} /></div></section>
    <section className="controls-actions"><button type="button" className="components-primary" disabled={readOnly || saving || !commands().length} onClick={save}>{saving ? "Saving…" : "Save people decisions"}</button>{error && <p className="components-error" role="alert">{error}</p>}</section>
  </div>;
}

export function SecurityPanel({ view, instanceId, onSaved }) {
  const [viewState, setViewState] = useState(view);
  useEffect(() => setViewState(view), [view]);
  const [selection, setSelection] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const team = viewState?.team;
  const readOnly = !team || team.revision === null || team.locked_revision !== null;
  const policies = useMemo(() => Object.fromEntries((team?.policies || []).map((item) => [item.key, item.selected])), [team]);

  function selected(key, fallback = "") { return selection[key] ?? fallback; }
  function set(key, value) { setSelection((prior) => ({ ...prior, [key]: value })); }

  function commands() {
    const result = (viewState?.policies || []).map((item) => ({ key: `policy_${item.key}`, op: "set_policy", policy: item.key, selected: selected(`policy:${item.key}`, policies[item.key]) }));
    if (selected("security_component") && selected("security_placement")) result.push({ key: `security_${selected("security_component")}`, op: "buy_application", catalog: selected("security_component"), placement: selected("security_placement"), config: "core", primary_for: null, tco_categories: [] });
    return result;
  }

  async function save() {
    const payload = commands();
    if (readOnly || !payload.length) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/controls/security`, { version: 1, expected_revision: team.revision, commands: payload });
      setViewState(response.data);
      if (onSaved) onSaved(response.data);
      setSelection({});
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The data policies decision could not be saved.");
    } finally { setSaving(false); }
  }

  return <div className="controls-page">
    <section className="controls-panel"><h2>Data policies</h2><div className="controls-grid">{(viewState?.policies || []).map((item) => <SelectField key={item.key} label={policyLabels[item.key] || item.label} value={selected(`policy:${item.key}`, item.selected)} options={item.options.map((key) => ({ key, label: key.replaceAll("_", " ") }))} onChange={(value) => set(`policy:${item.key}`, value)} disabled={readOnly} />)}</div></section>
    <section className="controls-panel"><h2>Security component request</h2><div className="controls-grid"><SelectField label="Component" value={selected("security_component")} options={viewState?.security_components || []} onChange={(value) => { set("security_component", value); set("security_placement", ""); }} disabled={readOnly} /><SelectField label="Placement" value={selected("security_placement")} options={((viewState?.security_components || []).find((item) => item.key === selected("security_component"))?.values || []).map((key) => ({ key, label: key.replaceAll("_", " ") }))} onChange={(value) => set("security_placement", value)} disabled={readOnly} /></div></section>
    <section className="controls-actions"><button type="button" className="components-primary" disabled={readOnly || saving || !commands().length} onClick={save}>{saving ? "Saving…" : "Save data policies"}</button>{error && <p className="components-error" role="alert">{error}</p>}</section>
  </div>;
}

export function GovernancePanel({ view, instanceId, onSaved }) {
  const [viewState, setViewState] = useState(view);
  useEffect(() => setViewState(view), [view]);
  const [selection, setSelection] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const team = viewState?.team;
  const readOnly = !team || team.revision === null || team.locked_revision !== null;

  function selected(key, fallback = "") { return selection[key] ?? fallback; }
  function set(key, value) { setSelection((prior) => ({ ...prior, [key]: value })); }

  function commands() {
    return (viewState?.governance || []).filter((item) => selected(`owner:${item.capability}`, item.owner) || selected(`sponsor:${item.capability}`, item.sponsor)).map((item) => ({ key: `assign_${item.capability}`, op: "assign", capability: item.capability, owner: selected(`owner:${item.capability}`, item.owner) || null, sponsor: selected(`sponsor:${item.capability}`, item.sponsor) || null }));
  }

  async function save() {
    const payload = commands();
    if (readOnly || !payload.length) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/controls/governance`, { version: 1, expected_revision: team.revision, commands: payload });
      setViewState(response.data);
      if (onSaved) onSaved(response.data);
      setSelection({});
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The ownership decision could not be saved.");
    } finally { setSaving(false); }
  }

  return <div className="controls-page">
    <p className="components-muted">Each capability needs a business owner and a sponsor to ensure adoption success and accountability.</p>
    <section className="controls-panel"><h2>Capability ownership</h2>
      <div className="detail-table-wrap"><table className="detail-table"><thead><tr><th>Capability</th><th>Owner</th><th>Sponsor</th></tr></thead><tbody>{(viewState?.governance || []).map((item) => <tr key={item.capability}><td><strong>{item.label}</strong></td><td><SelectField label="" value={selected(`owner:${item.capability}`, item.owner || "")} options={[{ key: "technology", label: "Technology" }, { key: "operations", label: "Operations" }, { key: "finance", label: "Finance" }]} onChange={(value) => set(`owner:${item.capability}`, value)} disabled={readOnly} /></td><td><SelectField label="" value={selected(`sponsor:${item.capability}`, item.sponsor || "")} options={[{ key: "business", label: "Business" }, { key: "technology", label: "Technology" }, { key: "finance", label: "Finance" }]} onChange={(value) => set(`sponsor:${item.capability}`, value)} disabled={readOnly} /></td></tr>)}</tbody></table></div>
    </section>
    <section className="controls-actions"><button type="button" className="components-primary" disabled={readOnly || saving || !commands().length} onClick={save}>{saving ? "Saving…" : "Save ownership decisions"}</button>{error && <p className="components-error" role="alert">{error}</p>}</section>
  </div>;
}

export function BudgetPanel({ view, instanceId, onSaved, reviewData }) {
  const [viewState, setViewState] = useState(view);
  useEffect(() => setViewState(view), [view]);
  const [selection, setSelection] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const team = viewState?.team;
  const reviewTeam = reviewData?.team;
  const readOnly = !team || team.revision === null || team.locked_revision !== null;

  function selected(key, fallback = "") { return selection[key] ?? fallback; }
  function set(key, value) { setSelection((prior) => ({ ...prior, [key]: value })); }

  function commands() {
    if (selected("amount") && selected("reason").trim()) return [{ key: "capital_request", op: "request_capital", amount: Number(selected("amount")), reason: selected("reason").trim() }];
    return [];
  }

  async function save() {
    const payload = commands();
    if (readOnly || !payload.length) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/controls/budget`, { version: 1, expected_revision: team.revision, commands: payload });
      setViewState(response.data);
      if (onSaved) onSaved(response.data);
      setSelection({});
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The capital request could not be saved.");
    } finally { setSaving(false); }
  }

  function money(value) {
    return typeof value === "number" && Number.isFinite(value) ? `$${value.toLocaleString()}` : "—";
  }

  return <div className="controls-page">
    {reviewTeam && <section className="spending-summary">
      <h2 style={{ margin: 0, fontSize: "18px" }}>Spending this round</h2>
      <div><span>Capital available</span><strong>{money(reviewTeam.capital_available)}</strong></div>
      <div><span>Capital committed</span><strong>{money(reviewTeam.capital_spend)}</strong></div>
      <div><span>Remaining</span><strong className="spending-highlight">{money(reviewTeam.capital_remaining)}</strong></div>
      <div><span>Run-rate this round</span><strong>{money(reviewTeam.run_rate_before)}/round</strong></div>
      <div><span>Run-rate after</span><strong>{money(reviewTeam.run_rate_after)}/round</strong></div>
    </section>}
    {reviewTeam?.lines && <section className="spending-table"><h2>Spending breakdown</h2><div className="detail-table-wrap"><table className="detail-table"><thead><tr><th>Area</th><th>Changes</th><th>Capital</th><th>Run-rate +/-</th></tr></thead><tbody>{reviewTeam.lines.map((line) => <tr key={line.category}><td>{line.category}</td><td>{line.changes}</td><td>{money(line.capital)}</td><td>{line.operating ? `+$${line.operating.toLocaleString()}/round` : "$0/round"}</td></tr>)}</tbody></table></div></section>}
    <section className="controls-panel"><h2>Request additional capital</h2>
      <p className="components-muted">The CFO approves requests up to ${Number(viewState?.capital_request_max_amount || 0).toLocaleString()}. Justification must be at least {viewState?.capital_request_min_reason_length || 20} characters.{viewState?.capital_request_approval_rounds ? ` Available in rounds: ${viewState.capital_request_approval_rounds.join(", ")}.` : ""}</p>
      <div className="controls-grid"><TextField label="Amount" type="number" min="1" value={selected("amount")} onChange={(value) => set("amount", value)} disabled={readOnly} /><label className="controls-field"><span>Justification</span><textarea value={selected("reason")} minLength={viewState?.capital_request_min_reason_length || undefined} maxLength={1000} placeholder="Explain the decision, evidence, and expected outcome." disabled={readOnly} onChange={(event) => set("reason", event.target.value)} /></label></div>
    </section>
    <section className="controls-actions"><button type="button" className="components-primary" disabled={readOnly || saving || !commands().length} onClick={save}>{saving ? "Saving…" : "Submit capital request"}</button>{error && <p className="components-error" role="alert">{error}</p>}</section>
  </div>;
}

/* ---------- Challenges (default export — stays as its own page) ---------- */

export default function Controls({ data, instanceId, section }) {
  const [view, setView] = useState(data);
  const [selection, setSelection] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { setView(data); setSelection({}); setError(""); }, [data, section]);
  const team = view?.team;
  const current = meta[section] || meta.challenges;
  const readOnly = !team || team.revision === null || team.locked_revision !== null;

  function selected(key, fallback = "") { return selection[key] ?? fallback; }
  function set(key, value) { setSelection((prior) => ({ ...prior, [key]: value })); }

  function commands() {
    if (section === "challenges" && selected("event") && selected("option") && selected("rationale")) {
      const response = { key: `respond_${selected("event")}`, op: "respond", event: selected("event"), option: selected("option"), rationale_tag: selected("rationale") };
      if (selected("note").trim()) response.note = selected("note").trim();
      return [response];
    }
    return [];
  }

  async function save() {
    const payload = commands();
    if (readOnly || !payload.length) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/controls/${section}`, { version: 1, expected_revision: team.revision, commands: payload });
      setView(response.data); setSelection({});
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "This decision could not be saved for the current round.");
    } finally { setSaving(false); }
  }

  if (!team) return <section className="controls-empty"><h2>Your team has not entered the runtime yet</h2><p>These controls become editable after the instructor initializes the team runtime.</p></section>;
  const challenge = view.challenges.find((item) => item.key === selected("event"));
  return <div className="controls-page">
    <section className="components-context"><p className="eyebrow">{current.eyebrow}</p><p className="components-muted">{team.name} · Round {team.current_round}</p><p className="controls-description">{current.description}</p></section>
    {team.locked_revision !== null && <section className="review-banner"><strong>This round is locked.</strong><span>Decisions reopen when the instructor advances the round.</span></section>}
    {section === "challenges" && <section className="controls-panel"><h2>Challenge response</h2><SelectField label="Inbox event" value={selected("event")} options={view.challenges} onChange={(value) => { set("event", value); set("option", ""); set("rationale", ""); set("note", ""); }} disabled={readOnly} />{challenge && <><SelectField label="Response" value={selected("option")} options={challenge.options} onChange={(value) => { set("option", value); const choice = challenge.options.find((item) => item.key === value); set("rationale", choice?.rationale_tags?.[0] || ""); }} disabled={readOnly} />{selected("option") && <SelectField label="Rationale" value={selected("rationale")} options={(challenge.options.find((item) => item.key === selected("option"))?.rationale_tags || []).map((key) => ({ key, label: key.replaceAll("_", " ") }))} onChange={(value) => set("rationale", value)} disabled={readOnly} />}<label className="controls-field"><span>Decision note (optional)</span><textarea value={selected("note")} maxLength={2000} placeholder="Explain the evidence behind this response." disabled={readOnly} onChange={(event) => set("note", event.target.value)} /></label></>}</section>}
    <section className="controls-actions"><button type="button" className="components-primary" disabled={readOnly || saving || !commands().length} onClick={save}>{saving ? "Saving…" : `Save ${current.title.toLowerCase()} decision`}</button>{error && <p className="components-error" role="alert">{error}</p>}</section>
  </div>;
}
