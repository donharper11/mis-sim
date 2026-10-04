/* eslint-disable react/prop-types */
export default function ContextBanner({ description }) {
  if (!description) return null;
  return (
    <section className="components-context" style={{ flexDirection: "column", alignItems: "flex-start" }}>
      <p className="controls-description" style={{ margin: 0 }}>{description}</p>
    </section>
  );
}
