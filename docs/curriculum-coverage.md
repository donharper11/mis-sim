# Curriculum Coverage — the Chapter 5 concepts that are not catalog items

**Produced by** module 1.3, the mis_lite harvest · **Date:** 2026-08-18
**Source:** `mis_lite.component_types_master`, 45 rows, extracted read-only to
`backend/harvest/mis_lite/component_types_master.json`
**Basis:** `design/01-mis_lite-harvest.md` §3 · `CONTRACTS.md` ("Harvested mis_lite content")
· `handoffs/1.3-harvest/spec.md` §3 decision 3

---

## Why this file exists

`component_types_master` is the most-cited asset in the harvest and it is **a Laudon
Chapter 5 vocabulary list, not a parts list.** Entries include *Packet Switching*,
*TCP/IP*, *Analog Signals*, *Green Computing*, *Consumerization of IT*.

Those work correctly in mis_lite's preference model — a team sets an adoption level 1–100
and is scored on alignment. They **cannot** work as nodes in a dependency graph. You
cannot draw an edge from *Green Computing* to *Data Mart*, and *Analog Signals* has no
capacity, no availability and no service life. Putting them in `catalog.yaml` would mean
authoring an attribute vector for a concept, which is fiction dressed as seed data.

They are not discarded. They are **how the simulation proves it covers Chapter 5** — as
debrief concept links, coach material and quiz content. They are just not things you buy.

---

## Count drift, reported

`design/01` §3 writes *"Buildable (~19)"* and then **enumerates 21 names**. Spec §3
decision 3 repeats *"~19 of 45"* and *"~26 are concepts"*, both with tildes, and says the
buildable list *"is enumerated there"* — so the enumeration governs and the round numbers
do not.

```
enumerated buildable   21
concept / trend        24        (45 − 21)
```

**This file therefore documents 24 concepts, not 26.** No row is unaccounted for: 21 + 24
= 45. The drift is in the two prose estimates, not in the data.

---

## The 21 buildable rows, and where each one went

Only 21 of the 45 carry attributes an operational engine can use. Where they landed is a
judged decision (spec §5.2), and "not instantiated" is a real disposition — it means the
row is a legitimate option a *later* pack or a *later* round of authoring can take up, not
that it was lost.

| # | mis_lite row | cost_value | Landed in |
|---|---|---|---|
| 1 | High-Performance Server | 20000 | `platform.yaml` `compute_pool` (cost basis) |
| 2 | Cloud-Based Storage | 15000 | `platform.yaml` `storage_pool` |
| 3 | SQL Database | 10000 | `catalog.yaml` `order_db_cluster` |
| 4 | NoSQL Database | 12000 | `catalog.yaml` `nosql_database` |
| 5 | VPN Network | 8000 | not instantiated — `client_network` covers the network role |
| 6 | 5G Wireless Network | 20000 | not instantiated — same role as above |
| 9 | ERP Software Suite | 30000 | `catalog.yaml` `erp_suite` (licence base) |
| 12 | Virtualization | 15000 | `platform.yaml` `compute_pool` (the on-premises option) |
| 13 | PaaS | 20000 | not instantiated — expressed as the `cloud` placement on every item |
| 14 | IaaS | 25000 | not instantiated — expressed as the `cloud` placement on every item |
| 25 | SaaS | 18000 | `platform.yaml` `end_user_email`; also the `saas` placement everywhere |
| 33 | LAN | 6000 | not instantiated — `client_network` |
| 34 | WAN | 15000 | not instantiated — `client_network`; 0.3 §5.6 names "Network & WAN" as one panel |
| 37 | Data Warehouse | 20000 | `platform.yaml` `data_platform` (with row 45) |
| 38 | Data Mart | 12000 | not instantiated — `analytics_workspace` covers the analytics role |
| 39 | Hadoop | 18000 | not instantiated — technology choice below the business layer |
| 40 | In-Memory Computing | 25000 | not instantiated — a config tier, not a purchase |
| 41 | OLAP | 22000 | not instantiated — `analytics_workspace` |
| 43 | API Gateway | 10000 | `platform.yaml` `integration_api` (with `it_infrastructure_addons_master` row 4) |
| 44 | Next-Gen Firewall | 15000 | `catalog.yaml` `next_gen_firewall`, already present from 1.1 |
| 45 | Data Lake | 20000 | `platform.yaml` `data_platform` (with row 37) |

**Placement is not a component.** Rows 13, 14 and 25 (PaaS, IaaS, SaaS) are the three
placements every catalog item and platform service already offers as `deployment_modes` /
`placement_options`. Modelling them a second time as buyable items would let a student buy
"IaaS" *and* place something on-premises, which is not a thing that can be true.

---

## The 24 concept rows — curriculum reference, not catalog

Each is a Chapter 5 concept a debrief can link to. None is a purchase.

| # | Concept | Chapter 5 topic it evidences |
|---|---|---|
| 7 | On-Premises Deployment | IT infrastructure — where computing happens |
| 8 | Cloud-Based Deployment | IT infrastructure — where computing happens |
| 10 | Mobile Digital Platform | the mobile digital platform |
| 11 | Consumerization of IT | consumerization and BYOD |
| 15 | Edge Computing | contemporary hardware platform trends |
| 16 | Green Computing | contemporary hardware platform trends |
| 17 | High Performance Processors | contemporary hardware platform trends |
| 18 | Power Saving Processors | contemporary hardware platform trends |
| 19 | Linux/Open Source | contemporary software platform trends |
| 20 | Web Software — Java | software for the web |
| 21 | Web Software — JavaScript | software for the web |
| 22 | Web Software — HTML | software for the web |
| 23 | Web Software — HTML5 | software for the web |
| 24 | Web Services and SOA | web services and service-oriented architecture |
| 26 | Software Outsourcing | software outsourcing and cloud services |
| 27 | Mashups and Apps | mashups and apps |
| 28 | Client/Server Computing | IT infrastructure evolution — the five eras |
| 29 | Packet Switching | networking and communication technology |
| 30 | TCP/IP | networking and communication technology |
| 31 | Digital Signals | signals — digital vs analog |
| 32 | Analog Signals | signals — digital vs analog |
| 35 | MAN | types of network |
| 36 | Blockchain | contemporary data management trends |
| 42 | Data Mining | business intelligence and analytics |

**The line between the two tables** is the one `GOVERNANCE §2.1` draws: *what does it
cost, who does it affect, what happens if it fails?* A Data Warehouse has a cost, a set of
people who depend on it and a failure mode. TCP/IP has none of those in any sense a
business decision reaches — a student who has to understand how it *works* to make the
call is in an IT course, and it comes out of the catalog.

---

## Also curriculum, not catalog

| Source | Rows | Disposition |
|---|---|---|
| `objectives` | 5 | Laudon Ch 1 strategic business objectives (OEX, NPB, CSI, DMK, CMP). Authored into `labels.yaml` `misc` as the declaration vocabulary a strategy is argued in. Not a scored object in v1 |
| `impact_areas` | 5 | Operational Efficiency · Customer Intimacy · Market Share · Profitability · Security Resilience. Authored into `labels.yaml` `misc`. The Balanced Scorecard (Ch 12) is the presentation layer the pack actually scores on — `design/01` §6 carries this as an open question and it stays open |
| `business_processes_master` | 8 | Maps onto value-chain activities, which are a **platform constant** (the 1.2-020 ruling), not pack content. Not harvested |
| `change_management_master` | 8 | Big Bang · Phased · Pilot · Change Champions · Comprehensive Training · Ongoing Support · Knowledge Portal · Feedback Loops. Reference for the rollout mix; the pack expresses the mix as `training_options` + `process_option` per deployment |
