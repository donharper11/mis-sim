/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { apiClient } from "../api/client.js";
import { ContextBanner, DetailTable, PageTabs, StatusBadge } from "../components/index.js";

import { PeoplePanel, SecurityPanel } from "./Controls.jsx";

const placementNames = { cloud: "Cloud", on_prem: "On-Premises", saas: "SaaS" };
const typeLabels = { on_prem: "On-Premises", cloud: "Cloud" };
const subtypeLabels = { iaas: "IaaS", paas: "PaaS", saas: "SaaS", aiaas: "AIaaS" };
const statusBadgeMap = { active: ["complete", "Active"], pending: ["info", "Pending"], retired: ["neutral", "Retired"] };
const modelBadgeColors = { iaas: "var(--status-info-bg)", paas: "var(--status-ok-bg)", saas: "var(--p-purple-100, #ede9fe)", aiaas: "var(--p-amber-100, #fef3c7)" };
const modelBadgeTextColors = { iaas: "var(--status-info-text)", paas: "var(--status-ok-text)", saas: "var(--p-purple-700, #6d28d9)", aiaas: "var(--p-amber-700, #b45309)" };
const categoryOrder = ["computing", "networking", "storage", "security", "data_management", "integration", "resilience", "productivity", "enterprise_software", "ai_ml", "management", "other"];

function fmt$(n) { return n >= 1000 ? `$${(n / 1000).toFixed(n % 1000 === 0 ? 0 : 1)}K` : `$${n}`; }

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

function ServiceCatalogBrowser({ platform, team, instanceId, categories, onProvisioned, onCancel, onBusyChange }) {
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

  const sortedCategories = categoryOrder.filter((c) => grouped[c]?.length > 0);

  function selectPlacement(serviceKey, placement) {
    setSelectedPlacements((prev) => ({ ...prev, [serviceKey]: placement }));
  }

  async function provision(service) {
    const placement = selectedPlacements[service.key];
    if (!placement || team.revision === null || team.locked_revision !== null) return;
    setProvisioning(service.key); onBusyChange(true); setError("");
    try {
      const current = (await apiClient.get(`/instances/${instanceId}/controls`)).data;
      const commandKey = `platform_${service.key}_${placement}`;
      const response = await apiClient.patch(`/instances/${instanceId}/platform`, {
        version: 1,
        expected_revision: current.team.revision,
        commands: [...current.team.selected_commands.filter((c) => ["buy_service", "replace_service"].includes(c.op) && c.key !== commandKey), { key: commandKey, op: "buy_service", service: service.key, placement, units: 1 }],
      });
      let warning = "";
      // Assign to platform
      const newAssetKey = service.key;
      try {
        await apiClient.post(`/instances/${instanceId}/host-platforms/${platform.id}/members`, {
          asset_key: newAssetKey,
          member_kind: "service",
        });
      } catch { warning = "The purchase was saved, but it could not be assigned to this host platform. Reload to check the purchase before trying again."; }
      await onProvisioned(response.data, warning);
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(typeof detail === "string" ? detail : detail?.code || "Could not provision the service.");
    } finally { setProvisioning(null); onBusyChange(false); }
  }

  if (sortedCategories.length === 0) {
    return (
      <div className="catalog-browser">
        <div className="catalog-browser__header">
          <h3>Add a Service to {platform.platform_code} &middot; {platform.name}</h3>
          <button type="button" className="components-secondary" disabled={!!provisioning} onClick={onCancel}>Cancel</button>
        </div>
        <p className="components-muted">All available services have been provisioned.</p>
      </div>
    );
  }

  return (
    <div className="catalog-browser">
      <div className="catalog-browser__header">
        <h3>Add a Service to {platform.platform_code} &middot; {platform.name}</h3>
        <button type="button" className="components-secondary" disabled={!!provisioning} onClick={onCancel}>Cancel</button>
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
                    <button type="button" className="components-primary" disabled={!selected || !!provisioning || team.revision === null} onClick={() => provision(svc)}>
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

function ComponentCatalogBrowser({ platform, team, instanceId, categories, firmwideComponents, onProvisioned, onCancel, onBusyChange }) {
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
    setProvisioning(item.key); onBusyChange(true); setError("");
    try {
      const [controlsResponse, componentsResponse] = await Promise.all([
        apiClient.get(`/instances/${instanceId}/controls`),
        apiClient.get(`/instances/${instanceId}/components`),
      ]);
      const current = controlsResponse.data;
      const config = componentsResponse.data.team?.choices.find((choice) => choice.key === item.key)?.configs[0]?.key;
      if (!config) {
        setError("No configuration is available for this component. Reload the catalog before trying again.");
        return;
      }
      const commandKey = `buy_${item.key}_${placement}`;
      await apiClient.patch(`/instances/${instanceId}/controls/security`, {
        version: 1,
        expected_revision: current.team.revision,
        commands: [...current.team.selected_commands.filter((c) => ["buy_application", "replace_application"].includes(c.op) && c.key !== commandKey), { key: commandKey, op: "buy_application", catalog: item.key, placement, config, primary_for: null, tco_categories: [] }],
      });
      let warning = "";
      try {
        await apiClient.post(`/instances/${instanceId}/host-platforms/${platform.id}/members`, {
          asset_key: item.key,
          member_kind: "component",
        });
      } catch { warning = "The purchase was saved, but it could not be assigned to this host platform. Reload to check the purchase before trying again."; }
      const response = await apiClient.get(`/instances/${instanceId}/platform`);
      await onProvisioned(response.data, warning);
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(typeof detail === "string" ? detail : detail?.code || "Could not provision the component.");
    } finally { setProvisioning(null); onBusyChange(false); }
  }

  return (
    <div className="catalog-browser">
      <div className="catalog-browser__header">
        <h3>Add a Component to {platform.platform_code} &middot; {platform.name}</h3>
        <button type="button" className="components-secondary" disabled={!!provisioning} onClick={onCancel}>Cancel</button>
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
              <button type="button" className="components-primary" disabled={!selected || !!provisioning || team.revision === null} onClick={() => provision(item)}>
                {provisioning === item.key ? "Provisioning..." : "Provision"}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* ---------- Platform Detail Modal ---------- */

export function PlatformDetailModal({ platform, team, instanceId, categories, firmwideComponents, readOnly, onClose, onPlatformDataUpdated }) {
  const [showServiceCatalog, setShowServiceCatalog] = useState(false);
  const [provisioning, setProvisioning] = useState(false);
  const [showComponentCatalog, setShowComponentCatalog] = useState(false);
  const [badgeStatus, badgeLabel] = statusBadgeMap[platform.status] || ["neutral", platform.status];
  const isActive = platform.status === "active";
  const isPending = platform.status === "pending";

  const services = platform.members.filter((m) => m.member_kind === "service");
  const components = platform.members.filter((m) => m.member_kind === "component");
  const teamAssets = team?.assets || [];
  const availableServicesList = team?.available_services || [];

  function enrichService(member) {
    const asset = teamAssets.find((a) => a.source_key === member.asset_key || a.id === member.asset_key);
    const svcDef = availableServicesList.find((s) => s.key === (asset?.source_key || member.asset_key));
    const placementDetail = svcDef?.placement_details?.find((d) => d.placement === asset?.placement);
    return {
      key: member.id,
      name: asset?.label || member.asset_key,
      vendor: svcDef?.vendor_examples || "",
      model: svcDef?.service_model || "",
      category: svcDef?.infrastructure_category || "other",
      placement: asset?.placement ? (placementNames[asset.placement] || asset.placement) : "",
      capex: placementDetail?.capex || 0,
      opex: placementDetail?.opex || 0,
      staffLoad: (svcDef?.staff_load || 0) * (placementDetail?.staff_load_modifier || 1),
      leadTime: placementDetail?.lead_time_rounds || 0,
    };
  }

  function enrichComponent(member) {
    const asset = teamAssets.find((a) => a.source_key === member.asset_key || a.id === member.asset_key);
    const fwItem = (firmwideComponents || []).find((c) => c.key === (asset?.source_key || member.asset_key));
    const placementDetail = fwItem?.placement_details?.find((d) => d.placement === asset?.placement);
    return {
      key: member.id,
      name: asset?.label || member.asset_key,
      vendor: fwItem?.vendor_examples || "",
      category: fwItem?.infrastructure_category || "other",
      placement: asset?.placement ? (placementNames[asset.placement] || asset.placement) : "",
      capex: placementDetail?.capex || 0,
      opex: placementDetail?.opex || 0,
      staffLoad: 0,
      leadTime: placementDetail?.lead_time_rounds || 0,
    };
  }

  const enrichedServices = services.map(enrichService);
  const enrichedComponents = components.map(enrichComponent);

  // Group services by category
  const servicesByCategory = useMemo(() => {
    const map = {};
    for (const s of enrichedServices) {
      const cat = s.category || "other";
      if (!map[cat]) map[cat] = [];
      map[cat].push(s);
    }
    return map;
  }, [enrichedServices]);
  const sortedServiceCategories = categoryOrder.filter((c) => servicesByCategory[c]?.length > 0);

  // Group components by category
  const componentsByCategory = useMemo(() => {
    const map = {};
    for (const c of enrichedComponents) {
      const cat = c.category || "other";
      if (!map[cat]) map[cat] = [];
      map[cat].push(c);
    }
    return map;
  }, [enrichedComponents]);
  const sortedComponentCategories = categoryOrder.filter((c) => componentsByCategory[c]?.length > 0);

  // Cost summary
  const allItems = [...enrichedServices, ...enrichedComponents];
  const totalCapex = allItems.reduce((s, i) => s + i.capex, 0);
  const totalOpex = allItems.reduce((s, i) => s + i.opex, 0);
  const totalStaff = allItems.reduce((s, i) => s + i.staffLoad, 0);
  const maxLeadTime = allItems.reduce((m, i) => Math.max(m, i.leadTime), 0);

  const canEdit = isPending && !readOnly;

  return (
    <div className="modal-overlay" onClick={(e) => { if (e.target === e.currentTarget && !provisioning) onClose(); }}>
      <div className="platform-detail-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="platform-detail-modal__header">
          <div className="platform-detail-modal__header-left">
            <h2>
              <span className="host-platform-card__code">{platform.platform_code}</span>
              {platform.name}
            </h2>
            <span className={`host-platform-type-badge host-platform-type-badge--${platform.platform_type}`}>
              {typeLabels[platform.platform_type] || platform.platform_type}
              {platform.cloud_subtype ? ` \u00b7 ${subtypeLabels[platform.cloud_subtype] || platform.cloud_subtype}` : ""}
            </span>
            <StatusBadge status={badgeStatus} label={badgeLabel} />
          </div>
          <button type="button" className="modal-close" disabled={provisioning} onClick={onClose}>&times;</button>
        </div>

        {/* Body */}
        <div className="platform-detail-modal__body">
          {/* Locked banner */}
          {isActive && (
            <div className="platform-detail-modal__locked-banner">
              This platform was approved in Round {platform.activated_round || "?"} and is now operational. No further changes can be made.
            </div>
          )}

          {/* Meta info */}
          <div className="platform-detail-modal__meta">
            {platform.notes && <p>{platform.notes}</p>}
            <p>Created: Round {platform.created_round || 1}</p>
          </div>

          {/* Services section */}
          <div className="platform-detail-modal__section">
            <h3 className="platform-detail-modal__section-title">Services ({services.length}/5)</h3>
            {sortedServiceCategories.map((cat) => {
              const catLabel = categories[cat] || cat.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
              return (
                <div key={cat}>
                  <div className="platform-detail-modal__group-label">{catLabel}</div>
                  {servicesByCategory[cat].map((s) => (
                    <div key={s.key} className="platform-detail-modal__item">
                      <div className="platform-detail-modal__item-header">
                        <strong>{s.name}</strong>
                        <ServiceModelBadge model={s.model} />
                        {s.vendor && <span className="components-muted" style={{ fontStyle: "italic" }}>{s.vendor}</span>}
                      </div>
                      <div className="platform-detail-modal__item-costs">
                        <span>{s.placement}</span>
                        <span>CAPEX {fmt$(s.capex)}</span>
                        <span>OPEX {fmt$(s.opex)}/rd</span>
                        {s.staffLoad > 0 && <span>{s.staffLoad.toFixed(1)} FTE</span>}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
            {services.length === 0 && !showServiceCatalog && <p className="components-muted">No services provisioned yet.</p>}

            {/* Inline service catalog */}
            {showServiceCatalog && (
              <ServiceCatalogBrowser
                platform={platform}
                team={team}
                instanceId={instanceId}
                categories={categories}
                onBusyChange={setProvisioning}
                onProvisioned={async (data, warning) => { await onPlatformDataUpdated?.(data, warning); setShowServiceCatalog(false); }}
                onCancel={() => setShowServiceCatalog(false)}
              />
            )}
            {canEdit && !showServiceCatalog && !showComponentCatalog && services.length < 5 && (
              <button type="button" className="components-secondary" onClick={() => setShowServiceCatalog(true)}>+ Add a Service</button>
            )}
          </div>

          {/* Components section */}
          <div className="platform-detail-modal__section">
            <h3 className="platform-detail-modal__section-title">Components ({components.length}/5)</h3>
            {sortedComponentCategories.map((cat) => {
              const catLabel = categories[cat] || cat.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
              return (
                <div key={cat}>
                  <div className="platform-detail-modal__group-label">{catLabel}</div>
                  {componentsByCategory[cat].map((c) => (
                    <div key={c.key} className="platform-detail-modal__item">
                      <div className="platform-detail-modal__item-header">
                        <strong>{c.name}</strong>
                        {c.vendor && <span className="components-muted" style={{ fontStyle: "italic" }}>{c.vendor}</span>}
                      </div>
                      <div className="platform-detail-modal__item-costs">
                        <span>{c.placement}</span>
                        <span>CAPEX {fmt$(c.capex)}</span>
                        <span>OPEX {fmt$(c.opex)}/rd</span>
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
            {components.length === 0 && !showComponentCatalog && <p className="components-muted">No components provisioned yet.</p>}

            {/* Inline component catalog */}
            {showComponentCatalog && (
              <ComponentCatalogBrowser
                platform={platform}
                team={team}
                instanceId={instanceId}
                categories={categories}
                firmwideComponents={firmwideComponents}
                onBusyChange={setProvisioning}
                onProvisioned={async (data, warning) => { await onPlatformDataUpdated?.(data, warning); setShowComponentCatalog(false); }}
                onCancel={() => setShowComponentCatalog(false)}
              />
            )}
            {canEdit && !showComponentCatalog && !showServiceCatalog && components.length < 5 && (
              <button type="button" className="components-secondary" onClick={() => setShowComponentCatalog(true)}>+ Add a Component</button>
            )}
          </div>

          {/* Cost summary */}
          {allItems.length > 0 && (
            <div className="platform-detail-modal__cost-summary">
              <div><span>Total CAPEX</span><strong>{fmt$(totalCapex)}</strong></div>
              <div><span>Total OPEX</span><strong>{fmt$(totalOpex)}/round</strong></div>
              <div><span>Staff Load</span><strong>{totalStaff.toFixed(1)} FTE</strong></div>
              <div><span>Lead Time</span><strong>{maxLeadTime} round{maxLeadTime !== 1 ? "s" : ""}</strong></div>
            </div>
          )}

          {/* Actions */}
          <div className="platform-detail-modal__actions">
            <button type="button" className="components-secondary" disabled={provisioning} onClick={onClose}>Close</button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- Main page ---------- */

export default function InfrastructurePage({ platformData, controlsData, instanceId, hostPlatforms: initialHostPlatforms }) {
  const [view, setView] = useState(platformData);
  const [controlsView, setControlsView] = useState(controlsData);
  const [activeTab, setActiveTab] = useState("hosting");
  const [controlsRefreshing, setControlsRefreshing] = useState(false);
  const [refreshError, setRefreshError] = useState("");
  const [purchaseWarning, setPurchaseWarning] = useState("");
  useEffect(() => setControlsView(controlsData), [controlsData]);
  const [hostPlatforms, setHostPlatforms] = useState(initialHostPlatforms || []);
  const [showNewPlatformForm, setShowNewPlatformForm] = useState(false);
  const [selectedPlatformId, setSelectedPlatformId] = useState(null);
  useEffect(() => setView(platformData), [platformData]);
  useEffect(() => { if (initialHostPlatforms) setHostPlatforms(initialHostPlatforms); }, [initialHostPlatforms]);

  const team = view?.team;
  const controlsTeam = controlsView?.team;
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

  async function handlePlatformDataUpdated(data, warning = "") {
    setView(data);
    setPurchaseWarning(warning);
    setControlsRefreshing(true);
    setRefreshError("");
    // A revision and its commands must come from the same snapshot.
    setControlsView(null);
    try {
      const response = await apiClient.get(`/instances/${instanceId}/controls`);
      setControlsView(response.data);
    } catch {
      setRefreshError("Your purchase was saved, but the decision controls could not be refreshed. Reload the page before making another decision.");
    } finally {
      setControlsRefreshing(false);
    }
    await refreshHostPlatforms();
  }

  function handleControlsSaved(next) {
    setControlsView(next);
    setView((prior) => prior ? { ...prior, team: { ...prior.team, revision: next.team.revision, locked_revision: next.team.locked_revision } } : prior);
  }

  // Table columns
  const columns = [
    { key: "platform_code", title: "Code" },
    { key: "name", title: "Name" },
    { key: "type", title: "Type" },
    { key: "services", title: "Services" },
    { key: "components", title: "Components" },
    { key: "status", title: "Status" },
  ];

  const rows = hostPlatforms.map((p) => {
    const svcCount = p.members.filter((m) => m.member_kind === "service").length;
    const cmpCount = p.members.filter((m) => m.member_kind === "component").length;
    const [bStatus, bLabel] = statusBadgeMap[p.status] || ["neutral", p.status];
    const typeParts = [typeLabels[p.platform_type] || p.platform_type];
    if (p.cloud_subtype) typeParts.push(subtypeLabels[p.cloud_subtype] || p.cloud_subtype);
    return {
      key: p.id,
      platform_code: p.platform_code,
      name: p.name,
      type: typeParts.join(" \u00b7 "),
      services: svcCount,
      components: cmpCount,
      status: <StatusBadge status={bStatus} label={bLabel} />,
    };
  });

  const selectedPlatform = selectedPlatformId ? hostPlatforms.find((p) => p.id === selectedPlatformId) : null;
  const modalReadOnly = selectedPlatform ? (selectedPlatform.status === "active" || readOnly) : true;

  return (
    <div className="controls-page">
      <ContextBanner description="Provision and manage your firm's shared IT infrastructure &mdash; the hardware, software, and services that support the entire enterprise." />

      {purchaseWarning && <p className="components-error" role="alert">{purchaseWarning}</p>}
      {refreshError && <p className="components-error" role="alert">{refreshError} <button type="button" onClick={() => window.location.reload()}>Reload page</button></p>}
      {controlsRefreshing && <p role="status">Refreshing saved decisions…</p>}
      <PageTabs tabs={[{ key: "hosting", label: "Host platforms" }, { key: "security", label: "Security & data policies" }, { key: "people", label: "People" }]} activeKey={activeTab} onChange={setActiveTab} />
      {activeTab === "security" && controlsView && <SecurityPanel view={controlsView} instanceId={instanceId} onSaved={handleControlsSaved} />}
      {activeTab === "people" && controlsView && <PeoplePanel view={controlsView} instanceId={instanceId} onSaved={handleControlsSaved} />}
      {activeTab === "hosting" && <>
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

      {/* Platform table */}
      {hostPlatforms.length > 0 && (
        <section className="components-table-panel">
          <DetailTable columns={columns} rows={rows} onRowClick={(row) => setSelectedPlatformId(row.key)} />
        </section>
      )}

      {/* Empty state */}
      {hostPlatforms.length === 0 && !showNewPlatformForm && (
        <section className="controls-empty" style={{ textAlign: "center" }}>
          <h2>No platforms yet</h2>
          <p>Create your first host platform to start building your firm&apos;s IT infrastructure.</p>
          {!readOnly && <button type="button" className="components-primary" style={{ marginTop: "var(--space-md)" }} onClick={() => setShowNewPlatformForm(true)}>+ New Host Platform</button>}
        </section>
      )}

      {/* Platform detail modal */}
      {selectedPlatform && (
        <PlatformDetailModal
          platform={selectedPlatform}
          team={team}
          instanceId={instanceId}
          categories={categories}
          firmwideComponents={firmwideComponents}
          readOnly={modalReadOnly}
          onClose={() => setSelectedPlatformId(null)}
          onPlatformDataUpdated={handlePlatformDataUpdated}
        />
      )}
      </>}
    </div>
  );
}
