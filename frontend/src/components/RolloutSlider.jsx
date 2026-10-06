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

function CategoryCard({ category, options, selectedKey, onSelect, disabled }) {
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
          disabled={disabled || !options.length}
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

    </div>
  );
}

function fmt$(n) { return n >= 1000 ? `$${(n / 1000).toFixed(n % 1000 === 0 ? 0 : 1)}K` : `$${n}`; }
const placementNames = { cloud: "Cloud", on_prem: "On-Premises", saas: "SaaS" };

export default function RolloutSlider({ deployment, team, instanceId, onSaved, onViewPlatform }) {
  const initialValues = useMemo(() => ({
    training: team.selected_commands?.find((c) => c.op === "train" && c.asset === deployment.id)?.option
      || deployment.training_options.find((item) => (item.coverage || 0) >= deployment.training_pct)?.key || deployment.training_options[0]?.key || "",
    process: team.selected_commands?.find((c) => c.op === "set_process" && c.asset === deployment.id)?.choice || deployment.process,
    communication: team.selected_commands?.find((c) => c.op === "communicate" && c.org_unit === deployment.org_unit)?.option || deployment.communication,
  }), [deployment, team.selected_commands]);

  const [training, setTraining] = useState(initialValues.training);
  const [process, setProcess] = useState(initialValues.process);
  const [communication, setCommunication] = useState(initialValues.communication);
  useEffect(() => {
    setTraining(initialValues.training);
    setProcess(initialValues.process);
    setCommunication(initialValues.communication);
  }, [initialValues]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [revisionConflict, setRevisionConflict] = useState(false);
  const readOnly = team.revision === null || team.locked_revision !== null;

  function reset() {
    setTraining(initialValues.training);
    setProcess(initialValues.process);
    setCommunication(initialValues.communication);
    setError("");
    setRevisionConflict(false);
  }

  async function save() {
    if (readOnly || !training || !process || !communication) return;
    setSaving(true); setError(""); setRevisionConflict(false);
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/rollout`, {
        version: 1, expected_revision: team.revision,
        replace_categories: {
          training: [
            ...(team.selected_commands || []).filter((c) => c.op === "train" && c.asset !== deployment.id),
            { key: `rollout_train_${deployment.id}`, op: "train", asset: deployment.id, option: training },
          ],
          process_redesign: [
            ...(team.selected_commands || []).filter((c) => c.op === "set_process" && c.asset !== deployment.id),
            { key: `rollout_process_${deployment.id}`, op: "set_process", asset: deployment.id, choice: process },
          ],
          communication: [
            ...(team.selected_commands || []).filter((c) => c.op === "communicate" && c.org_unit !== deployment.org_unit),
            { key: `rollout_communicate_${deployment.org_unit}`, op: "communicate", org_unit: deployment.org_unit, option: communication },
          ],
        },
      });
      onSaved(response.data);
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      const conflict = detail?.code === "revision_conflict";
      setRevisionConflict(conflict);
      setError(conflict ? "Another save changed this round. Your choices are still shown here. Reload the latest decisions before trying again; reloading discards these unsaved choices." : typeof detail === "string" ? detail : "The rollout decision could not be saved.");
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

      {/* Deployment metadata */}
      {(deployment.platform_code || deployment.capex || deployment.opex) && (
        <div className="rollout-deployment-meta">
          {deployment.platform_code && (
            <span>
              Platform: {deployment.platform_code} &middot; {deployment.platform_name || "—"}
              {onViewPlatform && deployment.platform_id && (
                <>
                  {" "}
                  <button type="button" className="rollout-deployment-meta__link" onClick={() => onViewPlatform(deployment.platform_id)}>view &#x2197;</button>
                </>
              )}
            </span>
          )}
          {deployment.org_unit && <span>BU: {deployment.org_unit.replaceAll("_", " ")}</span>}
          {deployment.placement && <span>Placement: {placementNames[deployment.placement] || deployment.placement}</span>}
          {deployment.capex > 0 && <span>Setup: {fmt$(deployment.capex)} CAPEX</span>}
          {deployment.opex > 0 && <span>OPEX: {fmt$(deployment.opex)}/round</span>}
        </div>
      )}

      <div className="rollout-category-cards">
        <CategoryCard
          category="training"
          options={deployment.training_options}
          selectedKey={training}
          onSelect={setTraining}
          disabled={readOnly}
        />
        <CategoryCard
          category="process"
          options={deployment.process_options}
          selectedKey={process}
          onSelect={setProcess}
          disabled={readOnly}
        />
        <CategoryCard
          category="communication"
          options={deployment.communication_options}
          selectedKey={communication}
          onSelect={setCommunication}
          disabled={readOnly}
        />
      </div>

      <div className="rollout-detail-actions">
        <button type="button" className="components-secondary" disabled={readOnly} onClick={reset}>Reset</button>
        <button type="button" className="components-primary" disabled={readOnly || saving || !deployment.training_options.length} onClick={save}>{saving ? "Saving…" : "Save Changes"}</button>
      </div>
      {error && <p className="components-error" role="alert">{error}</p>}
      {revisionConflict && <button type="button" className="components-secondary" onClick={() => window.location.reload()}>Reload latest decisions</button>}
    </section>
  );
}
