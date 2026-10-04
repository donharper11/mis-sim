/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api/client.js";
import { DetailTable, OptionCard, OptionRow } from "../components/index.js";

const placementNames = { cloud: "Cloud", on_prem: "On-Premises", saas: "SaaS" };
const wizardStepLabels = ["Select application", "Where will it run?", "Configuration tier", "Cost forecast", "Confirm & add"];

function formatOrgUnit(value) {
  if (!value) return "Firmwide";
  return value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function assetStatus(asset) {
  if (asset.status === "retired") return ["not-started", "Retired"];
  if (typeof asset.adoption === "number" && asset.adoption < 0.5) return ["needs-attention", "Needs attention"];
  if (typeof asset.adoption === "number" && asset.adoption < 0.9) return ["partly-done", "Partly done"];
  return ["complete", "Complete"];
}

const orgUnitOptions = [
  { key: "hr", label: "HR" },
  { key: "finance", label: "Finance" },
  { key: "marketing", label: "Marketing" },
  { key: "service", label: "Service" },
  { key: "production", label: "Production" },
];

const operationOptions = [
  { key: "active", label: "Active" },
  { key: "discontinue", label: "Discontinue" },
  { key: "modified", label: "Modified" },
];

function SimpleAddForm({ team, instanceId, onSaved, onAdvanced, onCancel, hostPlatforms }) {
  const [choiceKey, setChoiceKey] = useState("");
  const [customName, setCustomName] = useState("");
  const [notes, setNotes] = useState("");
  const [basePlatformId, setBasePlatformId] = useState("");
  const [orgUnit, setOrgUnit] = useState("");
  const [operation, setOperation] = useState("active");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const choice = team.choices.find((item) => item.key === choiceKey);
  const availablePlatforms = (hostPlatforms || []).filter((p) => p.status === "active" || p.status === "pending");

  // Derive placement from selected platform's type
  const selectedPlatform = availablePlatforms.find((p) => String(p.id) === basePlatformId);
  const derivedPlacement = selectedPlatform ? (selectedPlatform.platform_type === "cloud" ? "cloud" : "on_prem") : (choice?.placements[0]?.key || "on_prem");

  const readOnly = team.revision === null || team.locked_revision !== null;
  const canSubmit = !readOnly && choiceKey && orgUnit && operation;

  async function submit(event) {
    event.preventDefault();
    if (!canSubmit) return;
    setSaving(true); setError("");
    try {
      let commands;
      if (operation === "discontinue") {
        const asset = team.assets?.find((a) => a.source_key === choiceKey && a.status === "active");
        if (!asset) { setError("No active asset found to discontinue."); setSaving(false); return; }
        commands = { lifecycle: [{ key: `retire_${asset.id}`, op: "retire_asset", asset: asset.id }] };
      } else {
        const placement = derivedPlacement;
        const config = choice?.configs[0]?.key || "core";
        commands = { application: [{ key: `buy_${choiceKey}_${placement}`, op: "buy_application", catalog: choiceKey, placement, config, primary_for: orgUnit, tco_categories: [] }] };
      }
      const response = await apiClient.patch(`/instances/${instanceId}/components`, {
        version: 1, expected_revision: team.revision, replace_categories: commands,
      });
      onSaved(response.data);
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The application decision could not be saved.");
    } finally { setSaving(false); }
  }

  return (
    <div className="modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget) onCancel(); }}>
      <section className="modal-dialog">
        <div className="modal-header">
          <h2>Add Application</h2>
          <button type="button" className="modal-close" onClick={onCancel} aria-label="Close">&times;</button>
        </div>
        <form onSubmit={submit} className="modal-body">
          <label>Name
            <select value={choiceKey} onChange={(e) => setChoiceKey(e.target.value)} disabled={readOnly}>
              <option value="">Choose an application…</option>
              {team.choices.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}
            </select>
          </label>
          <label>Custom Name
            <input type="text" value={customName} maxLength={200} placeholder="Your name for this application" onChange={(e) => setCustomName(e.target.value)} disabled={readOnly} />
          </label>
          <label>Notes
            <textarea value={notes} maxLength={1000} placeholder="Optional notes" onChange={(e) => setNotes(e.target.value)} disabled={readOnly} />
          </label>
          <label>Base Platform
            <select value={basePlatformId} onChange={(e) => setBasePlatformId(e.target.value)} disabled={readOnly}>
              <option value="">Choose a platform…</option>
              {availablePlatforms.map((p) => <option key={p.id} value={String(p.id)}>{p.platform_code} — {p.name}{p.status === "pending" ? " (pending)" : ""}</option>)}
            </select>
          </label>
          <label>Business Unit
            <select value={orgUnit} onChange={(e) => setOrgUnit(e.target.value)} disabled={readOnly}>
              <option value="">Choose a unit…</option>
              {orgUnitOptions.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}
            </select>
          </label>
          <label>Operation
            <select value={operation} onChange={(e) => setOperation(e.target.value)} disabled={readOnly}>
              {operationOptions.map((item) => <option key={item.key} value={item.key}>{item.label}</option>)}
            </select>
          </label>
          <div className="modal-actions">
            <button type="submit" className="components-primary" disabled={!canSubmit || saving}>{saving ? "Launching…" : "Launch Application"}</button>
            <button type="button" className="components-secondary" onClick={onAdvanced}>Advanced setup</button>
            <button type="button" className="components-secondary" onClick={onCancel}>Cancel</button>
          </div>
          {error && <p className="components-error" role="alert">{error}</p>}
        </form>
      </section>
    </div>
  );
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
      <div className="components-panel-heading"><div><p className="eyebrow">Add to the plan</p><h2 id="components-wizard-heading">Choose applications for each business unit</h2></div><button type="button" className="components-secondary" onClick={onClose}>Cancel</button></div>
      <div className="components-steps" aria-label="Wizard steps">{wizardStepLabels.map((label, index) => <span className={step === index + 1 ? "components-step--active" : step > index + 1 ? "components-step--done" : ""} key={label}>{index + 1}. {label}</span>)}</div>
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

export default function Components({ data, instanceId, hostPlatforms }) {
  const navigate = useNavigate();
  const [view, setView] = useState(data);
  const [wizard, setWizard] = useState(false);
  const [showSimpleForm, setShowSimpleForm] = useState(false);
  const [filter, setFilter] = useState("All");
  useEffect(() => setView(data), [data]);
  const team = view?.team;

  // Build business-unit filter list from assets
  const filterOptions = useMemo(() => {
    if (!team?.assets) return ["All"];
    const units = new Set(team.assets.map((a) => a.org_unit || "firmwide"));
    return ["All", ...Array.from(units).sort().map((u) => formatOrgUnit(u))];
  }, [team]);

  const rows = useMemo(() => {
    const assets = team?.assets || [];
    if (filter === "All") return assets;
    return assets.filter((asset) => formatOrgUnit(asset.org_unit) === filter);
  }, [team, filter]);

  if (!team) return <section className="components-empty"><h2>Your team has not entered the runtime yet</h2><p>Components will appear here after the team runtime is initialized.</p></section>;
  return <div className="components-page">
    <section className="components-toolbar"><div className="components-filters">{filterOptions.map((value) => <button type="button" className={filter === value ? "components-filter--active" : ""} onClick={() => setFilter(value)} key={value}>{value}</button>)}</div><button type="button" className="components-primary" disabled={team.revision === null || team.locked_revision !== null || !team.choices.length} onClick={() => setShowSimpleForm(true)}>+ Add application</button></section>
    {showSimpleForm && !wizard && <SimpleAddForm team={team} instanceId={instanceId} hostPlatforms={hostPlatforms} onSaved={(next) => { setView(next); setShowSimpleForm(false); }} onAdvanced={() => { setShowSimpleForm(false); setWizard(true); }} onCancel={() => setShowSimpleForm(false)} />}
    {wizard && <AddWizard team={team} instanceId={instanceId} onClose={() => setWizard(false)} onSaved={(next) => setView(next)} />}
    <section className="components-table-panel"><div className="components-panel-heading"><div><h2>Applications</h2><p className="components-muted">Registered assets and their current rollout state</p></div><span className="components-muted">{rows.length} shown</span></div><DetailTable columns={[{ key: "label", label: "Application" }, { key: "typeLabel", label: "Type" }, { key: "placement", label: "Runs on" }, { key: "org_unit", label: "For whom" }, { key: "adoption", label: "Adoption" }, { key: "statusLabel", label: "Status" }]} rows={rows.map((asset) => { const [, label] = assetStatus(asset); return { ...asset, typeLabel: asset.label, placement: placementNames[asset.placement] || asset.placement || "—", org_unit: formatOrgUnit(asset.org_unit), adoption: typeof asset.adoption === "number" ? `${Math.round(asset.adoption * 100)}%` : "—", statusLabel: label, key: asset.id }; })} onRowClick={(row) => navigate(`/applications/${row.id}`)} /></section>
  </div>;
}
