import { useState } from "react";
import { DetailTable, OptionCard, OptionRow, SplitRule, StatusBadge } from "../components/index.js";

const statuses = ["complete", "partly-done", "needs-attention", "not-started"];
const rows = [
  { key: "warehouse", name: "Warehouse", status: <StatusBadge status="needs-attention" />, detail: "Needs a decision this round" },
  { key: "operations", name: "Operations", status: <StatusBadge status="complete" />, detail: "On track" }
];

export default function DevComponents() {
  const [service, setService] = useState("standard");
  const [strategy, setStrategy] = useState("balanced");
  const [opened, setOpened] = useState("");

  return (
    <main className="app-shell component-gallery">
      <header className="page-header">
        <p className="eyebrow">Development gallery</p>
        <h1>Shared components</h1>
        <p className="page-lede">The reusable grammar for the student loop. This page contains no simulation data.</p>
      </header>

      <section className="gallery-section" aria-labelledby="badges-heading">
        <h2 id="badges-heading">Status badges</h2>
        <div className="component-row">{statuses.map((status) => <StatusBadge key={status} status={status} />)}</div>
      </section>

      <section className="gallery-section" aria-labelledby="rows-heading">
        <h2 id="rows-heading">Single-line choices</h2>
        <div className="choice-stack">
          <OptionRow label="Basic support" detail="$4,000 per round" selected={service === "basic"} onSelect={() => setService("basic")} />
          <OptionRow label="Standard support" detail="$9,100 per round" selected={service === "standard"} onSelect={() => setService("standard")} />
          <OptionRow label="Premium support" detail="Unavailable until the next round" disabled disabledReason="Requires an active vendor contract" />
        </div>
      </section>

      <section className="gallery-section" aria-labelledby="cards-heading">
        <h2 id="cards-heading">Multi-line choices</h2>
        <div className="option-card-grid">
          <OptionCard title="Balanced" detail="Protect capacity while improving service" selected={strategy === "balanced"} onSelect={() => setStrategy("balanced")} />
          <OptionCard title="Low-cost leadership" detail="Reduce spend first; headroom is limited" selected={strategy === "cost"} onSelect={() => setStrategy("cost")} />
          <OptionCard title="Customer insight" detail="Unavailable until a strategy is locked" disabled disabledReason="Choose a strategy before reviewing this option" />
        </div>
      </section>

      <section className="gallery-section" aria-labelledby="table-heading">
        <h2 id="table-heading">Rows that open detail</h2>
        <DetailTable columns={[{ key: "name", label: "Unit" }, { key: "status", label: "Status" }, { key: "detail", label: "Detail" }]} rows={rows} onRowClick={(row) => setOpened(row.name)} />
        {opened && <p className="gallery-feedback" role="status">Opened {opened} details.</p>}
      </section>

      <section className="gallery-section" aria-labelledby="split-heading">
        <h2 id="split-heading">Split rule</h2>
        <SplitRule label="What determines the split?" options={["Steady on-premises", "Bursty in cloud"]} />
      </section>
    </main>
  );
}
