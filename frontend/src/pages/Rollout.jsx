/* eslint-disable react/prop-types */
import { useEffect, useMemo, useState } from "react";
import { ContextBanner, RolloutSlider } from "../components/index.js";
import { GovernancePanel } from "./Controls.jsx";

/* ---------- Main Rollout component ---------- */

export default function Rollout({ data, controlsData, instanceId }) {
  const [view, setView] = useState(data);
  useEffect(() => setView(data), [data]);
  const team = view?.team;

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

  if (!team) return <section className="components-empty"><h2>Your team has not entered the runtime yet</h2><p>Rollout decisions will appear here after the team runtime is initialized.</p></section>;

  const activeDeployment = activeTab !== "ownership" ? team.deployments?.find((d) => d.id === activeTab) : null;

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
          onSaved={(next) => setView(next)}
        />
      )}

      {/* Ownership tab */}
      {activeTab === "ownership" && controlsData && <GovernancePanel view={controlsData} instanceId={instanceId} />}
      {activeTab === "ownership" && !controlsData && <section className="controls-empty"><p>Ownership data is not available.</p></section>}
    </div>
  );
}
