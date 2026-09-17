/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client.js";

const meta = {
  strategy: { title: "Strategy", eyebrow: "Declare the trade-offs that guide your decisions", description: "Choose one declared strategy. The engine uses it when it evaluates capability fit and events." },
  governance: { title: "Governance", eyebrow: "Make ownership visible", description: "Assign accountable owners and sponsors for the capabilities your team is changing." },
  security: { title: "Security", eyebrow: "Set the information boundary", description: "Choose the six policy switches and, when needed, add a security component to the current sheet." },
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

export default function Controls({ data, instanceId, section }) {
  const [view, setView] = useState(data);
  const [selection, setSelection] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => { setView(data); setSelection({}); setError(""); }, [data, section]);
  const team = view?.team;
  const current = meta[section] || meta.strategy;
  const readOnly = !team || team.revision === null || team.locked_revision !== null;
  const policies = useMemo(() => Object.fromEntries((team?.policies || []).map((item) => [item.key, item.selected])), [team]);

  function selected(key, fallback = "") { return selection[key] ?? fallback; }
  function set(key, value) { setSelection((prior) => ({ ...prior, [key]: value })); }

  function commands() {
    if (section === "strategy") return selected("strategy") ? [{ key: "strategy_declaration", op: "declare_strategy", strategy: selected("strategy") }] : [];
    if (section === "governance") return (view.governance || []).filter((item) => selected(`owner:${item.capability}`, item.owner) || selected(`sponsor:${item.capability}`, item.sponsor)).map((item) => ({ key: `assign_${item.capability}`, op: "assign", capability: item.capability, owner: selected(`owner:${item.capability}`, item.owner) || null, sponsor: selected(`sponsor:${item.capability}`, item.sponsor) || null }));
    if (section === "security") {
      const result = (view.policies || []).map((item) => ({ key: `policy_${item.key}`, op: "set_policy", policy: item.key, selected: selected(`policy:${item.key}`, policies[item.key]) }));
      if (selected("security_component") && selected("security_placement")) result.push({ key: `security_${selected("security_component")}`, op: "buy_application", catalog: selected("security_component"), placement: selected("security_placement"), config: "core", primary_for: null, tco_categories: [] });
      return result;
    }
    if (section === "services") return selected("service") && selected("placement") ? [{ key: `service_${selected("service")}`, op: "buy_service", service: selected("service"), placement: selected("placement"), units: 1 }] : [];
    if (section === "people") {
      const result = [];
      if (selected("hire")) result.push({ key: `hire_${selected("hire")}`, op: "hire", option: selected("hire") });
      if (selected("unit") && selected("communication")) result.push({ key: `communicate_${selected("unit")}`, op: "communicate", org_unit: selected("unit"), option: selected("communication") });
      return result;
    }
    if (section === "challenges" && selected("event") && selected("option") && selected("rationale")) {
      const response = { key: `respond_${selected("event")}`, op: "respond", event: selected("event"), option: selected("option"), rationale_tag: selected("rationale") };
      if (selected("note").trim()) response.note = selected("note").trim();
      return [response];
    }
    if (section === "budget" && selected("amount") && selected("reason").trim()) return [{ key: "capital_request", op: "request_capital", amount: Number(selected("amount")), reason: selected("reason").trim() }];
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
  const service = view.services.find((item) => item.key === selected("service"));
  const challenge = view.challenges.find((item) => item.key === selected("event"));
  return <div className="controls-page">
    <section className="components-context"><p className="eyebrow">{current.eyebrow}</p><p className="components-muted">{team.name} · Round {team.current_round}</p><p className="controls-description">{current.description}</p></section>
    {team.locked_revision !== null && <section className="review-banner"><strong>This round is locked.</strong><span>Decisions reopen when the instructor advances the round.</span></section>}
    {section === "strategy" && <section className="controls-panel"><h2>Declared strategy</h2><SelectField label="Strategy" value={selected("strategy", team.strategy)} options={view.strategies} onChange={(value) => set("strategy", value)} disabled={readOnly} /><div className="controls-option-grid">{view.strategies.map((item) => <article key={item.key}><strong>{item.label}</strong><p>{item.values.map((value) => value.replaceAll("_", " ")).join(" · ")}</p></article>)}</div></section>}
    {section === "governance" && <section className="controls-panel"><h2>Capability ownership</h2><div className="controls-grid">{view.governance.map((item) => <article className="controls-card" key={item.capability}><h3>{item.label}</h3><SelectField label="Owner" value={selected(`owner:${item.capability}`, item.owner || "")} options={[{ key: "technology", label: "Technology" }, { key: "operations", label: "Operations" }, { key: "finance", label: "Finance" }]} onChange={(value) => set(`owner:${item.capability}`, value)} disabled={readOnly} /><SelectField label="Sponsor" value={selected(`sponsor:${item.capability}`, item.sponsor || "")} options={[{ key: "business", label: "Business" }, { key: "technology", label: "Technology" }, { key: "finance", label: "Finance" }]} onChange={(value) => set(`sponsor:${item.capability}`, value)} disabled={readOnly} /></article>)}</div></section>}
    {section === "security" && <section className="controls-panel"><h2>Information-policy switches</h2><div className="controls-grid">{view.policies.map((item) => <SelectField key={item.key} label={item.label} value={selected(`policy:${item.key}`, item.selected)} options={item.options.map((key) => ({ key, label: key.replaceAll("_", " ") }))} onChange={(value) => set(`policy:${item.key}`, value)} disabled={readOnly} />)}</div><h2>Security component request</h2><div className="controls-grid"><SelectField label="Component" value={selected("security_component")} options={view.security_components} onChange={(value) => { set("security_component", value); set("security_placement", ""); }} disabled={readOnly} /><SelectField label="Placement" value={selected("security_placement")} options={(view.security_components.find((item) => item.key === selected("security_component"))?.values || []).map((key) => ({ key, label: key.replaceAll("_", " ") }))} onChange={(value) => set("security_placement", value)} disabled={readOnly} /></div></section>}
    {section === "services" && <section className="controls-panel"><h2>Firm-wide service request</h2><SelectField label="Service" value={selected("service")} options={view.services} onChange={(value) => { set("service", value); set("placement", ""); }} disabled={readOnly} />{service && <SelectField label="Placement" value={selected("placement")} options={service.values.map((key) => ({ key, label: key.replaceAll("_", " ") }))} onChange={(value) => set("placement", value)} disabled={readOnly} />}</section>}
    {section === "people" && <section className="controls-panel"><h2>Capacity and communication</h2><div className="controls-grid"><SelectField label="Hiring option" value={selected("hire")} options={view.hiring_options} onChange={(value) => set("hire", value)} disabled={readOnly} /><SelectField label="Unit" value={selected("unit")} options={view.people_units} onChange={(value) => set("unit", value)} disabled={readOnly} /><SelectField label="Communication" value={selected("communication")} options={view.communication_options} onChange={(value) => set("communication", value)} disabled={readOnly} /></div></section>}
    {section === "challenges" && <section className="controls-panel"><h2>Challenge response</h2><SelectField label="Inbox event" value={selected("event")} options={view.challenges} onChange={(value) => { set("event", value); set("option", ""); set("rationale", ""); set("note", ""); }} disabled={readOnly} />{challenge && <><SelectField label="Response" value={selected("option")} options={challenge.options} onChange={(value) => { set("option", value); const choice = challenge.options.find((item) => item.key === value); set("rationale", choice?.rationale_tags?.[0] || ""); }} disabled={readOnly} />{selected("option") && <SelectField label="Rationale" value={selected("rationale")} options={(challenge.options.find((item) => item.key === selected("option"))?.rationale_tags || []).map((key) => ({ key, label: key.replaceAll("_", " ") }))} onChange={(value) => set("rationale", value)} disabled={readOnly} />}<label className="controls-field"><span>Decision note (optional)</span><textarea value={selected("note")} maxLength={2000} placeholder="Explain the evidence behind this response." disabled={readOnly} onChange={(event) => set("note", event.target.value)} /></label></>}</section>}
    {section === "budget" && <section className="controls-panel"><h2>Capital request</h2><p className="components-muted">Approved requests add capital to this round and are recorded in the accounting ledger. Maximum ${Number(view.capital_request_max_amount || 0).toLocaleString()}; justification must be at least {view.capital_request_min_reason_length} characters.</p><div className="controls-grid"><TextField label="Amount" type="number" min="1" value={selected("amount")} onChange={(value) => set("amount", value)} disabled={readOnly} /><label className="controls-field"><span>Justification</span><textarea value={selected("reason")} minLength={view.capital_request_min_reason_length || undefined} maxLength={1000} placeholder="Explain the decision, evidence, and expected outcome." disabled={readOnly} onChange={(event) => set("reason", event.target.value)} /></label></div></section>}
    <section className="controls-actions"><button type="button" className="components-primary" disabled={readOnly || saving || !commands().length} onClick={save}>{saving ? "Saving…" : `Save ${current.title.toLowerCase()} decision`}</button>{error && <p className="components-error" role="alert">{error}</p>}</section>
  </div>;
}
