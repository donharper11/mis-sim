/* eslint-disable react/prop-types */
const decisionItems = ["Strategy", "Platform", "Components", "Rollout", "Security", "Services", "People"];
const resultItems = ["Dashboard", "Challenges", "Review", "Debrief"];

function NavItem({ label, active }) {
  return (
    <span className={`app-shell__nav-item${active ? " app-shell__nav-item--active" : ""}`} aria-current={active ? "page" : undefined}>
      {label}
    </span>
  );
}

export default function AppShell({ me, instance, schedule, children }) {
  const round = instance ? Math.max(instance.current_round, 1) : null;
  const totalRounds = instance?.total_rounds || null;
  return (
    <div className="product-shell">
      <aside className="product-shell__sidebar">
        <div className="product-shell__brand">MIS Simulation</div>
        {me?.name && <div className="product-shell__user">{me.name}</div>}
        <nav aria-label="Main navigation">
          <div className="product-shell__nav-group">
            {resultItems.map((item) => <NavItem key={item} label={item} active={item === "Dashboard"} />)}
          </div>
          <div className="product-shell__nav-label">Decisions</div>
          <div className="product-shell__nav-group">
            {decisionItems.map((item) => <NavItem key={item} label={item} />)}
          </div>
        </nav>
      </aside>
      <div className="product-shell__workspace">
        <header className="product-shell__topbar">
          <div>
            <p className="product-shell__context">{instance ? `Instance ${instance.instance_id}` : "No instance selected"}</p>
            <h1>Dashboard</h1>
          </div>
          <div className="product-shell__round" aria-label={round ? `Round ${round} of ${totalRounds}` : "Round unavailable"}>
            <span className="product-shell__round-label">Round</span>
            <strong>{round ? `${round} of ${totalRounds}` : "—"}</strong>
            {schedule?.deadline && <time dateTime={schedule.deadline}>Closes {new Date(schedule.deadline).toLocaleString()}</time>}
          </div>
        </header>
        <section className="product-shell__capital" aria-label="Capital summary">
          <div><span>Capital remaining</span><strong>—</strong></div>
          <div><span>Run-rate</span><strong>—</strong></div>
          <div><span>Round status</span><strong>{schedule?.decisions_locked ? "Locked" : "Open"}</strong></div>
        </section>
        <main className="product-shell__content">{children}</main>
      </div>
    </div>
  );
}
