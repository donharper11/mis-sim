/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client.js";
import { DetailTable, SplitRule, StatusBadge } from "../components/index.js";

const placementNames = { cloud: "Cloud", on_prem: "On-Premises", saas: "SaaS" };

function statusFor(utilisation) {
  if (typeof utilisation !== "number") return ["not-started", "Not measured"];
  if (utilisation >= 100) return ["needs-attention", "Needs attention"];
  if (utilisation >= 70) return ["partly-done", "Partly done"];
  return ["complete", "OK"];
}

function PlatformServiceDetail({ asset, onClose }) {
  const [status, label] = statusFor(asset.utilisation_pct);
  return (
    <section className="platform-detail-panel">
      <div className="components-panel-heading"><div><h3>{asset.label}</h3><p className="components-muted">{placementNames[asset.placement] || asset.placement} · {asset.status}</p></div><button type="button" className="components-secondary" onClick={onClose}>Close</button></div>
      {asset.utilisation_pct !== null && <><span className="platform-label">Capacity used</span><strong>{Math.round(asset.utilisation_pct)}% used</strong><div className="platform-bar"><span style={{ width: `${Math.min(100, Math.max(0, asset.utilisation_pct))}%` }} /></div></>}
      {asset.capacity_pct !== null && <p className="platform-muted">Capacity reference {asset.capacity_pct}%</p>}
      {asset.capture_enabled !== null && <p className="platform-muted">Data capture {asset.capture_enabled ? "enabled" : "disabled"} · retained {asset.storage_rounds} round{asset.storage_rounds === 1 ? "" : "s"}</p>}
      <StatusBadge status={status} label={label} />
    </section>
  );
}

export default function Platform({ data, instanceId }) {
  const [view, setView] = useState(data);
  const [serviceKey, setServiceKey] = useState("");
  const [placement, setPlacement] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  useEffect(() => setView(data), [data]);
  const team = view?.team;
  const services = team?.assets?.filter((asset) => asset.source_kind === "service") || [];
  const cloud = services.filter((a) => a.placement === "cloud");
  const onPrem = services.filter((a) => a.placement === "on_prem");
  const selectedService = useMemo(() => team?.missing_services?.find((item) => item.key === serviceKey), [team, serviceKey]);
  const selectedAsset = services.find((a) => a.id === selectedId);

  if (!team) {
    return <section className="platform-empty"><h2>Your team has not entered the runtime yet</h2><p>Platform decisions will appear here after the team runtime is initialized.</p></section>;
  }

  async function addService(event) {
    event.preventDefault();
    if (!selectedService || !placement || team.revision === null || team.locked_revision !== null) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/platform`, {
        version: 1,
        expected_revision: team.revision,
        commands: [{ key: `platform_${selectedService.key}_${placement}`, op: "buy_service", service: selectedService.key, placement, units: 1 }],
      });
      setView(response.data); setServiceKey(""); setPlacement("");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "The platform decision could not be saved.");
    } finally { setSaving(false); }
  }

  const readOnly = team.revision === null || team.locked_revision !== null;
  const showForm = !readOnly && team.missing_services.length > 0;

  const rows = services.map((asset) => {
    const [status, label] = statusFor(asset.utilisation_pct);
    return {
      ...asset,
      key: asset.id,
      placementLabel: placementNames[asset.placement] || asset.placement,
      capacity: typeof asset.utilisation_pct === "number" ? `${Math.round(asset.utilisation_pct)}%` : "—",
      statusLabel: label,
      _status: status,
    };
  });

  return (
    <div className="platform-page">
      {showForm && <section className="action-form-top">
        <h2>Provision a new service</h2>
        <form onSubmit={addService} className="platform-form">
          <label>Service<select value={serviceKey} onChange={(event) => { setServiceKey(event.target.value); setPlacement(""); }}><option value="">Choose a service</option>{team.missing_services.map((service) => <option value={service.key} key={service.key}>{service.label}</option>)}</select></label>
          <label>Placement<select value={placement} onChange={(event) => setPlacement(event.target.value)} disabled={!selectedService}><option value="">Choose a placement</option>{selectedService?.placements.map((option) => <option value={option} key={option}>{placementNames[option] || option}</option>)}</select></label>
          <button type="submit" disabled={saving || !selectedService || !placement}>{saving ? "Saving…" : "Add"}</button>
        </form>
        {error && <p className="platform-error" role="alert">{error}</p>}
      </section>}
      {readOnly && team.locked_revision !== null && <section className="review-banner"><strong>This round is locked.</strong><span>Decisions reopen when the round advances.</span></section>}
      <section className="platform-banner"><strong>Hosting posture: {cloud.length} Cloud · {onPrem.length} On-Prem{cloud.length > 0 && onPrem.length > 0 ? " (Hybrid)" : ""}</strong></section>
      {selectedAsset && <PlatformServiceDetail asset={selectedAsset} onClose={() => setSelectedId(null)} />}
      <section className="components-table-panel">
        <div className="components-panel-heading"><div><h2>Provisioned services</h2><p className="components-muted">{services.length} services active</p></div></div>
        <DetailTable columns={[{ key: "label", label: "Service" }, { key: "placementLabel", label: "Placement" }, { key: "capacity", label: "Capacity" }, { key: "statusLabel", label: "Status" }]} rows={rows} onRowClick={(row) => setSelectedId(row.id)} />
      </section>
      <SplitRule label="What determines the split?" options={team.split_rule.length ? team.split_rule : ["No placement rule recorded for this runtime"]} />
      {team.projects.length > 0 && <section className="components-projects"><h2>In-flight projects</h2>{team.projects.map((project) => <article className="components-project-row" key={project.id}><div><strong>{project.label}</strong><p>{project.status} · {project.remaining_lead} round{project.remaining_lead === 1 ? "" : "s"} remaining</p></div></article>)}</section>}
    </div>
  );
}
