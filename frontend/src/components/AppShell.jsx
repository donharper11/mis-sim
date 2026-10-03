/* eslint-disable react/prop-types */
import { NavLink } from "react-router-dom";

const resultItems = ["Dashboard", "Challenges", "Review & Budget", "Debrief"];

const phases = [
  { num: 1, label: "Strategy", to: "/strategy" },
  { num: 2, label: "IT Infrastructure", to: "/infrastructure" },
  { num: 3, label: "Applications", to: "/applications" },
  { num: 4, label: "Rollout & Adoption", to: "/rollout" },
  { num: 5, label: "Review & Budget", to: "/review" },
];

function resultPath(item) {
  if (item === "Dashboard") return "/";
  if (item === "Challenges") return "/challenges";
  if (item === "Review & Budget") return "/review";
  if (item === "Debrief") return "/debrief";
  return undefined;
}

function NavItem({ label, active, to }) {
  const className = `app-shell__nav-item product-shell__nav-item${active ? " product-shell__nav-item--active" : ""}`;
  return to ? <NavLink className={className} to={to} end={to === "/"}>{label}</NavLink> : <span className={className}>{label}</span>;
}

function PhaseItem({ num, label, to, active }) {
  return (
    <NavLink className={`product-shell__phase${active ? " product-shell__phase--active" : ""}`} to={to}>
      <span className="product-shell__phase-num">{num}</span>
      <span>{label}</span>
    </NavLink>
  );
}

function formatMoney(value) {
  return typeof value === "number" && Number.isFinite(value) ? `$${value.toLocaleString()}` : "—";
}

export default function AppShell({ me, instance, schedule, dashboard, activePath = "/", pageTitle = "Dashboard", children }) {
  const round = instance ? Math.max(instance.current_round, 1) : null;
  const totalRounds = instance?.total_rounds || null;
  const team = dashboard?.teams?.find((item) => item.id === dashboard.selected_team_id) || dashboard?.teams?.[0];
  return (
    <div className="product-shell">
      <aside className="product-shell__sidebar">
        <div className="product-shell__brand">MIS Simulation</div>
        {me?.name && <div className="product-shell__user">{me.name}</div>}
        <nav aria-label="Main navigation">
          {(me?.role === "instructor" || me?.role === "admin") && <div className="product-shell__nav-group product-shell__nav-group--staff">
            <NavItem label="Instructor setup" to="/instructor/setup" active={activePath === "/instructor/setup"} />
            <NavItem label="Round control" to="/instructor/round-control" active={activePath === "/instructor/round-control"} />
            <NavItem label="Monitoring" to="/instructor/monitoring" active={activePath === "/instructor/monitoring"} />
            <NavItem label="Grading" to="/instructor/grading" active={activePath === "/instructor/grading"} />
            {me?.role === "admin" && <NavItem label="Registry" to="/instructor/registry" active={activePath === "/instructor/registry"} />}
          </div>}
          <div className="product-shell__nav-label">Results</div>
          <div className="product-shell__nav-group">
            {resultItems.map((item) => <NavItem key={item} label={item} to={resultPath(item)} active={(item === "Dashboard" && activePath === "/") || (item === "Challenges" && activePath === "/challenges") || (item === "Review & Budget" && activePath === "/review") || (item === "Debrief" && activePath === "/debrief")} />)}
          </div>
          <div className="product-shell__nav-label">Your Decisions</div>
          <div className="product-shell__nav-group">
            {phases.map((phase) => <PhaseItem key={phase.num} num={phase.num} label={phase.label} to={phase.to} active={activePath === phase.to} />)}
          </div>
        </nav>
      </aside>
      <div className="product-shell__workspace">
        <header className="product-shell__topbar">
          <div>
            <p className="product-shell__context">{instance ? `Instance ${instance.instance_id}` : "No instance selected"}</p>
            <h1>{pageTitle}</h1>
          </div>
          <div className="product-shell__round" aria-label={round ? `Round ${round} of ${totalRounds}` : "Round unavailable"}>
            <span className="product-shell__round-label">Round</span>
            <strong>{round ? `${round} of ${totalRounds}` : "—"}</strong>
            {schedule?.deadline && <time dateTime={schedule.deadline}>Closes {new Date(schedule.deadline).toLocaleString()}</time>}
          </div>
        </header>
        <section className="product-shell__capital" aria-label="Capital summary">
          <div><span>Capital remaining</span><strong>{formatMoney(team?.capital_remaining)}</strong></div>
          <div><span>Run-rate</span><strong>{formatMoney(team?.run_rate)}</strong></div>
          <div><span>Round status</span><strong>{schedule?.decisions_locked ? "Locked" : "Open"}</strong></div>
        </section>
        <main className="product-shell__content">{children}</main>
      </div>
    </div>
  );
}
