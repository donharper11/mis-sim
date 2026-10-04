/* eslint-disable react/prop-types */
import { useState } from "react";
import { apiClient } from "../api/client.js";
import { StatusBadge } from "./index.js";

function percent(value) {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "—";
}

function CategorySlider({ label, options, selectedKey, onSelect, budget, onBudgetChange, disabled }) {
  const idx = options.findIndex((o) => o.key === selectedKey);
  const current = idx >= 0 ? idx : 0;
  const opt = options[current];

  return (
    <div className="rollout-slider-category">
      <span className="rollout-slider-label">{label}</span>
      <input
        type="range"
        className="rollout-slider-input"
        min={0}
        max={options.length - 1}
        step={1}
        value={current}
        disabled={disabled}
        onChange={(e) => onSelect(options[Number(e.target.value)].key)}
      />
      <span className="rollout-slider-info">
        {opt?.label}{opt?.cost ? ` · $${opt.cost.toLocaleString()}` : ""}{opt?.coverage != null ? ` · ${Math.round(opt.coverage * 100)}%` : ""}
      </span>
      <label className="rollout-slider-budget">
        <span className="sr-only">{label} budget ($)</span>
        <input
          type="number"
          min="0"
          step="1"
          value={budget}
          placeholder="0"
          disabled={disabled}
          onChange={(e) => onBudgetChange(e.target.value)}
        />
      </label>
    </div>
  );
}

export default function RolloutSlider({ deployment, team, instanceId, onSaved }) {
  const [training, setTraining] = useState(
    deployment.training_options.find((item) => (item.coverage || 0) >= deployment.training_pct)?.key || deployment.training_options[0]?.key || ""
  );
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
      <div className="rollout-two-col">
        <div className="rollout-inline-controls">
          <CategorySlider
            label="Training"
            options={deployment.training_options}
            selectedKey={training}
            onSelect={setTraining}
            budget={trainingBudget}
            onBudgetChange={setTrainingBudget}
            disabled={readOnly}
          />
          <CategorySlider
            label="Process"
            options={deployment.process_options}
            selectedKey={process}
            onSelect={setProcess}
            budget={processBudget}
            onBudgetChange={setProcessBudget}
            disabled={readOnly}
          />
          <CategorySlider
            label="Communication"
            options={deployment.communication_options}
            selectedKey={communication}
            onSelect={setCommunication}
            budget={communicationBudget}
            onBudgetChange={setCommunicationBudget}
            disabled={readOnly}
          />
        </div>

        {/* Previous round summary */}
        <aside className="rollout-prev-round">
          <h4 style={{ margin: "0 0 var(--space-md)", fontSize: "13px" }}>Current State</h4>
          <div className="rollout-prev-items">
            <div className="rollout-prev-item">
              <span className="rollout-prev-label">Training</span>
              <span className="rollout-prev-value">{deployment.trained_count} trained ({percent(deployment.training_pct)})</span>
            </div>
            <div className="rollout-prev-item">
              <span className="rollout-prev-label">Process</span>
              <span className="rollout-prev-value">{deployment.process === "unchanged" ? "Unchanged" : deployment.process === "partial" ? "Partial redesign" : deployment.process === "redesigned" ? "Redesigned" : deployment.process}</span>
            </div>
            <div className="rollout-prev-item">
              <span className="rollout-prev-label">Communication</span>
              <span className="rollout-prev-value">{deployment.communication === "none" ? "None" : deployment.communication}</span>
            </div>
            <div className="rollout-prev-item">
              <span className="rollout-prev-label">Adoption</span>
              <span className="rollout-prev-value">{percent(deployment.adoption)}</span>
            </div>
            <div className="rollout-prev-item">
              <span className="rollout-prev-label">Budget (training)</span>
              <span className="rollout-prev-value">{typeof deployment.training_budget === "number" ? `$${deployment.training_budget.toLocaleString()}` : "—"}</span>
            </div>
            <div className="rollout-prev-item">
              <span className="rollout-prev-label">Budget (process)</span>
              <span className="rollout-prev-value">{typeof deployment.process_budget === "number" ? `$${deployment.process_budget.toLocaleString()}` : "—"}</span>
            </div>
            <div className="rollout-prev-item">
              <span className="rollout-prev-label">Budget (comms)</span>
              <span className="rollout-prev-value">{typeof deployment.communication_budget === "number" ? `$${deployment.communication_budget.toLocaleString()}` : "—"}</span>
            </div>
          </div>
        </aside>
      </div>

      <div className="rollout-detail-actions">
        <button type="button" className="components-primary" disabled={readOnly || saving || !deployment.training_options.length} onClick={save}>{saving ? "Saving…" : "Apply to this deployment"}</button>
      </div>
      {error && <p className="components-error" role="alert">{error}</p>}
    </section>
  );
}
