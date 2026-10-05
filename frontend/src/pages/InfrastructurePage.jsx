/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client.js";
import { ContextBanner, DetailTable, StatusBadge } from "../components/index.js";

const placementNames = { cloud: "Cloud", on_prem: "On-Premises", saas: "SaaS" };
const typeLabels = { on_prem: "On-Premises", cloud: "Cloud" };
const subtypeLabels = { iaas: "IaaS", paas: "PaaS", saas: "SaaS", aiaas: "AIaaS" };
const statusBadgeMap = { active: ["complete", "Active"], pending: ["info", "Pending"], retired: ["neutral", "Retired"] };
const modelBadgeColors = { iaas: "var(--status-info-bg)", paas: "var(--status-ok-bg)", saas: "var(--p-purple-100, #ede9fe)", aiaas: "var(--p-amber-100, #fef3c7)" };
const modelBadgeTextColors = { iaas: "var(--status-info-text)", paas: "var(--status-ok-text)", saas: "var(--p-purple-700, #6d28d9)", aiaas: "var(--p-amber-700, #b45309)" };

function fmt$(n) { return n >= 1000 ? `$${(n / 1000).toFixed(n % 1000 === 0 ? 0 : 1)}K` : `$${n}`; }

function statusFor(utilisation) {
  if (typeof utilisation !== "number") return ["not-started", "Not measured"];
  if (utilisation >= 100) return ["needs-attention", "Needs attention"];
  if (utilisation >= 70) return ["partly-done", "Partly done"];
  return ["complete", "OK"];
}

/* ---------- Service model badge ---------- */

function ServiceModelBadge({ model }) {
  if (!model) return null;
  const label = (model || "").toUpperCase();
  return (
    <span className="service-model-badge" style={{ background: modelBadgeColors[model] || "var(--surface-sunken)", color: modelBadgeTextColors[model] || "var(--text-secondary)" }}>
      {label}
    </span>
  );
}

/* ---------- New platform form ---------- */

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
            <option value="">Choose...</option>
            <option value="on_prem">On-Premises</option>
            <option value="cloud">Cloud</option>
          </select>
        </label>
        {platformType === "cloud" && (
          <label>Cloud subtype
            <select value={cloudSubtype} onChange={(e) => setCloudSubtype(e.target.value)}>
              <option value="">Choose...</option>
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
          <button type="submit" className="components-primary" disabled={saving || !platformType || !name.trim() || (platformType === "cloud" && !cloudSubtype)}>{saving ? "Creating..." : "Create"}</button>
        </div>
      </form>
      {error && <p className="platform-error" role="alert">{error}</p>}
    </section>
  );
}

/* ---------- Categorized service catalog browser ---------- */

function ServiceCatalogBrowser({ platform, team, instanceId, categories, onProvisioned, onCancel }) {
  const [expanded, setExpanded] = useState(null);
  const [selectedPlacements, setSelectedPlacements] = useState({});
  const [provisioning, setProvisioning] = useState(null);
  const [error, setError] = useState("");

  const availableServices = team?.available_services || [];
  const activeServiceKeys = new Set((team?.assets || []).filter((a) => a.source_kind === "service" && a.status === "active").map((a) => a.source_key));
  const missingServices = availableServices.filter((s) => !activeServiceKeys.has(s.key));

  // Group by infrastructure_category
  const grouped = useMemo(() => {
    const map = {};
    for (const svc of missingServices) {
      const cat = svc.infrastructure_category || "other";
      if (!map[cat]) map[cat] = [];
      map[cat].push(svc);
    }
    return map;
  }, [missingServices]);

  const categoryOrder = ["computing", "networking", "storage", "security", "data_management", "integration", "resilience", "productivity", "enterprise_software", "ai_ml", "management", "other"];
  const sortedCategories = categoryOrder.filter((c) => grouped[c]?.length > 0);

  function selectPlacement(serviceKey, placement) {
    setSelectedPlacements((prev) => ({ ...prev, [serviceKey]: placement }));
  }

  async function provision(service) {
    const placement = selectedPlacements[service.key];
    if (!placement || team.revision === null || team.locked_revision !== null) return;
    setProvisioning(service.key); setError("");
    try {
      // Buy the service
      const response = await apiClient.patch(`/instances/${instanceId}/platform`, {
        version: 1,
        expected_revision: team.revision,
        commands: [{ key: `platform_${service.key}_${placement}`, op: "buy_service", service: service.key, placement, units: 1 }],
      });
      // Assign to platform
      const newAssetKey = service.key;
      try {
        await apiClient.post(`/instances/${instanceId}/host-platforms/${platform.id}/members`, {
          asset_key: newAssetKey,
          member_kind: "service",
        });
      } catch { /* assignment failure is non-fatal */ }
      onProvisioned(response.data);
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(typeof detail === "string" ? detail : detail?.code || "Could not provision the service.");
    } finally { setProvisioning(null); }
  }

  if (sortedCategories.length === 0) {
    return (
      <div className="catalog-browser">
        <div className="catalog-browser__header">
          <h3>Add a Service to {platform.platform_code} &middot; {platform.name}</h3>
          <button type="button" className="components-secondary" onClick={onCancel}>Cancel</button>
        </div>
        <p className="components-muted">All available services have been provisioned.</p>
      </div>
    );
  }

  return (
    <div className="catalog-browser">
      <div className="catalog-browser__header">
        <h3>Add a Service to {platform.platform_code} &middot; {platform.name}</h3>
        <button type="button" className="components-secondary" onClick={onCancel}>Cancel</button>
      </div>
      {error && <p className="platform-error" role="alert">{error}</p>}
      {sortedCategories.map((cat) => {
        const isExpanded = expanded === cat;
        const catLabel = categories[cat] || cat.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
        const items = grouped[cat];
        return (
          <div key={cat} className="catalog-category">
            <button type="button" className="catalog-category__toggle" onClick={() => setExpanded(isExpanded ? null : cat)}>
              <span className="catalog-category__arrow">{isExpanded ? "\u25be" : "\u25b8"}</span>
              <span className="catalog-category__label">{catLabel}</span>
              <span className="catalog-category__count">({items.length} available)</span>
            </button>
            {isExpanded && items.map((svc) => {
              const selected = selectedPlacements[svc.key] || "";
              const detail = svc.placement_details?.find((d) => d.placement === selected);
              return (
                <div key={svc.key} className="catalog-service-card">
                  <div className="catalog-service-card__header">
                    <strong>{svc.label}</strong>
                    <ServiceModelBadge model={svc.service_model} />
                  </div>
                  {svc.vendor_examples && <p className="catalog-service-card__vendors">{svc.vendor_examples}</p>}
                  {svc.description && <p className="catalog-service-card__desc">{svc.description}</p>}
                  <div className="catalog-service-card__placement">
                    <span className="catalog-service-card__field-label">Placement:</span>
                    <div className="catalog-service-card__placement-options">
                      {svc.placements.map((p) => (
                        <label key={p} className={`catalog-placement-option${selected === p ? " catalog-placement-option--selected" : ""}`}>
                          <input type="radio" name={`placement-${svc.key}`} value={p} checked={selected === p} onChange={() => selectPlacement(svc.key, p)} />
                          {placementNames[p] || p}
                        </label>
                      ))}
                    </div>
                  </div>
                  {detail && (
                    <div className="catalog-service-card__costs">
                      <span>CAPEX: {fmt$(detail.capex)}</span>
                      <span>OPEX: {fmt$(detail.opex)}/round</span>
                      <span>Lead time: {detail.lead_time_rounds} round{detail.lead_time_rounds !== 1 ? "s" : ""}</span>
                      <span>Staff: {svc.staff_load} FTE &times; {detail.staff_load_modifier}</span>
                      <span>Reliability: {detail.availability_modifier < 1 ? "Standard" : detail.availability_modifier > 1 ? "Enhanced" : "Good"} ({detail.availability_modifier}&times;)</span>
                    </div>
                  )}
                  <div className="catalog-service-card__action">
                    <button type="button" className="components-primary" disabled={!selected || provisioning === svc.key || team.revision === null} onClick={() => provision(svc)}>
                      {provisioning === svc.key ? "Provisioning..." : "Provision"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}

/* ---------- Firmwide component browser ---------- */

function ComponentCatalogBrowser({ platform, team, instanceId, categories, firmwideComponents, onProvisioned, onCancel }) {
  const [selectedPlacements, setSelectedPlacements] = useState({});
  const [provisioning, setProvisioning] = useState(null);
  const [error, setError] = useState("");

  const activeComponentKeys = new Set((team?.assets || []).filter((a) => a.source_kind === "catalog" && a.status === "active").map((a) => a.source_key));
  const available = (firmwideComponents || []).filter((c) => !activeComponentKeys.has(c.key));

  function selectPlacement(key, placement) {
    setSelectedPlacements((prev) => ({ ...prev, [key]: placement }));
  }

  async function provision(item) {
    const placement = selectedPlacements[item.key];
    if (!placement || team.revision === null || team.locked_revision !== null) return;
    setProvisioning(item.key); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/platform`, {
        version: 1,
        expected_revision: team.revision,
        commands: [{ key: `buy_${item.key}_${placement}`, op: "buy", application: item.key, placement, config: "basic", units: 1 }],
      });
      try {
        await apiClient.post(`/instances/${instanceId}/host-platforms/${platform.id}/members`, {
          asset_key: item.key,
          member_kind: "component",
        });
      } catch { /* assignment failure is non-fatal */ }
      onProvisioned(response.data);
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(typeof detail === "string" ? detail : detail?.code || "Could not provision the component.");
    } finally { setProvisioning(null); }
  }

  return (
    <div className="catalog-browser">
      <div className="catalog-browser__header">
        <h3>Add a Component to {platform.platform_code} &middot; {platform.name}</h3>
        <button type="button" className="components-secondary" onClick={onCancel}>Cancel</button>
      </div>
      {error && <p className="platform-error" role="alert">{error}</p>}
      {available.length === 0 && <p className="components-muted">All firmwide components have been provisioned.</p>}
      {available.map((item) => {
        const selected = selectedPlacements[item.key] || "";
        const detail = item.placement_details?.find((d) => d.placement === selected);
        const catLabel = item.infrastructure_category ? (categories[item.infrastructure_category] || item.infrastructure_category) : "";
        return (
          <div key={item.key} className="catalog-service-card">
            <div className="catalog-service-card__header">
              <strong>{item.label}</strong>
              {catLabel && <span className="catalog-category-tag">{catLabel}</span>}
            </div>
            {item.vendor_examples && <p className="catalog-service-card__vendors">{item.vendor_examples}</p>}
            {item.description && <p className="catalog-service-card__desc">{item.description}</p>}
            <div className="catalog-service-card__placement">
              <span className="catalog-service-card__field-label">Placement:</span>
              <div className="catalog-service-card__placement-options">
                {item.placements.map((p) => (
                  <label key={p} className={`catalog-placement-option${selected === p ? " catalog-placement-option--selected" : ""}`}>
                    <input type="radio" name={`comp-placement-${item.key}`} value={p} checked={selected === p} onChange={() => selectPlacement(item.key, p)} />
                    {placementNames[p] || p}
                  </label>
                ))}
              </div>
            </div>
            {detail && (
              <div className="catalog-service-card__costs">
                <span>CAPEX: {fmt$(detail.capex)}</span>
                <span>OPEX: {fmt$(detail.opex)}/round</span>
                <span>Lead time: {detail.lead_time_rounds} round{detail.lead_time_rounds !== 1 ? "s" : ""}</span>
              </div>
            )}
            <div className="catalog-service-card__action">
              <button type="button" className="components-primary" disabled={!selected || provisioning === item.key || team.revision === null} onClick={() => provision(item)}>
                {provisioning === item.key ? "Provisioning..." : "Provision"}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ---------- Platform card ---------- */

function PlatformCard({ platform, team, instanceId, categories, firmwideComponents, onPlatformsUpdated, onPlatformDataUpdated }) {
  const [badgeStatus, badgeLabel] = statusBadgeMap[platform.status] || ["neutral", platform.status];
  const [showServiceCatalog, setShowServiceCatalog] = useState(false);
  const [showComponentCatalog, setShowComponentCatalog] = useState(false);
  const services = platform.members.filter((m) => m.member_kind === "service");
  const components = platform.members.filter((m) => m.member_kind === "component");
  const readOnly = !team || team.revision === null || team.locked_revision !== null;
  const isActive = platform.status === "active";
  const isPending = platform.status === "pending";

  const teamAssets = team?.assets || [];
  const availableServicesList = team?.available_services || [];

  function serviceRow(member) {
    const asset = teamAssets.find((a) => a.source_key === member.asset_key || a.id === member.asset_key);
    const svcDef = availableServicesList.find((s) => s.key === member.asset_key);
    if (!asset) return { key: member.id, name: member.asset_key, vendor: "", model: "", capacity: "", utilisation: "", status: "" };
    const [, statusLabel] = statusFor(asset.utilisation_pct);
    return {
      key: member.id,
      name: asset.label,
      vendor: svcDef?.vendor_examples || "",
      model: svcDef?.service_model || "",
      category: svcDef?.infrastructure_category || "",
      capacity: typeof asset.capacity_pct === "number" ? `${asset.capacity_pct}%` : "",
      utilisation: typeof asset.utilisation_pct === "number" ? `${Math.round(asset.utilisation_pct)}%` : "",
      status: statusLabel,
    };
  }

  function componentRow(member) {
    const asset = teamAssets.find((a) => a.source_key === member.asset_key || a.id === member.asset_key);
    if (!asset) return { key: member.id, name: member.asset_key, vendor: "", installed: "", placement: "", config: "" };
    const fwItem = (firmwideComponents || []).find((c) => c.key === member.asset_key);
    return {
      key: member.id,
      name: asset.label,
      vendor: fwItem?.vendor_examples || "",
      category: fwItem?.infrastructure_category || "",
      installed: `R${asset.installed_round}`,
      placement: placementNames[asset.placement] || asset.placement,
      config: asset.config || "",
    };
  }

  // Group services by category for display
  const serviceRows = services.map(serviceRow);
  const servicesByCategory = useMemo(() => {
    const map = {};
    for (const row of serviceRows) {
      const cat = row.category || "other";
      if (!map[cat]) map[cat] = [];
      map[cat].push(row);
    }
    return map;
  }, [serviceRows]);
  const categoryOrder = ["computing", "networking", "storage", "security", "data_management", "integration", "resilience", "productivity", "enterprise_software", "ai_ml", "management", "other"];
  const sortedServiceCategories = categoryOrder.filter((c) => servicesByCategory[c]?.length > 0);

  return (
    <section className="host-platform-card">
      <div className="host-platform-card__header">
        <div>
          <span className="host-platform-card__code">{platform.platform_code}</span>
          <strong>{platform.name}</strong>
          <span className={`host-platform-type-badge host-platform-type-badge--${platform.platform_type}`}>
            {typeLabels[platform.platform_type] || platform.platform_type}
            {platform.cloud_subtype ? ` \u00b7 ${subtypeLabels[platform.cloud_subtype] || platform.cloud_subtype}` : ""}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)" }}>
          {isPending && <span className="components-muted">Available next round</span>}
          <StatusBadge status={badgeStatus} label={badgeLabel} />
        </div>
      </div>
      {platform.notes && <p className="components-muted" style={{ margin: 0 }}>{platform.notes}</p>}

      {/* Services section */}
      {services.length > 0 && (
        <div className="host-platform-card__section">
          <h3>Services ({services.length}/5)</h3>
          {sortedServiceCategories.map((cat) => {
            const catLabel = categories[cat] || cat.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
            return (
              <div key={cat} className="platform-service-group">
                <span className="platform-service-group__label">{catLabel}</span>
                {servicesByCategory[cat].map((r) => (
                  <div key={r.key} className="platform-service-item">
                    <span className="platform-service-item__name">{r.name}</span>
                    <ServiceModelBadge model={r.model} />
                    {r.vendor && <span className="platform-service-item__vendor">{r.vendor.split(" / ")[0]}</span>}
                    <span className="platform-service-item__status">{r.capacity ? `${r.capacity} cap` : r.status || "Active"}</span>
                  </div>
                ))}
              </div>
            );
          })}
        </div>
      )}

      {/* Components section */}
      {components.length > 0 && (
        <div className="host-platform-card__section">
          <h3>Components ({components.length}/5)</h3>
          {components.map((m) => {
            const r = componentRow(m);
            const catLabel = r.category ? (categories[r.category] || r.category) : "";
            return (
              <div key={r.key} className="platform-service-group">
                {catLabel && <span className="platform-service-group__label">{catLabel}</span>}
                <div className="platform-service-item">
                  <span className="platform-service-item__name">{r.name}</span>
                  {r.vendor && <span className="platform-service-item__vendor">{r.vendor.split(" / ")[0]}</span>}
                  <span className="platform-service-item__status">{r.placement}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Action buttons */}
      {isActive && !readOnly && !showServiceCatalog && !showComponentCatalog && (
        <div className="host-platform-card__actions" style={{ display: "flex", gap: "var(--space-md)", justifyContent: "center" }}>
          {services.length < 5 && (
            <button type="button" className="components-secondary" onClick={() => setShowServiceCatalog(true)}>+ Add a Service</button>
          )}
          {components.length < 5 && (
            <button type="button" className="components-secondary" onClick={() => setShowComponentCatalog(true)}>+ Add a Component</button>
          )}
        </div>
      )}

      {/* Service catalog browser */}
      {showServiceCatalog && (
        <ServiceCatalogBrowser
          platform={platform}
          team={team}
          instanceId={instanceId}
          categories={categories}
          onProvisioned={(data) => { onPlatformDataUpdated(data); setShowServiceCatalog(false); }}
          onCancel={() => setShowServiceCatalog(false)}
        />
      )}

      {/* Component catalog browser */}
      {showComponentCatalog && (
        <ComponentCatalogBrowser
          platform={platform}
          team={team}
          instanceId={instanceId}
          categories={categories}
          firmwideComponents={firmwideComponents}
          onProvisioned={(data) => { onPlatformDataUpdated(data); setShowComponentCatalog(false); }}
          onCancel={() => setShowComponentCatalog(false)}
        />
      )}
    </section>
  );
}

/* ---------- Main page ---------- */

export default function InfrastructurePage({ platformData, controlsData, instanceId, hostPlatforms: initialHostPlatforms }) {
  const [view, setView] = useState(platformData);
  const [hostPlatforms, setHostPlatforms] = useState(initialHostPlatforms || []);
  const [showNewPlatformForm, setShowNewPlatformForm] = useState(false);
  useEffect(() => setView(platformData), [platformData]);
  useEffect(() => { if (initialHostPlatforms) setHostPlatforms(initialHostPlatforms); }, [initialHostPlatforms]);

  const team = view?.team;
  const controlsTeam = controlsData?.team;
  const displayTeam = team || controlsTeam;
  const categories = view?.infrastructure_categories || {};
  const firmwideComponents = team?.firmwide_components || [];

  if (!displayTeam) return <section className="controls-empty"><h2>Your team has not entered the runtime yet</h2><p>Infrastructure decisions will appear here after the team runtime is initialized.</p></section>;

  const readOnly = !team || team.revision === null || team.locked_revision !== null;

  async function refreshHostPlatforms() {
    try {
      const res = await apiClient.get(`/instances/${instanceId}/host-platforms`);
      setHostPlatforms(res.data.platforms);
    } catch { /* ignore */ }
  }

  function handlePlatformDataUpdated(data) {
    setView(data);
    refreshHostPlatforms();
  }

  return (
    <div className="controls-page">
      <ContextBanner description="Provision and manage your firm's shared IT infrastructure &mdash; the hardware, software, and services that support the entire enterprise." />

      {readOnly && team?.locked_revision !== null && <section className="review-banner"><strong>This round is locked.</strong><span>Decisions reopen when the round advances.</span></section>}

      {/* Top-level action */}
      <section className="components-toolbar">
        <div />
        <div>
          {!readOnly && !showNewPlatformForm && <button type="button" className="components-primary" onClick={() => setShowNewPlatformForm(true)}>+ New Host Platform</button>}
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
          categories={categories}
          firmwideComponents={firmwideComponents}
          onPlatformsUpdated={setHostPlatforms}
          onPlatformDataUpdated={handlePlatformDataUpdated}
        />
      ))}

      {/* Empty state */}
      {hostPlatforms.length === 0 && !showNewPlatformForm && (
        <section className="controls-empty" style={{ textAlign: "center" }}>
          <h2>No platforms yet</h2>
          <p>Create your first host platform to start building your firm's IT infrastructure.</p>
          {!readOnly && <button type="button" className="components-primary" style={{ marginTop: "var(--space-md)" }} onClick={() => setShowNewPlatformForm(true)}>+ New Host Platform</button>}
        </section>
      )}
    </div>
  );
}
