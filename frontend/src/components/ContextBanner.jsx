/* eslint-disable react/prop-types */
export default function ContextBanner({ step, eyebrow, description, teamName, round, strategy }) {
  return (
    <section className="components-context" style={{ flexDirection: "column", alignItems: "flex-start" }}>
      <p className="eyebrow">Step {step} of 5</p>
      <p className="eyebrow" style={{ margin: 0 }}>{eyebrow}</p>
      {description && <p className="controls-description">{description}</p>}
      <div style={{ display: "flex", alignItems: "center", gap: "var(--space-md)", flexWrap: "wrap" }}>
        <p className="components-muted" style={{ margin: 0 }}>{teamName} · Round {round}</p>
        {strategy && <span className="dashboard-context__chip">{strategy}</span>}
      </div>
    </section>
  );
}
