/* eslint-disable react/prop-types */
export default function PageTabs({ tabs, activeKey, onChange }) {
  return (
    <div className="page-tabs" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          type="button"
          role="tab"
          aria-selected={activeKey === tab.key}
          className={`page-tab${activeKey === tab.key ? " page-tab--active" : ""}`}
          onClick={() => onChange(tab.key)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
