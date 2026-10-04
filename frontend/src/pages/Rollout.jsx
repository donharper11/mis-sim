/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client.js";
import { ContextBanner, OptionRow, StatusBadge } from "../components/index.js";
import { GovernancePanel } from "./Controls.jsx";

function percent(value) {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "—";
}

function BudgetField({ label, value, onChange, disabled }) {
  return (
    <label className="rollout-budget-field">
      <span>{label}</span>
      <input type="number" min="0" step="1" value={value} placeholder="0" disabled={disabled} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

/* ---------- Inline rollout detail for a single deployment ---------- */

function InlineRolloutDetail({ deployment, team, instanceId, onSaved }) {
  const [training, setTraining] = useState(deployment.training_options.find((item) => (item.coverage || 0) >= deployment.training_pct)?.key || deployment.training_options[0]?.key || "");
  const [process, setProcess] = useState(deployment.process);
  const [communication, setCommunication] = useState(deployment.communication);
  const [trainingBudget, setTrainingBudget] = useState(deployment.training_budget ?? "");
  const [processBudget, setProcessBudget] = useState(deployment.process_budget ?? "");
  const [communicationBudget, setCommunicationBudget] = useState(deployment.communication_budget ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const readOnly = team.revision === null || team.locked_revision !== null;

  async function save() {
    if (readOnly || !training || !process || !communication) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/rollout`, {
        version: 1, expected_revision: team.revision,
        replace_categories: {
          training: [{ key: `rollout_train_${deployment.id}`, op: "train", asset: deployment.id, option: training, budget: Number(trainingBudget) || 0 }],
          process_redesign: [{ key: `rollout_process_${deployment.id}`, op: "set_process", asset: deployment.id, choice: process, budget: Number(processBudget) || 0 }],
          communication: [{ key: `rollout_communicate_${deployment.org_unit}`, op: "communicate", org_unit: deployment.org_unit, option: communication, budget: Number(communicationBudget) || 0 }],
        },
      });
      onSaved(response.data);
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The rollout decision could not be saved.");
    } finally { setSaving(false); }
  }

  return (
    <section className="rollout-inline-detail">
      <div className="rollout-inline-header">
        <div>
          <h3>{deployment.label}</h3>
          <p className="components-muted">{deployment.org_unit?.replaceAll("_", " ") || "Firm-wide"} · {deployment.people || "—"} people</p>
        </div>
        <div className="rollout-status">
          <StatusBadge status={deployment.status} />
          <span>{percent(deployment.adoption)} adoption</span>
        </div>
      </div>
      <p className="components-muted" style={{ margin: 0 }}>Current: {deployment.trained_count} trained · {deployment.process} · {deployment.communication === "none" ? "no communication" : "communicated"}</p>

      <div className="rollout-inline-controls">
        {/* Training */}
        <div>
          <h4 style={{ margin: "0 0 var(--space-sm)", fontSize: "13px" }}>Training</h4>
          <div className="choice-stack">{deployment.training_options.map((item) => <OptionRow key={item.key} label={item.label} detail={`${item.cost ? `$${item.cost.toLocaleString()}` : "$0"}${item.coverage !== null && item.coverage !== undefined ? ` · covers ${Math.round(item.coverage * 100)}%` : ""}`} selected={training === item.key} disabled={readOnly} onSelect={() => setTraining(item.key)} />)}</div>
          <BudgetField label="Training budget ($)" value={trainingBudget} onChange={setTrainingBudget} disabled={readOnly} />
        </div>

        {/* Process */}
        <div>
          <h4 style={{ margin: "0 0 var(--space-sm)", fontSize: "13px" }}>Process</h4>
          <div className="choice-stack">{deployment.process_options.map((item) => <OptionRow key={item.key} label={item.label} detail={`${item.cost ? `$${item.cost.toLocaleString()}` : "$0"}${item.coverage !== null && item.coverage !== undefined ? ` · covers ${Math.round(item.coverage * 100)}%` : ""}`} selected={process === item.key} disabled={readOnly} onSelect={() => setProcess(item.key)} />)}</div>
          <BudgetField label="Process budget ($)" value={processBudget} onChange={setProcessBudget} disabled={readOnly} />
        </div>

        {/* Communication */}
        <div>
          <h4 style={{ margin: "0 0 var(--space-sm)", fontSize: "13px" }}>Communication</h4>
          <div className="choice-stack">{deployment.communication_options.map((item) => <OptionRow key={item.key} label={item.label} detail={`${item.cost ? `$${item.cost.toLocaleString()}` : "$0"}${item.coverage !== null && item.coverage !== undefined ? ` · covers ${Math.round(item.coverage * 100)}%` : ""}`} selected={communication === item.key} disabled={readOnly} onSelect={() => setCommunication(item.key)} />)}</div>
          <BudgetField label="Communication budget ($)" value={communicationBudget} onChange={setCommunicationBudget} disabled={readOnly} />
        </div>
      </div>

      <div className="rollout-detail-actions">
        <button type="button" className="components-primary" disabled={readOnly || saving || !deployment.training_options.length} onClick={save}>{saving ? "Saving…" : "Apply to this deployment"}</button>
      </div>
      {error && <p className="components-error" role="alert">{error}</p>}
    </section>
  );
}

/* ---------- Main Rollout component ---------- */

export default function Rollout({ data, controlsData, instanceId }) {
  const [view, setView] = useState(data);
  useEffect(() => setView(data), [data]);
  const team = view?.team;

  // Build dynamic tabs from deployments, grouped by label
  const appTabs = useMemo(() => {
    if (!team?.deployments?.length) return [];
    const seen = new Map();
    for (const dep of team.deployments) {
      const tabKey = dep.id;
      if (!seen.has(tabKey)) {
        seen.set(tabKey, { key: tabKey, label: dep.label, deploymentId: dep.id });
      }
    }
    return Array.from(seen.values());
  }, [team]);

  const allTabs = useMemo(() => [...appTabs, { key: "ownership", label: "Ownership" }], [appTabs]);

  const [activeTab, setActiveTab] = useState(() => allTabs[0]?.key || "ownership");

  // Reset active tab when tabs change and current tab is no longer valid
  useEffect(() => {
    if (allTabs.length > 0 && !allTabs.find((t) => t.key === activeTab)) {
      setActiveTab(allTabs[0].key);
    }
  }, [allTabs, activeTab]);

  if (!team) return <section className="components-empty"><h2>Your team has not entered the runtime yet</h2><p>Rollout decisions will appear here after the team runtime is initialized.</p></section>;

  const activeDeployment = activeTab !== "ownership" ? team.deployments?.find((d) => d.id === activeTab) : null;

  return (
    <div className="rollout-page">
      <ContextBanner step={4} eyebrow="Getting systems into the hands of the people who use them" description="Deploy, train, and assign ownership for each capability." teamName={team.name} round={team.current_round} strategy={team.strategy} />

      {/* Dynamic tabs */}
      <div className="rollout-app-tabs" role="tablist">
        {allTabs.map((tab) => (
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === tab.key}
            className={`rollout-app-tab${activeTab === tab.key ? " rollout-app-tab--active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
            key={tab.key}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Per-application inline detail */}
      {activeDeployment && (
        <InlineRolloutDetail
          key={activeDeployment.id}
          deployment={activeDeployment}
          team={team}
          instanceId={instanceId}
          onSaved={(next) => setView(next)}
        />
      )}

      {/* Ownership tab */}
      {activeTab === "ownership" && controlsData && <GovernancePanel view={controlsData} instanceId={instanceId} />}
      {activeTab === "ownership" && !controlsData && <section className="controls-empty"><p>Ownership data is not available.</p></section>}
    </div>
  );
}
