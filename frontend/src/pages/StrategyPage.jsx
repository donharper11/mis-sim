/* eslint-disable react/prop-types */
import { ContextBanner } from "../components/index.js";
import { StrategyPanel } from "./Controls.jsx";

export default function StrategyPage({ data, instanceId }) {
  const team = data?.team;
  if (!team) return <section className="controls-empty"><h2>Your team has not entered the runtime yet</h2><p>Strategy decisions will appear here after the team runtime is initialized.</p></section>;
  return (
    <div className="controls-page">
      <ContextBanner step={1} eyebrow="Choose your competitive strategy" description="Your declared strategy guides every capability evaluation and event response." teamName={team.name} round={team.current_round} strategy={team.strategy} />
      <StrategyPanel view={data} instanceId={instanceId} />
    </div>
  );
}
