/* eslint-disable react/prop-types */
import { useEffect, useState, useMemo } from "react";
import { Slider } from "antd";
import { GraduationCap, Cog, Megaphone } from "lucide-react";
import { apiClient } from "../api/client.js";
import { StatusBadge } from "./index.js";

function percent(value) {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "—";
}

const categoryMeta = {
  training: { icon: GraduationCap, label: "Training" },
  process: { icon: Cog, label: "Process" },
  communication: { icon: Megaphone, label: "Communication" },
};

function CategoryCard({ category, options, selectedKey, onSelect, budget, onBudgetChange, disabled }) {
  const meta = categoryMeta[category];
  const Icon = meta.icon;
  const idx = options.findIndex((o) => o.key === selectedKey);
  const snappedIdx = idx >= 0 ? idx : 0;
  const segSize = 100 / Math.max(options.length - 1, 1);
  const [rawVal, setRawVal] = useState(snappedIdx * segSize);

  useEffect(() => {
    const i = options.findIndex((o) => o.key === selectedKey);
    if (i >= 0) setRawVal(i * segSize);
  }, [selectedKey, options, segSize]);

  const nearestIdx = Math.min(Math.round(rawVal / segSize), options.length - 1);
  const opt = options[nearestIdx];
  const marks = options.reduce((acc, _o, i) => { acc[i * segSize] = Math.round(i * segSize); return acc; }, {});

  return (
    <div className="rollout-category-card">
      <div className="rollout-category-card__icon"><Icon size={32} /></div>
      <div className="rollout-category-card__label">{meta.label}</div>
      <div className="rollout-category-card__slider">
        <Slider
          min={0}
          max={100}
          step={1}
          value={rawVal}
          marks={marks}
          disabled={disabled}
          tooltip={{ formatter: (v) => Math.round(v) }}
          onChange={(val) => setRawVal(val)}
          onChangeComplete={(val) => {
            const nearest = Math.min(Math.round(val / segSize), options.length - 1);
            setRawVal(nearest * segSize);
            onSelect(options[nearest].key);
          }}
        />
      </div>
      <div className="rollout-category-card__desc">{opt?.label || "—"}</div>
      <div className="rollout-category-card__info">
        {opt?.cost ? `$${opt.cost.toLocaleString()}` : "$0"}{opt?.coverage != null ? ` · ${Math.round(opt.coverage * 100)}%` : ""}
      </div>
      <div className="rollout-category-card__budget">
        <label>
          Budget ($)
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
    </div>
  );
}

export default function RolloutSlider({ deployment, team, instanceId, onSaved }) {
  const initialValues = useMemo(() => ({
    training: deployment.training_options.find((item) => (item.coverage || 0) >= deployment.training_pct)?.key || deployment.training_options[0]?.key || "",
    process: deployment.process,
    communication: deployment.communication,
    trainingBudget: deployment.training_budget ?? "",
    processBudget: deployment.process_budget ?? "",
    communicationBudget: deployment.communication_budget ?? "",
  }), [deployment]);

  const [training, setTraining] = useState(initialValues.training);
  const [process, setProcess] = useState(initialValues.process);
  const [communication, setCommunication] = useState(initialValues.communication);
  const [trainingBudget, setTrainingBudget] = useState(initialValues.trainingBudget);
  const [processBudget, setProcessBudget] = useState(initialValues.processBudget);
  const [communicationBudget, setCommunicationBudget] = useState(initialValues.communicationBudget);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const readOnly = team.revision === null || team.locked_revision !== null;

  function reset() {
    setTraining(initialValues.training);
    setProcess(initialValues.process);
    setCommunication(initialValues.communication);
    setTrainingBudget(initialValues.trainingBudget);
    setProcessBudget(initialValues.processBudget);
    setCommunicationBudget(initialValues.communicationBudget);
    setError("");
  }

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

      <div className="rollout-category-cards">
        <CategoryCard
          category="training"
          options={deployment.training_options}
          selectedKey={training}
          onSelect={setTraining}
          budget={trainingBudget}
          onBudgetChange={setTrainingBudget}
          disabled={readOnly}
        />
        <CategoryCard
          category="process"
          options={deployment.process_options}
          selectedKey={process}
          onSelect={setProcess}
          budget={processBudget}
          onBudgetChange={setProcessBudget}
          disabled={readOnly}
        />
        <CategoryCard
          category="communication"
          options={deployment.communication_options}
          selectedKey={communication}
          onSelect={setCommunication}
          budget={communicationBudget}
          onBudgetChange={setCommunicationBudget}
          disabled={readOnly}
        />
      </div>

      <div className="rollout-detail-actions">
        <button type="button" className="components-secondary" disabled={readOnly} onClick={reset}>Reset</button>
        <button type="button" className="components-primary" disabled={readOnly || saving || !deployment.training_options.length} onClick={save}>{saving ? "Saving…" : "Save Changes"}</button>
      </div>
      {error && <p className="components-error" role="alert">{error}</p>}
    </section>
  );
}
