/* eslint-disable react/prop-types */
const STATUS = {
  complete: { label: "Complete", className: "status-badge--ok" },
  "partly-done": { label: "Partly done", className: "status-badge--info" },
  "needs-attention": { label: "Needs attention", className: "status-badge--warn" },
  "not-started": { label: "Not started", className: "status-badge--neutral" }
};

export default function StatusBadge({ status, label }) {
  const definition = STATUS[status];
  if (!definition) throw new Error(`Unknown status badge: ${status}`);
  return (
    <span className={`status-badge ${definition.className}`} data-status={status}>
      <span className="status-badge__marker" aria-hidden="true" />
      {label || definition.label}
    </span>
  );
}

export { STATUS };
