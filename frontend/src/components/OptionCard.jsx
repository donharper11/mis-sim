/* eslint-disable react/prop-types */
export default function OptionCard({ title, detail, selected = false, disabled = false, disabledReason, onSelect, children }) {
  const description = disabled ? disabledReason : detail;
  return (
    <button
      type="button"
      className={`option-card${selected ? " option-card--selected" : ""}`}
      disabled={disabled}
      aria-pressed={selected}
      aria-label={disabled && disabledReason ? `${title}: ${disabledReason}` : title}
      onClick={onSelect}
    >
      <span className="option-card__heading">
        <span>
          <span className="option-card__title">{title}</span>
          {description && <span className="option-card__detail">{description}</span>}
        </span>
        {selected && <span className="option-card__check" aria-label="Selected">✓</span>}
      </span>
      {children && <span className="option-card__body">{children}</span>}
    </button>
  );
}
