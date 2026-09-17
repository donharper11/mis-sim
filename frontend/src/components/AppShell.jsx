/* eslint-disable react/prop-types */
import { NavLink } from "react-router-dom";
const decisionItems = ["Strategy", "Platform", "Components", "Rollout", "Security", "Services", "People", "Governance"];
const resultItems = ["Dashboard", "Challenges", "Review", "Debrief"];

function NavItem({ label, active, to }) {
  const className = `app-shell__nav-item${active ? " app-shell__nav-item--active" : ""}`;
  return to ? <NavLink className={className} to={to} end={to === "/"}>{label}</NavLink> : <span className={className}>{label}</span>;
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
          </div>}
          <div className="product-shell__nav-group">
            {resultItems.map((item) => <NavItem key={item} label={item} to={item === "Dashboard" ? "/" : item === "Challenges" ? "/challenges" : item === "Review" ? "/review" : item === "Debrief" ? "/debrief" : undefined} active={(item === "Dashboard" && activePath === "/") || (item === "Challenges" && activePath === "/challenges") || (item === "Review" && activePath === "/review") || (item === "Debrief" && activePath === "/debrief")} />)}
          </div>
          <div className="product-shell__nav-label">Decisions</div>
          <div className="product-shell__nav-group">
            {decisionItems.map((item) => <NavItem key={item} label={item} to={item === "Strategy" ? "/strategy" : item === "Platform" ? "/platform" : item === "Components" ? "/components" : item === "Rollout" ? "/rollout" : item === "Security" ? "/security" : item === "Services" ? "/services" : item === "People" ? "/people" : item === "Governance" ? "/governance" : undefined} active={activePath === `/${item.toLowerCase()}`} />)}
            <NavItem label="Budget" to="/budget" active={activePath === "/budget"} />
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
