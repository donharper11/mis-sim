/* eslint-disable react/prop-types */
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { apiClient } from "../api/client.js";
import { RolloutSlider, StatusBadge } from "../components/index.js";

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

export default function ApplicationDetailPage({ data, rolloutData, instanceId }) {
  const { id } = useParams();
  const navigate = useNavigate();
  const [componentsView, setComponentsView] = useState(data);
  const [rolloutView, setRolloutView] = useState(rolloutData);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const team = componentsView?.team;
  const asset = team?.assets?.find((a) => a.id === id);
  const deployment = rolloutView?.team?.deployments?.find((d) => d.id === id);

  if (!team) return <section className="controls-empty"><h2>Your team has not entered the runtime yet</h2><p>Application details will appear here after the team runtime is initialized.</p></section>;
  if (!asset) return <section className="controls-empty"><h2>Application not found</h2><p>The requested application could not be found in the current plan.</p><button type="button" className="components-secondary" style={{ marginTop: "var(--space-md)" }} onClick={() => navigate("/applications")}>Back to applications</button></section>;

  const [status, statusLabel] = assetStatus(asset);

  async function retire() {
    if (team.revision === null || team.locked_revision !== null) return;
    setSaving(true); setError("");
    try {
      const response = await apiClient.patch(`/instances/${instanceId}/components`, { version: 1, expected_revision: team.revision, replace_categories: { lifecycle: [{ key: `retire_${asset.id}`, op: "retire_asset", asset: asset.id }] } });
      setComponentsView(response.data);
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
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-md)" }}>
            <StatusBadge status={status} label={statusLabel} />
            <button type="button" className="components-danger" disabled={saving || team.locked_revision !== null || team.revision === null || asset.status === "retired"} onClick={retire}>{saving ? "Saving…" : "Retire component"}</button>
          </div>
        </div>
        {error && <p className="components-error" role="alert">{error}</p>}
      </section>

      {deployment && rolloutView?.team ? (
        <RolloutSlider
          key={deployment.id}
          deployment={deployment}
          team={rolloutView.team}
          instanceId={instanceId}
          onSaved={(next) => setRolloutView(next)}
        />
      ) : (
        <section className="controls-empty">
          <h2>No deployment found</h2>
          <p>This application does not have rollout data yet. It may be pending installation or not yet deployed.</p>
        </section>
      )}
    </div>
  );
}
