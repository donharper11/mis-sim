/* eslint-disable react/prop-types */
import Components from "./Components.jsx";

export default function ApplicationsPage({ data, instanceId, hostPlatforms }) {
  const team = data?.team;
  if (!team) return <section className="controls-empty"><h2>Your team has not entered the runtime yet</h2><p>Application decisions will appear here after the team runtime is initialized.</p></section>;
  return <Components data={data} instanceId={instanceId} hostPlatforms={hostPlatforms} />;
}
