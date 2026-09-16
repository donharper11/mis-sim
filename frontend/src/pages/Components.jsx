/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client.js";
import { DetailTable, OptionCard, OptionRow, StatusBadge } from "../components/index.js";

const placementNames = { cloud: "Cloud", on_prem: "On-Premises", saas: "SaaS" };
const tabs = ["Overview", "Deployment", "Data", "Connections", "Lifecycle"];

function assetStatus(asset) {
  if (asset.status === "retired") return ["not-started", "Retired"];
  if (typeof asset.adoption === "number" && asset.adoption < 0.5) return ["needs-attention", "Needs attention"];
  if (typeof asset.adoption === "number" && asset.adoption < 0.9) return ["partly-done", "Partly done"];
  return ["complete", "Complete"];
}

function AddWizard({ team, onClose, onSaved, instanceId }) {
  const [step, setStep] = useState(1);
  const [choiceKey, setChoiceKey] = useState("");
  const [placement, setPlacement] = useState("");
  const [config, setConfig] = useState("");
  const [tcoCategories, setTcoCategories] = useState([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const choice = team.choices.find((item) => item.key === choiceKey);
  const mode = choice?.placements.find((item) => item.key === placement);
  const canSave = choice && mode && config && team.revision !== null && team.locked_revision === null;

  function selectChoice(key) {
    const next = team.choices.find((item) => item.key === key);
    setChoiceKey(key); setPlacement(next?.placements[0]?.key || ""); setConfig(next?.configs[0]?.key || ""); setTcoCategories([]);
  }

  async function submit(event) {
    event.preventDefault();
    if (!canSave) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/components`, {
        version: 1, expected_revision: team.revision,
        replace_categories: { application: [{ key: `buy_${choiceKey}_${placement}`, op: "buy_application", catalog: choiceKey, placement, config, primary_for: null, tco_categories: tcoCategories }] },
      });
      onSaved(response.data); onClose();
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The component decision could not be saved.");
    } finally { setSaving(false); }
  }

  return (
    <section className="components-wizard" aria-labelledby="components-wizard-heading">
      <div className="components-panel-heading"><div><p className="eyebrow">Add to the plan</p><h2 id="components-wizard-heading">What are you adding?</h2></div><button type="button" className="components-secondary" onClick={onClose}>Cancel</button></div>
      <div className="components-steps" aria-label="Wizard steps">{["Choose", "Placement", "Configuration", "TCO forecast", "Review"].map((label, index) => <span className={step === index + 1 ? "components-step--active" : step > index + 1 ? "components-step--done" : ""} key={label}>{index + 1}. {label}</span>)}</div>
      <form onSubmit={submit}>
        {step === 1 && <div className="option-card-grid">{team.choices.map((item) => <OptionCard key={item.key} title={item.label} detail={`${item.people || "—"} people · ${(item.serves || []).join(", ") || "No capability recorded"}`} selected={choiceKey === item.key} onSelect={() => selectChoice(item.key)} />)}</div>}
        {step === 2 && <div className="choice-stack">{choice?.placements.map((item) => <OptionRow key={item.key} label={placementNames[item.key] || item.label} detail={`$${item.capex.toLocaleString()} capex · $${item.opex.toLocaleString()} per round${item.lead_time ? ` · available in ${item.lead_time} round${item.lead_time === 1 ? "" : "s"}` : " · available now"}`} selected={placement === item.key} onSelect={() => setPlacement(item.key)} />)}</div>}
        {step === 3 && <div className="choice-stack">{choice?.configs.map((item) => <OptionRow key={item.key} label={item.label} detail="Configuration for this component" selected={config === item.key} onSelect={() => setConfig(item.key)} />)}</div>}
        {step === 4 && <div className="components-review"><h3>What else will this cost?</h3><p className="components-muted">Select the secondary cost categories you expect. The debrief compares this forecast with the costs the round actually produces.</p><div className="components-tco-grid">{[...(choice?.true_cost_categories || []), ...(choice?.decoy_cost_categories || [])].map((category) => <label className="components-tco-option" key={category}><input type="checkbox" checked={tcoCategories.includes(category)} onChange={(event) => setTcoCategories((prior) => event.target.checked ? [...prior, category] : prior.filter((item) => item !== category))} /><span>{category.replaceAll("_", " ")}</span></label>)}</div><p>{choice?.label} · {placementNames[placement] || placement} · {config} · {mode ? `$${mode.capex.toLocaleString()} capex + $${mode.opex.toLocaleString()} per round` : "Choose a placement"}</p></div>}
        {step === 5 && <div className="components-review"><h3>{choice?.label}</h3><p>{placementNames[placement] || placement} · {config} · {mode ? `$${mode.capex.toLocaleString()} capex + $${mode.opex.toLocaleString()} per round` : "Choose a placement"}</p><p>Forecast: {tcoCategories.length ? tcoCategories.map((item) => item.replaceAll("_", " ")).join(", ") : "No secondary costs selected"}.</p><p className="components-muted">This adds one application command to the current round sheet.</p></div>}
        <div className="components-wizard-actions"><button type="button" className="components-secondary" disabled={step === 1} onClick={() => setStep((value) => value - 1)}>Back</button>{step < 5 ? <button type="button" className="components-primary" disabled={(step === 1 && !choice) || (step === 2 && !placement) || (step === 3 && !config)} onClick={() => setStep((value) => value + 1)}>Continue</button> : <button type="submit" className="components-primary" disabled={!canSave || saving}>{saving ? "Saving…" : "Add to plan"}</button>}</div>
        {error && <p className="components-error" role="alert">{error}</p>}
      </form>
    </section>
  );
}

function ComponentDetail({ asset, onClose, team, instanceId, onSaved }) {
  const [tab, setTab] = useState("Overview");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [status, label] = assetStatus(asset);
  async function retire() {
    if (team.revision === null || team.locked_revision !== null) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/components`, { version: 1, expected_revision: team.revision, replace_categories: { lifecycle: [{ key: `retire_${asset.id}`, op: "retire_asset", asset: asset.id }] } });
      onSaved(response.data); onClose();
    } catch (requestError) { setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The lifecycle decision could not be saved."); }
    finally { setSaving(false); }
  }
  return <section className="components-detail" aria-labelledby="components-detail-heading">
    <div className="components-panel-heading"><div><p className="eyebrow">Component detail</p><h2 id="components-detail-heading">{asset.label}</h2><p className="components-muted">{asset.org_unit || "Firm-wide"} · {asset.people || "—"} people · {asset.serves.join(", ") || "No capability recorded"}</p></div><button type="button" className="components-secondary" onClick={onClose}>Close</button></div>
    <div className="components-tabs" role="tablist">{tabs.map((item) => <button type="button" role="tab" aria-selected={tab === item} className={tab === item ? "components-tab--active" : ""} onClick={() => setTab(item)} key={item}>{item}</button>)}</div>
    {tab === "Overview" && <div className="components-detail-grid"><article><h3>Overview</h3><p>{asset.label} serves {asset.serves.join(", ") || "the business"} for {asset.people || "the recorded"} people.</p><StatusBadge status={status} label={label} /></article><article><h3>Rollout</h3><p>Trained {asset.trained_count ?? "—"} · adoption {typeof asset.adoption === "number" ? `${Math.round(asset.adoption * 100)}%` : "—"} · process {asset.process || "—"}</p></article></div>}
    {tab === "Deployment" && <div className="components-detail-grid"><article><h3>Placement</h3><p>{placementNames[asset.placement] || asset.placement} · {asset.config || "default configuration"}</p></article><article><h3>Lifecycle</h3><p>Installed round {asset.installed_round} · {asset.units} unit{asset.units === 1 ? "" : "s"}</p></article></div>}
    {tab === "Data" && <div className="components-detail-copy"><h3>Data</h3><p>The runtime records this component’s capabilities and people affected through the registered casepack.</p></div>}
    {tab === "Connections" && <div className="components-detail-copy"><h3>Connections</h3><p>Connection detail will appear when integration records are present for this asset.</p></div>}
    {tab === "Lifecycle" && <div className="components-detail-copy"><h3>Lifecycle</h3><p>Installed round {asset.installed_round}. Retiring removes this asset from the active estate at the round boundary.</p><button type="button" className="components-danger" disabled={saving || team.locked_revision !== null || team.revision === null || asset.status === "retired"} onClick={retire}>{saving ? "Saving…" : "Retire component"}</button>{error && <p className="components-error" role="alert">{error}</p>}</div>}
  </section>;
}

export default function Components({ data, instanceId }) {
  const [view, setView] = useState(data);
  const [selectedId, setSelectedId] = useState(null);
  const [wizard, setWizard] = useState(false);
  const [filter, setFilter] = useState("all");
  useEffect(() => setView(data), [data]);
  const team = view?.team;
  const selected = team?.assets?.find((asset) => asset.id === selectedId);
  const rows = useMemo(() => (team?.assets || []).filter((asset) => filter === "all" || asset.source_key.includes(filter)), [team, filter]);
  const [projectError, setProjectError] = useState("");
  if (!team) return <section className="components-empty"><h2>Your team has not entered the runtime yet</h2><p>Components will appear here after the team runtime is initialized.</p></section>;
  async function projectAction(project, choice) {
    if (team.revision === null || team.locked_revision !== null) return;
    setProjectError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/components`, { version: 1, expected_revision: team.revision, replace_categories: { lifecycle: [{ key: `${choice}_${project.id}`, op: "project", order: project.id, choice }] } });
      setView(response.data);
    } catch (requestError) { setProjectError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The in-flight decision could not be saved."); }
  }
  return <div className="components-page">
    <section className="components-context"><div><p className="eyebrow">What each part of the business runs</p><p className="components-muted">{team.name} · Round {team.current_round}</p></div>{team.strategy && <span className="dashboard-context__chip">{team.strategy}</span>}</section>
    <section className="components-toolbar"><div className="components-filters">{["all", "hardware", "software", "database", "network"].map((value) => <button type="button" className={filter === value ? "components-filter--active" : ""} onClick={() => setFilter(value)} key={value}>{value === "all" ? "All" : value[0].toUpperCase() + value.slice(1)}</button>)}</div><button type="button" className="components-primary" disabled={team.revision === null || team.locked_revision !== null || !team.choices.length} onClick={() => setWizard(true)}>Add component</button></section>
    {wizard && <AddWizard team={team} instanceId={instanceId} onClose={() => setWizard(false)} onSaved={(next) => setView(next)} />}
    {selected && <ComponentDetail asset={selected} team={team} instanceId={instanceId} onClose={() => setSelectedId(null)} onSaved={(next) => setView(next)} />}
    <section className="components-table-panel"><div className="components-panel-heading"><div><h2>Components</h2><p className="components-muted">Registered assets and their current rollout state</p></div><span className="components-muted">{rows.length} shown</span></div><DetailTable columns={[{ key: "label", label: "Item" }, { key: "source_key", label: "Category" }, { key: "placement", label: "Runs on" }, { key: "org_unit", label: "For whom" }, { key: "adoption", label: "Adoption" }, { key: "statusLabel", label: "Status" }]} rows={rows.map((asset) => { const [, label] = assetStatus(asset); return { ...asset, source_key: asset.source_key.replaceAll("_", " "), placement: placementNames[asset.placement] || asset.placement || "—", org_unit: asset.org_unit?.replaceAll("_", " ") || "—", adoption: typeof asset.adoption === "number" ? `${Math.round(asset.adoption * 100)}%` : "—", statusLabel: label, key: asset.id }; })} onRowClick={(row) => setSelectedId(row.id)} /></section>
    {team.projects.length > 0 && <section className="components-projects"><h2>In flight</h2>{team.projects.map((project) => <article className="components-project-row" key={project.id}><div><strong>{project.label}</strong><p>{project.status} · {project.remaining_lead} round{project.remaining_lead === 1 ? "" : "s"} remaining</p></div>{["pending", "paused"].includes(project.status) && <div className="components-project-actions"><button type="button" className="components-secondary" disabled={team.locked_revision !== null} onClick={() => projectAction(project, project.status === "paused" ? "continue" : "pause")}>{project.status === "paused" ? "Continue" : "Pause"}</button><button type="button" className="components-danger" disabled={team.locked_revision !== null} onClick={() => projectAction(project, "kill")}>Kill</button></div>}</article>)}{projectError && <p className="components-error" role="alert">{projectError}</p>}</section>}
  </div>;
}
