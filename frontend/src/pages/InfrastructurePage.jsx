/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client.js";
import { ContextBanner, DetailTable, StatusBadge } from "../components/index.js";

const placementNames = { cloud: "Cloud", on_prem: "On-Premises", saas: "SaaS" };
const typeLabels = { on_prem: "On-Premises", cloud: "Cloud" };
const subtypeLabels = { iaas: "IaaS", paas: "PaaS", saas: "SaaS", aiaas: "AIaaS" };
const statusBadgeMap = { active: ["complete", "Active"], pending: ["info", "Pending"], retired: ["neutral", "Retired"] };

function statusFor(utilisation) {
  if (typeof utilisation !== "number") return ["not-started", "Not measured"];
  if (utilisation >= 100) return ["needs-attention", "Needs attention"];
  if (utilisation >= 70) return ["partly-done", "Partly done"];
  return ["complete", "OK"];
}

/* ---------- New platform form (inline) ---------- */

function NewPlatformForm({ instanceId, onCreated, onCancel }) {
  const [platformType, setPlatformType] = useState("");
  const [cloudSubtype, setCloudSubtype] = useState("");
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function create(event) {
    event.preventDefault();
    if (!platformType || !name.trim()) return;
    if (platformType === "cloud" && !cloudSubtype) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.post(`/instances/${instanceId}/host-platforms`, {
        platform_type: platformType,
        cloud_subtype: platformType === "cloud" ? cloudSubtype : null,
        name: name.trim(),
        notes: notes.trim() || null,
      });
      onCreated(response.data.platforms);
      setPlatformType(""); setCloudSubtype(""); setName(""); setNotes("");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not create the platform.");
    } finally { setSaving(false); }
  }

  return (
    <section className="action-form-top">
      <h2>Set up new host platform</h2>
      <form onSubmit={create} className="host-platform-form">
        <label>Type
          <select value={platformType} onChange={(e) => { setPlatformType(e.target.value); setCloudSubtype(""); }}>
            <option value="">Choose…</option>
            <option value="on_prem">On-Premises</option>
            <option value="cloud">Cloud</option>
          </select>
        </label>
        {platformType === "cloud" && (
          <label>Cloud subtype
            <select value={cloudSubtype} onChange={(e) => setCloudSubtype(e.target.value)}>
              <option value="">Choose…</option>
              <option value="iaas">IaaS</option>
              <option value="paas">PaaS</option>
              <option value="saas">SaaS</option>
              <option value="aiaas">AIaaS</option>
            </select>
          </label>
        )}
        <label>Name
          <input type="text" value={name} maxLength={200} placeholder="e.g. Primary data center" onChange={(e) => setName(e.target.value)} />
        </label>
        <label>Notes
          <textarea value={notes} maxLength={1000} placeholder="Optional notes about this platform" onChange={(e) => setNotes(e.target.value)} />
        </label>
        <div className="host-platform-form-actions">
          <button type="button" className="components-secondary" onClick={onCancel}>Cancel</button>
          <button type="submit" className="components-primary" disabled={saving || !platformType || !name.trim() || (platformType === "cloud" && !cloudSubtype)}>{saving ? "Creating…" : "Create"}</button>
        </div>
      </form>
      {error && <p className="platform-error" role="alert">{error}</p>}
    </section>
  );
}

/* ---------- Add member form ---------- */

function AddMemberForm({ platformId, instanceId, memberKind, onAdded, availableAssets }) {
  const [assetKey, setAssetKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function add(event) {
    event.preventDefault();
    if (!assetKey) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.post(`/instances/${instanceId}/host-platforms/${platformId}/members`, {
        asset_key: assetKey,
        member_kind: memberKind,
      });
      onAdded(response.data.platforms);
      setAssetKey("");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Could not assign member.");
    } finally { setSaving(false); }
  }

  return (
    <form onSubmit={add} style={{ display: "flex", gap: "var(--space-sm)", alignItems: "end" }}>
      <select value={assetKey} onChange={(e) => setAssetKey(e.target.value)} style={{ flex: 1, minHeight: "2.5rem", padding: "var(--space-sm) var(--space-md)", border: "1px solid var(--input-border)" }}>
        <option value="">Choose a {memberKind}…</option>
        {availableAssets.map((a) => <option key={a.id} value={a.source_key || a.id}>{a.label}</option>)}
      </select>
      <button type="submit" className="components-primary" disabled={saving || !assetKey} style={{ whiteSpace: "nowrap" }}>{saving ? "Adding…" : "Add"}</button>
      {error && <p className="platform-error" role="alert" style={{ margin: 0, fontSize: "13px" }}>{error}</p>}
    </form>
  );
}

/* ---------- Platform card ---------- */

function PlatformCard({ platform, team, instanceId, controlsData, onPlatformsUpdated }) {
  const [badgeStatus, badgeLabel] = statusBadgeMap[platform.status] || ["neutral", platform.status];
  const services = platform.members.filter((m) => m.member_kind === "service");
  const components = platform.members.filter((m) => m.member_kind === "component");
  const readOnly = !team || team.revision === null || team.locked_revision !== null;
  const isActive = platform.status === "active";
  const isPending = platform.status === "pending";

  const teamAssets = team?.assets || [];
  const assignedKeys = new Set(platform.members.map((m) => m.asset_key));

  const unassignedServices = teamAssets.filter((a) => a.source_kind === "service" && a.status === "active" && !assignedKeys.has(a.source_key) && !assignedKeys.has(a.id));
  const unassignedComponents = teamAssets.filter((a) => a.source_kind === "catalog" && a.status === "active" && !assignedKeys.has(a.source_key) && !assignedKeys.has(a.id));

  function serviceRow(member) {
    const asset = teamAssets.find((a) => a.source_key === member.asset_key || a.id === member.asset_key);
    if (!asset) return { key: member.id, name: member.asset_key, id: member.asset_key, capacity: "—", utilisation: "—", status: "—", capture: "—" };
    const [, statusLabel] = statusFor(asset.utilisation_pct);
    return {
      key: member.id,
      name: asset.label,
      id: asset.id,
      capacity: typeof asset.capacity_pct === "number" ? `${asset.capacity_pct}%` : "—",
      utilisation: typeof asset.utilisation_pct === "number" ? `${Math.round(asset.utilisation_pct)}%` : "—",
      status: statusLabel,
      capture: asset.capture_enabled ? "On" : asset.capture_enabled === false ? "Off" : "—",
    };
  }

  function componentRow(member) {
    const asset = teamAssets.find((a) => a.source_key === member.asset_key || a.id === member.asset_key);
    if (!asset) return { key: member.id, name: member.asset_key, id: member.asset_key, installed: "—", placement: "—", config: "—", adoption: "—" };
    return {
      key: member.id,
      name: asset.label,
      id: asset.id,
      installed: `R${asset.installed_round}`,
      placement: placementNames[asset.placement] || asset.placement,
      config: asset.config || "—",
      adoption: typeof asset.adoption === "number" ? `${Math.round(asset.adoption * 100)}%` : "—",
    };
  }

  return (
    <section className="host-platform-card">
      <div className="host-platform-card__header">
        <div>
          <span className="host-platform-card__code">{platform.platform_code}</span>
          <strong>{platform.name}</strong>
          <span className={`host-platform-type-badge host-platform-type-badge--${platform.platform_type}`}>
            {typeLabels[platform.platform_type] || platform.platform_type}
            {platform.cloud_subtype ? ` · ${subtypeLabels[platform.cloud_subtype] || platform.cloud_subtype}` : ""}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)" }}>
          {isPending && <span className="components-muted">Available next round</span>}
          <StatusBadge status={badgeStatus} label={badgeLabel} />
        </div>
      </div>
      {platform.notes && <p className="components-muted" style={{ margin: 0 }}>{platform.notes}</p>}

      {/* Services table */}
      {services.length > 0 && (
        <div className="host-platform-card__section">
          <h3>Services ({services.length}/5)</h3>
          <div className="detail-table-wrap">
            <table className="detail-table">
              <thead><tr><th>Name</th><th>ID</th><th>Capacity</th><th>Utilization</th><th>Status</th><th>Data capture</th></tr></thead>
              <tbody>{services.map((m) => { const r = serviceRow(m); return <tr key={r.key}><td>{r.name}</td><td>{r.id}</td><td>{r.capacity}</td><td>{r.utilisation}</td><td>{r.status}</td><td>{r.capture}</td></tr>; })}</tbody>
            </table>
          </div>
        </div>
      )}

      {/* Components table */}
      {components.length > 0 && (
        <div className="host-platform-card__section">
          <h3>Components ({components.length}/5)</h3>
          <div className="detail-table-wrap">
            <table className="detail-table">
              <thead><tr><th>Name</th><th>ID</th><th>Installed</th><th>Placement</th><th>Config</th><th>Adoption</th></tr></thead>
              <tbody>{components.map((m) => { const r = componentRow(m); return <tr key={r.key}><td>{r.name}</td><td>{r.id}</td><td>{r.installed}</td><td>{r.placement}</td><td>{r.config}</td><td>{r.adoption}</td></tr>; })}</tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add buttons */}
      {isActive && !readOnly && (
        <div className="host-platform-card__actions">
          {services.length < 5 && unassignedServices.length > 0 && (
            <AddMemberForm platformId={platform.id} instanceId={instanceId} memberKind="service" availableAssets={unassignedServices} onAdded={onPlatformsUpdated} />
          )}
          {components.length < 5 && unassignedComponents.length > 0 && (
            <AddMemberForm platformId={platform.id} instanceId={instanceId} memberKind="component" availableAssets={unassignedComponents} onAdded={onPlatformsUpdated} />
          )}
        </div>
      )}
    </section>
  );
}

/* ---------- Add service form (existing buy_service flow) ---------- */

function AddServiceForm({ team, instanceId, onSaved }) {
  const [serviceKey, setServiceKey] = useState("");
  const [placement, setPlacement] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const selectedService = useMemo(() => team?.missing_services?.find((item) => item.key === serviceKey), [team, serviceKey]);

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
      onSaved(response.data); setServiceKey(""); setPlacement("");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "The platform decision could not be saved.");
    } finally { setSaving(false); }
  }

  return (
    <section className="action-form-top">
      <h2>Provision a new service</h2>
      <form onSubmit={addService} className="platform-form">
        <label>Service<select value={serviceKey} onChange={(event) => { setServiceKey(event.target.value); setPlacement(""); }}><option value="">Choose a service</option>{team.missing_services.map((service) => <option value={service.key} key={service.key}>{service.label}</option>)}</select></label>
        <label>Placement<select value={placement} onChange={(event) => setPlacement(event.target.value)} disabled={!selectedService}><option value="">Choose a placement</option>{selectedService?.placements.map((option) => <option value={option} key={option}>{placementNames[option] || option}</option>)}</select></label>
        <button type="submit" disabled={saving || !selectedService || !placement}>{saving ? "Saving…" : "Add"}</button>
      </form>
      {error && <p className="platform-error" role="alert">{error}</p>}
    </section>
  );
}

/* ---------- Main page ---------- */

export default function InfrastructurePage({ platformData, controlsData, instanceId, hostPlatforms: initialHostPlatforms }) {
  const [view, setView] = useState(platformData);
  const [hostPlatforms, setHostPlatforms] = useState(initialHostPlatforms || []);
  const [showNewPlatformForm, setShowNewPlatformForm] = useState(false);
  const [showAddService, setShowAddService] = useState(false);
  useEffect(() => setView(platformData), [platformData]);
  useEffect(() => { if (initialHostPlatforms) setHostPlatforms(initialHostPlatforms); }, [initialHostPlatforms]);

  const team = view?.team;
  const controlsTeam = controlsData?.team;
  const displayTeam = team || controlsTeam;

  if (!displayTeam) return <section className="controls-empty"><h2>Your team has not entered the runtime yet</h2><p>Infrastructure decisions will appear here after the team runtime is initialized.</p></section>;

  const services = team?.assets?.filter((asset) => asset.source_kind === "service") || [];
  const components = team?.assets?.filter((asset) => asset.source_kind === "catalog") || [];
  const readOnly = !team || team.revision === null || team.locked_revision !== null;
  const canAdd = !readOnly && team?.missing_services?.length > 0;

  // Figure out which assets are not assigned to any platform
  const allAssignedKeys = new Set(hostPlatforms.flatMap((p) => p.members.map((m) => m.asset_key)));
  const unassignedServices = services.filter((a) => a.status === "active" && !allAssignedKeys.has(a.source_key) && !allAssignedKeys.has(a.id));
  const unassignedComponents = components.filter((a) => a.status === "active" && !allAssignedKeys.has(a.source_key) && !allAssignedKeys.has(a.id));

  return (
    <div className="controls-page">
      <ContextBanner description="Platform services, staffing, and data governance for the entire firm." />

      {readOnly && team?.locked_revision !== null && <section className="review-banner"><strong>This round is locked.</strong><span>Decisions reopen when the round advances.</span></section>}

      {/* Toolbar with action buttons */}
      <section className="components-toolbar">
        <div />
        <div style={{ display: "flex", gap: "var(--space-sm)" }}>
          {canAdd && !showAddService && <button type="button" className="components-secondary" onClick={() => setShowAddService(true)}>+ Provision a service</button>}
          {!readOnly && !showNewPlatformForm && <button type="button" className="components-primary" onClick={() => setShowNewPlatformForm(true)}>+ New host platform</button>}
        </div>
      </section>

      {/* New platform form */}
      {showNewPlatformForm && (
        <NewPlatformForm
          instanceId={instanceId}
          onCreated={(platforms) => { setHostPlatforms(platforms); setShowNewPlatformForm(false); }}
          onCancel={() => setShowNewPlatformForm(false)}
        />
      )}

      {/* Platform cards */}
      {hostPlatforms.length > 0 && hostPlatforms.map((platform) => (
        <PlatformCard
          key={platform.id}
          platform={platform}
          team={team}
          instanceId={instanceId}
          controlsData={controlsData}
          onPlatformsUpdated={setHostPlatforms}
        />
      ))}

      {/* Provision service (existing buy_service flow) */}
      {showAddService && canAdd && <AddServiceForm team={team} instanceId={instanceId} onSaved={(next) => { setView(next); setShowAddService(false); }} />}

      {/* Unassigned services */}
      {unassignedServices.length > 0 && (
        <section className="controls-panel">
          <h2>Unassigned Services</h2>
          <p className="components-muted">These services are not assigned to any host platform.</p>
          <div className="detail-table-wrap">
            <table className="detail-table">
              <thead><tr><th>Service</th><th>Placement</th><th>Status</th></tr></thead>
              <tbody>{unassignedServices.map((asset) => {
                const [, label] = statusFor(asset.utilisation_pct);
                return <tr key={asset.id}><td>{asset.label}</td><td>{placementNames[asset.placement] || asset.placement}</td><td>{label}</td></tr>;
              })}</tbody>
            </table>
          </div>
        </section>
      )}

      {/* Unassigned components */}
      {unassignedComponents.length > 0 && (
        <section className="controls-panel">
          <h2>Unassigned Components</h2>
          <p className="components-muted">These components are not assigned to any host platform.</p>
          <div className="detail-table-wrap">
            <table className="detail-table">
              <thead><tr><th>Component</th><th>Placement</th><th>Status</th></tr></thead>
              <tbody>{unassignedComponents.map((asset) => <tr key={asset.id}><td>{asset.label}</td><td>{placementNames[asset.placement] || asset.placement}</td><td>{asset.status}</td></tr>)}</tbody>
            </table>
          </div>
        </section>
      )}

      {/* Empty state */}
      {hostPlatforms.length === 0 && services.length === 0 && !showNewPlatformForm && (
        <section className="controls-empty">
          <h2>No platforms or services yet</h2>
          <p>Set up your first host platform or provision a service to get started.</p>
        </section>
      )}
    </div>
  );
}
