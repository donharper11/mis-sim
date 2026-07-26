import { useEffect, useState } from "react";
import { Button, Select, Table } from "antd";
import { useTranslation } from "react-i18next";

const cssVariables = [
  "--bg-sidebar",
  "--bg-sidebar-active",
  "--bg-content",
  "--bg-card",
  "--bg-table-header",
  "--bg-table-alt",
  "--bg-topbar",
  "--bg-highlight-row",
  "--text-primary",
  "--text-secondary",
  "--text-muted",
  "--text-hint",
  "--text-sidebar",
  "--text-sidebar-muted",
  "--text-sidebar-section",
  "--text-link",
  "--accent-green",
  "--accent-blue",
  "--accent-purple",
  "--accent-amber",
  "--accent-red",
  "--accent-teal",
  "--accent-navy",
  "--status-compliant-bg",
  "--status-compliant-text",
  "--status-risk-bg",
  "--status-risk-text",
  "--status-danger-bg",
  "--status-danger-text",
  "--status-pending-bg",
  "--status-pending-text",
  "--status-active-bg",
  "--status-active-text",
  "--status-inactive-bg",
  "--status-inactive-text",
  "--color-surface-50",
  "--color-surface-100",
  "--color-surface-200",
  "--color-surface-300",
  "--color-surface-400",
  "--color-surface-500",
  "--color-surface-600",
  "--color-surface-700",
  "--color-surface-800",
  "--color-surface-900",
  "--topbar-bg",
  "--topbar-text",
  "--topbar-text-secondary",
  "--topbar-border",
  "--brand-primary",
  "--color-header-financial",
  "--color-header-strategic",
  "--color-header-market",
  "--color-header-decision",
  "--color-header-results",
  "--color-header-neutral",
  "--color-positive",
  "--color-negative",
  "--color-warning",
  "--color-info",
  "--color-neutral",
  "--color-primary",
  "--color-primary-hover",
  "--color-primary-light",
  "--color-input-bg",
  "--color-input-border",
  "--color-input-focus",
  "--color-input-editable",
  "--color-text-primary",
  "--color-text-secondary",
  "--color-text-inverse",
  "--color-text-link",
  "--chart-1",
  "--chart-2",
  "--chart-3",
  "--chart-4",
  "--chart-5",
  "--chart-6",
  "--chart-your-team",
  "--font-body",
  "--font-mono",
  "--space-xs",
  "--space-sm",
  "--space-md",
  "--space-lg",
  "--space-xl",
  "--space-2xl",
  "--space-3xl",
  "--space-4xl"
];

const rows = [
  { key: "primary", component: "Button", state: "Primary" },
  { key: "select", component: "Select", state: "Ready" },
  { key: "table", component: "Table", state: "Data" }
];

const columns = [
  { title: "Component", dataIndex: "component", key: "component" },
  { title: "State", dataIndex: "state", key: "state" }
];

export default function DevTokens() {
  const { t } = useTranslation();
  const [tokens, setTokens] = useState([]);

  useEffect(() => {
    const styles = getComputedStyle(document.documentElement);
    setTokens(
      cssVariables.map((name) => ({
        name,
        value: styles.getPropertyValue(name).trim()
      }))
    );
  }, []);

  return (
    <main className="app-shell">
      <header className="page-header">
        <h1>{t("dev.tokens.title")}</h1>
      </header>

      <section className="control-strip" aria-label="Ant Design controls">
        <Button type="primary">Button</Button>
        <Select
          defaultValue="ready"
          options={[
            { value: "ready", label: "Ready" },
            { value: "blocked", label: "Blocked" }
          ]}
        />
      </section>

      <Table
        className="component-table"
        columns={columns}
        dataSource={rows}
        pagination={false}
        size="small"
      />

      <section className="swatch-grid" aria-label="CSS variables">
        {tokens.map((item) => (
          <article className="swatch-card" key={item.name}>
            <div className="swatch-sample" style={{ background: item.value }} />
            <div className="swatch-copy">
              <strong>{item.name}</strong>
              <span>{item.value}</span>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

