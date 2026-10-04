/* eslint-disable react/prop-types */
import { ContextBanner } from "../components/index.js";
import { StrategyPanel } from "./Controls.jsx";

export default function StrategyPage({ data, instanceId }) {
  const team = data?.team;
  if (!team) return <section className="controls-empty"><h2>Your team has not entered the runtime yet</h2><p>Strategy decisions will appear here after the team runtime is initialized.</p></section>;
  return (
    <div className="controls-page">
      <ContextBanner description="Your declared strategy guides every capability evaluation and event response." />
      <StrategyPanel view={data} instanceId={instanceId} />
    </div>
  );
}
