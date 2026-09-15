/* eslint-disable react/prop-types */
export default function SplitRule({ label, options }) {
  return (
    <div className="split-rule" aria-label={label}>
      <span className="split-rule__label">{label}</span>
      <div className="split-rule__options">
        {options.map((option) => <span className="split-rule__option" key={option}>{option}</span>)}
      </div>
    </div>
  );
}
