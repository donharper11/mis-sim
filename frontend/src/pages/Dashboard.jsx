/* eslint-disable react/prop-types */
import { StatusBadge } from "../components/index.js";

const scorecard = [
  ["financial", "Financial"],
  ["customer", "Customer"],
  ["internal_process", "Internal Process"],
  ["learning_growth", "Learning & Growth"],
];

function percent(value) {
  return typeof value === "number" && Number.isFinite(value)
    ? `${Math.round(value * 100)}%`
    : "—";
}

function TeamEmpty() {
  return (
    <section className="dashboard-empty" aria-live="polite">
      <h2>Your team has not entered the runtime yet</h2>
      <p>Results and unit responses will appear here after the first round is advanced.</p>
    </section>
  );
}

export default function Dashboard({ data }) {
  const team = data?.teams?.find((item) => item.id === data.selected_team_id) || data?.teams?.[0];
  if (!team) return <TeamEmpty />;
  const hasAttention = team.attention.length > 0;
  return (
    <div className="dashboard-page">
      <section className="dashboard-context">
        <div>
          <p className="eyebrow">Where the business stands this round</p>
          <p className="dashboard-context__copy">{team.name} · {team.latest_result_round ? `Results through round ${team.latest_result_round}` : "No round results yet"}</p>
        </div>
        {team.strategy && <span className="dashboard-context__chip">{team.strategy}</span>}
      </section>

      {hasAttention && (
        <section className="dashboard-attention" aria-labelledby="dashboard-attention-heading">
          <div className="dashboard-section-heading">
            <h2 id="dashboard-attention-heading">Needs attention</h2>
            <StatusBadge status="needs-attention" label={`${team.attention.length} open`} />
          </div>
          <ul>
            {team.attention.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </section>
      )}

      <div className="dashboard-grid">
        <section className="dashboard-chain" aria-labelledby="dashboard-chain-heading">
          <div className="dashboard-section-heading">
            <h2 id="dashboard-chain-heading">How each unit is responding</h2>
            <span className="dashboard-muted">{team.units.length} units with runtime records</span>
          </div>
          {team.units.length === 0 ? (
            <p className="dashboard-muted dashboard-empty-inline">No unit response records have been persisted for this round.</p>
          ) : team.units.map((unit) => (
            <article className="dashboard-unit" key={unit.key}>
              <h3>{unit.name}{unit.people !== null ? ` · ${unit.people} people` : ""}</h3>
              <p><b>Running</b> {unit.running.length ? unit.running.join(", ") : "No asset record"}</p>
              <p><b>Implemented</b> {unit.implemented.length ? unit.implemented.join(" · ") : "No rollout record"}</p>
              <p><b>Responding</b> adoption {percent(unit.adoption)}{unit.process ? ` · process ${unit.process}` : ""}</p>
              <p><b>Contributing</b> {unit.contributing.length ? unit.contributing.join(", ") : "No capability record"}</p>
            </article>
          ))}
        </section>

        <aside className="dashboard-side">
          <section className="dashboard-scorecard" aria-labelledby="dashboard-scorecard-heading">
            <h2 id="dashboard-scorecard-heading">Balanced Scorecard</h2>
            <div className="dashboard-scorecard__grid">
              {scorecard.map(([key, label]) => (
                <div className="dashboard-scorecard__tile" key={key}>
                  <span>{label}</span>
                  <strong>{percent(team.scorecard[key])}</strong>
                </div>
              ))}
            </div>
          </section>
          <section className="dashboard-signals" aria-labelledby="dashboard-signals-heading">
            <div className="dashboard-section-heading">
              <h2 id="dashboard-signals-heading">Open signals</h2>
              <StatusBadge status={team.open_signals.length ? "needs-attention" : "complete"} label={`${team.open_signals.length} open`} />
            </div>
            {team.open_signals.length === 0 ? <p className="dashboard-muted">No open signal records.</p> : (
              <ul>
                {team.open_signals.map((signal) => <li key={`${signal.key}-${signal.first_shown_round || "now"}`}><strong>{signal.key}</strong>{signal.capability ? ` · ${signal.capability}` : ""}</li>)}
              </ul>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}
