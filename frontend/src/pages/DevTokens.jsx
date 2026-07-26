import { useEffect, useState } from "react";
import { Button, Select, Table } from "antd";
import { useTranslation } from "react-i18next";

const semanticGroups = [
  {
    label: "Surface roles",
    tokens: [
      "--surface-page",
      "--surface-card",
      "--surface-raised",
      "--surface-sunken",
      "--surface-sidebar",
      "--surface-sidebar-active",
      "--surface-topbar",
      "--surface-table-header",
      "--surface-table-stripe",
      "--surface-row-highlight",
      "--overlay-scrim"
    ]
  },
  {
    label: "Text roles",
    tokens: [
      "--text-primary",
      "--text-secondary",
      "--text-muted",
      "--text-hint",
      "--text-inverse",
      "--text-link",
      "--text-on-sidebar",
      "--text-on-sidebar-muted",
      "--text-on-sidebar-section"
    ]
  },
  {
    label: "Border roles",
    tokens: ["--border-default", "--border-strong", "--border-focus", "--border-annotation"]
  },
  {
    label: "Status roles",
    tokens: [
      "--status-ok-bg",
      "--status-ok-text",
      "--status-ok-marker",
      "--status-warn-bg",
      "--status-warn-text",
      "--status-warn-marker",
      "--status-danger-bg",
      "--status-danger-text",
      "--status-danger-marker",
      "--status-info-bg",
      "--status-info-text",
      "--status-info-marker",
      "--status-neutral-bg",
      "--status-neutral-text",
      "--status-neutral-marker"
    ]
  },
  {
    label: "Accent roles",
    tokens: ["--accent-1", "--accent-2", "--accent-3", "--accent-4", "--accent-5", "--accent-6", "--accent-7"]
  },
  {
    label: "Chart roles",
    tokens: ["--chart-1", "--chart-2", "--chart-3", "--chart-4", "--chart-5", "--chart-6", "--chart-highlight"]
  },
  {
    label: "Action roles",
    tokens: [
      "--action-primary",
      "--action-primary-hover",
      "--action-primary-text",
      "--action-secondary",
      "--action-secondary-hover",
      "--action-disabled",
      "--action-disabled-text"
    ]
  },
  {
    label: "Input roles",
    tokens: [
      "--input-bg",
      "--input-border",
      "--input-border-focus",
      "--input-text",
      "--input-editable-bg",
      "--input-disabled-bg"
    ]
  },
  {
    label: "Font roles",
    tokens: ["--font-body", "--font-mono"]
  },
  {
    label: "Space roles",
    tokens: [
      "--space-xs",
      "--space-sm",
      "--space-md",
      "--space-lg",
      "--space-xl",
      "--space-2xl",
      "--space-3xl",
      "--space-4xl"
    ]
  },
  {
    label: "Radius roles",
    tokens: ["--radius"]
  }
];

const primitiveGroups = [
  {
    label: "Primitive colours",
    tokens: [
      "--p-white",
      "--p-slate-25",
      "--p-slate-50",
      "--p-slate-100",
      "--p-slate-200",
      "--p-slate-300",
      "--p-slate-400",
      "--p-slate-500",
      "--p-slate-600",
      "--p-slate-700",
      "--p-slate-800",
      "--p-slate-900",
      "--p-navy-900",
      "--p-blue-50",
      "--p-blue-500",
      "--p-blue-700",
      "--p-blue-800",
      "--p-green-50",
      "--p-green-500",
      "--p-green-800",
      "--p-amber-50",
      "--p-amber-500",
      "--p-amber-800",
      "--p-red-50",
      "--p-red-500",
      "--p-red-800",
      "--p-purple-500",
      "--p-teal-500"
    ]
  },
  {
    label: "Primitive fonts",
    tokens: ["--p-font-body", "--p-font-mono"]
  },
  {
    label: "Primitive sizes",
    tokens: [
      "--p-size-4",
      "--p-size-8",
      "--p-size-12",
      "--p-size-16",
      "--p-size-20",
      "--p-size-24",
      "--p-size-32",
      "--p-size-40"
    ]
  }
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

const tokenGroups = [...semanticGroups, ...primitiveGroups];

export const devTokenGroups = tokenGroups;

export default function DevTokens() {
  const { t } = useTranslation();
  const [tokens, setTokens] = useState(new Map());

  useEffect(() => {
    const styles = getComputedStyle(document.documentElement);
    setTokens(
      new Map(
        tokenGroups.flatMap((group) =>
          group.tokens.map((name) => [name, styles.getPropertyValue(name).trim()])
        )
      )
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

      {tokenGroups.map((group) => (
        <section className="token-section" aria-label={group.label} key={group.label}>
          <h2>{group.label}</h2>
          <div className="swatch-grid">
            {group.tokens.map((name) => {
              const value = tokens.get(name) ?? "";

              return (
                <article className="swatch-card" key={name}>
                  <div className="swatch-sample" style={{ background: value }} />
                  <div className="swatch-copy">
                    <strong>{name}</strong>
                    <span>{value}</span>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      ))}
    </main>
  );
}
