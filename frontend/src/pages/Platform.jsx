/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client.js";
import { SplitRule, StatusBadge } from "../components/index.js";

const placementNames = { cloud: "Cloud", on_prem: "On-Premises", saas: "SaaS" };

function statusFor(utilisation) {
  if (typeof utilisation !== "number") return ["not-started", "Not measured"];
  if (utilisation >= 100) return ["needs-attention", "Needs attention"];
  if (utilisation >= 70) return ["partly-done", "Partly done"];
  return ["complete", "Complete"];
}

function PlatformService({ asset }) {
  const [status, label] = statusFor(asset.utilisation_pct);
  return (
    <article className="platform-service">
      <h3>{asset.label}</h3>
      <p>{placementNames[asset.placement] || asset.placement} · {asset.status}</p>
      {asset.utilisation_pct !== null && <><span className="platform-label">Capacity used</span><strong>{Math.round(asset.utilisation_pct)}% used</strong><div className="platform-bar"><span style={{ width: `${Math.min(100, Math.max(0, asset.utilisation_pct))}%` }} /></div></>}
      {asset.capacity_pct !== null && <p className="platform-muted">Capacity reference {asset.capacity_pct}%</p>}
      {asset.capture_enabled !== null && <p className="platform-muted">Data capture {asset.capture_enabled ? "enabled" : "disabled"} · retained {asset.storage_rounds} round{asset.storage_rounds === 1 ? "" : "s"}</p>}
      <StatusBadge status={status} label={label} />
    </article>
  );
}

function EmptyHosting({ label }) {
  return <div className="platform-hosting-empty"><h2>{label}</h2><p>Nothing is provisioned yet. Start with somewhere to run things.</p><StatusBadge status="not-started" /></div>;
}

export default function Platform({ data, instanceId }) {
  const [view, setView] = useState(data);
  const [serviceKey, setServiceKey] = useState("");
  const [placement, setPlacement] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => setView(data), [data]);
  const team = view?.team;
  const cloud = team?.assets?.filter((asset) => asset.source_kind === "service" && asset.placement === "cloud") || [];
  const onPrem = team?.assets?.filter((asset) => asset.source_kind === "service" && asset.placement === "on_prem") || [];
  const selectedService = useMemo(() => team?.missing_services?.find((item) => item.key === serviceKey), [team, serviceKey]);

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

  return (
    <div className="platform-page">
      <section className="platform-context">
        <div><p className="eyebrow">What the whole firm runs on</p><p className="platform-muted">{team.name} · Round {team.current_round}</p></div>
        {team.strategy && <span className="dashboard-context__chip">{team.strategy}</span>}
      </section>
      <section className="platform-banner"><strong>{team.assets.some((asset) => asset.placement === "cloud") && team.assets.some((asset) => asset.placement === "on_prem") ? "You are running a hybrid platform." : "Your current hosting posture is recorded below."}</strong><span>{cloud.length} cloud · {onPrem.length} on-premises</span></section>
      <section className="platform-hosting">
        <div className="platform-panel"><h2>Cloud</h2>{cloud.length ? cloud.map((asset) => <PlatformService asset={asset} key={asset.id} />) : <EmptyHosting label="Cloud" />}</div>
        <div className="platform-panel"><h2>On-Premises</h2>{onPrem.length ? onPrem.map((asset) => <PlatformService asset={asset} key={asset.id} />) : <EmptyHosting label="On-Premises" />}</div>
      </section>
      <section className="platform-missing"><h2>Not provisioned</h2>{team.missing_services.length ? <div className="platform-missing-grid">{team.missing_services.map((service) => <article key={service.key}><h3>{service.label}</h3><p>Nothing provides this yet</p><StatusBadge status="not-started" /></article>)}</div> : <p className="platform-muted">Every registered firm-wide service is provisioned.</p>}</section>
      <SplitRule label="What determines the split?" options={team.split_rule.length ? team.split_rule : ["No placement rule recorded for this runtime"]} />
      <section className="platform-summary"><span>{team.connections.length} connections between systems</span><span>{team.projects.length} in-flight platform projects</span></section>
      <section className="platform-actions">
        <h2>Add firm-wide service</h2>
        {team.revision === null ? <p className="platform-muted">Platform decisions are unavailable until this team has an initialized versioned runtime.</p> : team.locked_revision !== null ? <p className="platform-muted">This round is locked. Decisions reopen when the round advances.</p> : team.missing_services.length === 0 ? <p className="platform-muted">There are no unprovisioned firm-wide services in this casepack.</p> : (
          <form onSubmit={addService} className="platform-form">
            <label>Service<select value={serviceKey} onChange={(event) => { setServiceKey(event.target.value); setPlacement(""); }}><option value="">Choose a service</option>{team.missing_services.map((service) => <option value={service.key} key={service.key}>{service.label}</option>)}</select></label>
            <label>Placement<select value={placement} onChange={(event) => setPlacement(event.target.value)} disabled={!selectedService}><option value="">Choose a placement</option>{selectedService?.placements.map((option) => <option value={option} key={option}>{placementNames[option] || option}</option>)}</select></label>
            <button type="submit" disabled={saving || !selectedService || !placement}>{saving ? "Saving…" : "Add firm-wide service"}</button>
          </form>
        )}
        {error && <p className="platform-error" role="alert">{error}</p>}
      </section>
    </div>
  );
}
