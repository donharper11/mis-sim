/* eslint-disable react/prop-types */
export default function OptionRow({ label, detail, selected = false, disabled = false, disabledReason, onSelect }) {
  const description = disabled ? disabledReason : detail;
  return (
    <button
      type="button"
      className={`option-row${selected ? " option-row--selected" : ""}`}
      disabled={disabled}
      aria-pressed={selected}
      aria-label={disabled && disabledReason ? `${label}: ${disabledReason}` : label}
      onClick={onSelect}
    >
      <span className="option-row__marker" aria-hidden="true">{selected ? "●" : "○"}</span>
      <span className="option-row__copy">
        <span className="option-row__label">{label}</span>
        {description && <span className="option-row__detail">{description}</span>}
      </span>
    </button>
  );
}
