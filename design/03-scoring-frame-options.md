# Outcome Frame — Ch 1 Objectives vs Balanced Scorecard

Which frame the student sees as the **headline** each round. This is a presentation and
content decision, not an engine decision — the engine produces the same movements either
way.

## The three candidates

**A. Laudon Ch 1 strategic business objectives** — Operational Excellence · New Products
& Business Models · Customer & Supplier Intimacy · Improved Decision Making ·
Competitive Advantage · Survival. *(mis_lite has 5 of the 6.)*

**B. mis_lite impact areas** — Operational Efficiency · Customer Intimacy · Market Share
· Profitability · Security Resilience.

**C. Balanced Scorecard** (Ch 12) — Financial · Customer · Internal Business Process ·
Learning & Growth.

## Why C fits the engine best

The engine produces four families of output, and they map onto BSC almost exactly:

| BSC perspective | What the engine already produces |
|---|---|
| **Financial** | capex, opex run-rate, TCO variance, cost per transaction, debt ledger |
| **Customer** | service outcomes, availability, unmet demand, outage blast radius |
| **Internal Process** | realised value per capability, coverage, integration, data adequacy |
| **Learning & Growth** | training coverage, adoption, resistance, staff skills, governance maturity |

**Learning & Growth is the deciding argument.** Neither A nor B has a slot for the
organisational term — and the whole Tech × Org × Mgmt design turns on it. Under frame A
or B, a team's training and adoption investment has nowhere to show up on the headline
scorecard, which undercuts the sim's central lesson.

BSC is also a business framework rather than an IT one, so it passes the *"what does it
cost, who does it affect, what happens if it fails"* filter cleanly.

## Recommendation — use both, at their natural altitudes

They are not competing; they answer different questions.

```
  Ch 1 objectives  →  WHY are we investing?
                      Framing for the Strategic Intent Declaration.
                      "This investment serves Operational Excellence."

  Balanced Scorecard → HOW are we doing?
                      The round scorecard and the debrief headline.
```

This keeps both harvested content sets in play, puts each where it teaches best, and
covers Ch 1 and Ch 12 without either becoming decoration.

## What this means for the harvest

- `objectives` (5 rows) — keep, re-purposed as declaration vocabulary. Consider adding
  Survival to complete Laudon's six
- `impact_areas` (5 rows) — retire as a headline frame. Two of the five (Market Share,
  Profitability) collapse into BSC Financial; Security Resilience becomes a risk readout
  rather than a scorecard quadrant
- `kpi_scores` table shape (5 fixed columns) — replace with a BSC four-perspective
  structure, or a generic `scorecard_metric` table so the frame is casepack-configurable
