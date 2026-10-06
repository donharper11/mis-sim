/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { ContextBanner, RolloutSlider } from "../components/index.js";
import { GovernancePanel } from "./Controls.jsx";
import { PlatformDetailModal } from "./InfrastructurePage.jsx";

/* ---------- Main Rollout component ---------- */

export default function Rollout({ data, controlsData, instanceId, hostPlatforms, platformData }) {
  const [view, setView] = useState(data);
  const [controlsView, setControlsView] = useState(controlsData);
  useEffect(() => setControlsView(controlsData), [controlsData]);
  useEffect(() => setView(data), [data]);
  const team = view?.team;
  const [viewPlatformId, setViewPlatformId] = useState(null);

  // Build dynamic tabs from deployments, grouped by label
  const appTabs = useMemo(() => {
    if (!team?.deployments?.length) return [];
    const seen = new Map();
    for (const dep of team.deployments) {
      const tabKey = dep.id;
      if (!seen.has(tabKey)) {
        seen.set(tabKey, { key: tabKey, label: dep.label, deploymentId: dep.id });
      }
    }
    return Array.from(seen.values());
  }, [team]);

  const allTabs = useMemo(() => [...appTabs, { key: "ownership", label: "Ownership" }], [appTabs]);

  const [activeTab, setActiveTab] = useState("");

  // Default to first app tab when tabs become available
  useEffect(() => {
    if (appTabs.length > 0 && (!activeTab || !allTabs.find((t) => t.key === activeTab))) {
      setActiveTab(appTabs[0].key);
    }
  }, [appTabs, allTabs, activeTab]);

  function saveRollout(next) {
    setView(next);
    setControlsView((prior) => prior ? { ...prior, team: { ...prior.team, revision: next.team.revision, locked_revision: next.team.locked_revision, selected_commands: next.team.selected_commands } } : prior);
  }

  function saveOwnership(next) {
    setControlsView(next);
    setView((prior) => ({ ...prior, team: { ...prior.team, revision: next.team.revision, locked_revision: next.team.locked_revision, selected_commands: next.team.selected_commands } }));
  }

  if (!team) return <section className="components-empty"><h2>Your team has not entered the runtime yet</h2><p>Rollout decisions will appear here after the team runtime is initialized.</p></section>;

  const activeDeployment = activeTab !== "ownership" ? team.deployments?.find((d) => d.id === activeTab) : null;
  const viewPlatform = viewPlatformId && hostPlatforms ? hostPlatforms.find((p) => p.id === viewPlatformId) : null;

  return (
    <div className="rollout-page">
      <ContextBanner description="Deploy, train, and assign ownership for each capability." />

      {/* Dynamic tabs */}
      <div className="rollout-app-tabs" role="tablist">
        {allTabs.map((tab) => (
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === tab.key}
            className={`rollout-app-tab${activeTab === tab.key ? " rollout-app-tab--active" : ""}`}
            onClick={() => setActiveTab(tab.key)}
            key={tab.key}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Per-application inline detail */}
      {activeDeployment && (
        <RolloutSlider
          key={activeDeployment.id}
          deployment={activeDeployment}
          team={team}
          instanceId={instanceId}
          onSaved={saveRollout}
          onViewPlatform={(platformId) => setViewPlatformId(platformId)}
        />
      )}

      {/* Ownership tab */}
      {activeTab === "ownership" && controlsView && <GovernancePanel view={controlsView} instanceId={instanceId} onSaved={saveOwnership} />}
      {activeTab === "ownership" && !controlsView && <section className="controls-empty"><p>Ownership data is not available.</p></section>}

      {/* Platform detail modal (read-only, from rollout link) */}
      {viewPlatform && (
        <PlatformDetailModal
          platform={viewPlatform}
          team={platformData?.team}
          instanceId={instanceId}
          categories={platformData?.infrastructure_categories || {}}
          firmwideComponents={[
            ...(platformData?.team?.firmwide_components || []),
            ...(team.deployments || []).map((d) => ({ key: d.source_key, placement_details: [{ placement: d.placement, capex: d.capex, opex: d.opex }] })),
          ]}
          readOnly
          onClose={() => setViewPlatformId(null)}
        />
      )}
    </div>
  );
}
