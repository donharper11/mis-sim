/* eslint-disable react/prop-types */
import { useState } from "react";
import { ContextBanner, PageTabs } from "../components/index.js";
import Platform from "./Platform.jsx";
import { PeoplePanel, SecurityPanel } from "./Controls.jsx";

const tabs = [
  { key: "platform", label: "Host Platform" },
  { key: "people", label: "People & Staffing" },
  { key: "security", label: "Data Policies" },
];

export default function InfrastructurePage({ platformData, controlsData, instanceId }) {
  const [activeTab, setActiveTab] = useState("platform");
  const team = platformData?.team || controlsData?.team;
  if (!team) return <section className="controls-empty"><h2>Your team has not entered the runtime yet</h2><p>Infrastructure decisions will appear here after the team runtime is initialized.</p></section>;
  return (
    <div className="controls-page">
      <ContextBanner step={2} eyebrow="Build the firm's technology foundation" description="Platform services, staffing, and data governance for the entire firm." teamName={team.name} round={team.current_round} strategy={team.strategy} />
      <PageTabs tabs={tabs} activeKey={activeTab} onChange={setActiveTab} />
      {activeTab === "platform" && <Platform data={platformData} instanceId={instanceId} />}
      {activeTab === "people" && <PeoplePanel view={controlsData} instanceId={instanceId} />}
      {activeTab === "security" && <SecurityPanel view={controlsData} instanceId={instanceId} />}
    </div>
  );
}
