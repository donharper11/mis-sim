/* eslint-disable react/prop-types */
import { ContextBanner } from "../components/index.js";
import Components from "./Components.jsx";

export default function ApplicationsPage({ data, instanceId }) {
  const team = data?.team;
  if (!team) return <section className="controls-empty"><h2>Your team has not entered the runtime yet</h2><p>Application decisions will appear here after the team runtime is initialized.</p></section>;
  return (
    <div className="components-page">
      <ContextBanner step={3} eyebrow="Choose applications for each business unit" description="Select, configure, and deploy the applications each unit needs." teamName={team.name} round={team.current_round} strategy={team.strategy} />
      <Components data={data} instanceId={instanceId} />
    </div>
  );
}
