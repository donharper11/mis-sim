/* eslint-disable react/prop-types */
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiClient } from "../api/client.js";
import { StatusBadge } from "../components/index.js";

const placementNames = { cloud: "Cloud", on_prem: "On-Premises", saas: "SaaS" };
const detailTabs = ["Deployment", "Data", "Connections", "Lifecycle"];

function formatOrgUnit(value) {
  if (!value) return "Firmwide";
  return value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function assetStatus(asset) {
  if (asset.status === "retired") return ["not-started", "Retired"];
  if (typeof asset.adoption === "number" && asset.adoption < 0.5) return ["needs-attention", "Needs attention"];
  if (typeof asset.adoption === "number" && asset.adoption < 0.9) return ["partly-done", "Partly done"];
  return ["complete", "Complete"];
}

export default function ApplicationDetailPage({ data, instanceId }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [view, setView] = useState(data);
  const [tab, setTab] = useState("Deployment");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const team = view?.team;
  const asset = team?.assets?.find((a) => a.id === id);

  if (!team) return <section className="controls-empty"><h2>Your team has not entered the runtime yet</h2><p>Application details will appear here after the team runtime is initialized.</p></section>;
  if (!asset) return <section className="controls-empty"><h2>Application not found</h2><p>The requested application could not be found in the current plan.</p><button type="button" className="components-secondary" style={{ marginTop: "var(--space-md)" }} onClick={() => navigate("/applications")}>Back to applications</button></section>;

  const [status, statusLabel] = assetStatus(asset);

  async function retire() {
    if (team.revision === null || team.locked_revision !== null) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/components`, { version: 1, expected_revision: team.revision, replace_categories: { lifecycle: [{ key: `retire_${asset.id}`, op: "retire_asset", asset: asset.id }] } });
      setView(response.data);
    } catch (requestError) { setError(typeof requestError.response?.data?.detail === "string" ? requestError.response.data.detail : "The lifecycle decision could not be saved."); }
    finally { setSaving(false); }
  }

  return (
    <div className="controls-page">
      <button type="button" className="components-secondary" onClick={() => navigate("/applications")}>Back to applications</button>
      <section className="components-detail" aria-labelledby="app-detail-heading">
        <div className="components-panel-heading">
          <div>
            <h1 id="app-detail-heading" style={{ margin: 0, fontSize: "18px" }}>{asset.label}</h1>
            <p className="components-muted">{formatOrgUnit(asset.org_unit)} · {asset.people || "—"} people · {asset.serves?.join(", ") || "No capability recorded"}</p>
          </div>
          <StatusBadge status={status} label={statusLabel} />
        </div>
        <div className="components-tabs" role="tablist">{detailTabs.map((item) => <button type="button" role="tab" aria-selected={tab === item} className={tab === item ? "components-tab--active" : ""} onClick={() => setTab(item)} key={item}>{item}</button>)}</div>
        {tab === "Deployment" && <div className="components-detail-grid"><article><h3>Placement</h3><p>{placementNames[asset.placement] || asset.placement} · {asset.config || "default configuration"}</p></article><article><h3>Rollout</h3><p>Trained {asset.trained_count ?? "—"} · adoption {typeof asset.adoption === "number" ? `${Math.round(asset.adoption * 100)}%` : "—"} · process {asset.process || "—"}</p></article><article><h3>Lifecycle</h3><p>Installed round {asset.installed_round} · {asset.units} unit{asset.units === 1 ? "" : "s"}</p></article></div>}
        {tab === "Data" && <div className="components-detail-copy"><h3>Data</h3><p>The runtime records this component's capabilities and people affected through the registered casepack.</p></div>}
        {tab === "Connections" && <div className="components-detail-copy"><h3>Connections</h3><p>Connection detail will appear when integration records are present for this asset.</p></div>}
        {tab === "Lifecycle" && <div className="components-detail-copy"><h3>Lifecycle</h3><p>Installed round {asset.installed_round}. Retiring removes this asset from the active estate at the round boundary.</p><button type="button" className="components-danger" disabled={saving || team.locked_revision !== null || team.revision === null || asset.status === "retired"} onClick={retire}>{saving ? "Saving…" : "Retire component"}</button>{error && <p className="components-error" role="alert">{error}</p>}</div>}
      </section>
    </div>
  );
}
