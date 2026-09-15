/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client.js";
import { DetailTable, OptionRow, StatusBadge } from "../components/index.js";

const tabs = ["Training", "Process", "Communication"];

function percent(value) {
  return typeof value === "number" && Number.isFinite(value) ? `${Math.round(value * 100)}%` : "—";
}

function RolloutDetail({ deployment, team, instanceId, onSaved, onClose }) {
  const [tab, setTab] = useState("Training");
  const [training, setTraining] = useState(deployment.training_options.find((item) => (item.coverage || 0) >= deployment.training_pct)?.key || deployment.training_options[0]?.key || "");
  const [process, setProcess] = useState(deployment.process);
  const [communication, setCommunication] = useState(deployment.communication);
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
          training: [{ key: `rollout_train_${deployment.id}`, op: "train", asset: deployment.id, option: training }],
          process_redesign: [{ key: `rollout_process_${deployment.id}`, op: "set_process", asset: deployment.id, choice: process }],
          communication: [{ key: `rollout_communicate_${deployment.org_unit}`, op: "communicate", org_unit: deployment.org_unit, option: communication }],
        },
      });
      onSaved(response.data);
    } catch (requestError) {
      setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The rollout decision could not be saved.");
    } finally { setSaving(false); }
  }

  const options = tab === "Training" ? deployment.training_options : tab === "Process" ? deployment.process_options : deployment.communication_options;
  const selected = tab === "Training" ? training : tab === "Process" ? process : communication;
  const choose = tab === "Training" ? setTraining : tab === "Process" ? setProcess : setCommunication;
  return <section className="rollout-detail" aria-labelledby="rollout-detail-heading">
    <div className="components-panel-heading"><div><p className="eyebrow">Deployment detail</p><h2 id="rollout-detail-heading">{deployment.label} → {deployment.org_unit || "Firm-wide"} · {deployment.people || "—"} people</h2><p className="components-muted">Current: {deployment.trained_count} trained · {deployment.process} · {deployment.communication === "none" ? "no communication" : "communicated"}</p></div><button type="button" className="components-secondary" onClick={onClose}>Close</button></div>
    <div className="rollout-status"><StatusBadge status={deployment.status} /> <span>{percent(deployment.adoption)} adoption</span></div>
    <div className="components-tabs" role="tablist">{tabs.map((item) => <button type="button" role="tab" aria-selected={tab === item} className={tab === item ? "components-tab--active" : ""} onClick={() => setTab(item)} key={item}>{item}</button>)}</div>
    <div className="choice-stack">{options.map((item) => <OptionRow key={item.key} label={item.label} detail={`${item.cost ? `$${item.cost.toLocaleString()}` : "$0"}${item.coverage !== null && item.coverage !== undefined ? ` · covers ${Math.round(item.coverage * 100)}%` : ""}`} selected={selected === item.key} disabled={readOnly} onSelect={() => choose(item.key)} />)}</div>
    <div className="rollout-detail-actions"><button type="button" className="components-primary" disabled={readOnly || saving || !options.length} onClick={save}>{saving ? "Saving…" : "Apply to this deployment"}</button></div>
    {error && <p className="components-error" role="alert">{error}</p>}
  </section>;
}

export default function Rollout({ data, instanceId }) {
  const [view, setView] = useState(data);
  const [selectedId, setSelectedId] = useState(null);
  useEffect(() => setView(data), [data]);
  const team = view?.team;
  const selected = team?.deployments?.find((item) => item.id === selectedId);
  const rows = useMemo(() => (team?.deployments || []).map((deployment) => ({
    ...deployment, key: deployment.id, org_unit: deployment.org_unit?.replaceAll("_", " ") || "—",
    people: deployment.people ?? "—", trained: `${Math.round(deployment.training_pct * 100)}%`, processLabel: deployment.process,
    communicationLabel: deployment.communication === "none" ? "None" : "Done", adoption: percent(deployment.adoption), statusLabel: deployment.status === "needs-attention" ? "Needs attention" : deployment.status === "partly-done" ? "Partly done" : "Complete",
  })), [team]);
  if (!team) return <section className="components-empty"><h2>Your team has not entered the runtime yet</h2><p>Rollout decisions will appear here after the team runtime is initialized.</p></section>;
  return <div className="rollout-page">
    <section className="components-context"><div><p className="eyebrow">Getting systems into the hands of the people who use them</p><p className="components-muted">{team.name} · Round {team.current_round}</p></div></section>
    {selected && <RolloutDetail deployment={selected} team={team} instanceId={instanceId} onClose={() => setSelectedId(null)} onSaved={(next) => setView(next)} />}
    <section className="components-table-panel"><div className="components-panel-heading"><div><h2>Deployments</h2><p className="components-muted">Training, process, communication, and adoption for each active application</p></div><span className="components-muted">{rows.length} shown</span></div><DetailTable columns={[{ key: "label", label: "System" }, { key: "org_unit", label: "Unit" }, { key: "people", label: "People" }, { key: "trained", label: "Trained" }, { key: "processLabel", label: "Process" }, { key: "communicationLabel", label: "Communication" }, { key: "adoption", label: "Adoption" }, { key: "statusLabel", label: "Status" }]} rows={rows} onRowClick={(row) => setSelectedId(row.id)} /></section>
  </div>;
}
