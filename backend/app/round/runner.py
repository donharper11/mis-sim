"""The round runner -- the fixed resolution order (spec section 5.2) and the lock/advance
state machine (O1/O3). This is the orchestrator: 1.4 and 1.5 are pure, this is where state,
ordering, and persistence live.

Steps 10-12 bind to the merged 1.5/1.4 entry points (decision 11) -- ``advance_ledger`` ->
``resolve_events`` -> ``outage_duration`` -> re-``advance_ledger`` (fire stamp) ->
``project_signal_state`` -> ``score_team``. Per the O4 ruling (spec section 4), the ledger is
advanced and projected (step 10) BEFORE any responsiveness-bearing score; step 9's score
supplies raw tech/org/mgmt terms only (its responsiveness number is provisional and discarded,
finding 1.6-SR-001), and the single re-score at **step 12** is the authoritative per-capability
score for the round and the only place ``signal_responsiveness`` is recorded.

The re-score at step 12 runs **exactly once** (invariant I5): an event changes state so scores
must reflect it, but iterating to a fixed point makes outcomes unexplainable.
"""

from __future__ import annotations

from app.casepack.checks import ACTION_TYPES
from app.casepack.models import Casepack, Event
from app.engine import events as events_mod
from app.engine import ledger as ledger_mod
from app.engine.score import score_team
from app.round import models as m
from app.round import snapshot as snap

#: CONTRACTS.md decision_line.category enum (12 values) -- validation step 1.
DECISION_CATEGORIES = frozenset({
    "platform_service", "application", "integration", "lifecycle", "training",
    "process_redesign", "communication", "staffing", "governance", "policy",
    "event_response", "capital_request",
})


class LockStateError(RuntimeError):
    """A decision write against a locked round, or an advance of an unlocked round (O1/O3)."""


class SheetValidationError(ValueError):
    """The locked sheet failed validation (categories, affordability, legality) -- step 1."""


class RoundRunner:
    def __init__(self, session, pack: Casepack, instance_id: int, team_id: int):
        self.session = session
        self.pack = pack
        self.instance_id = instance_id
        self.team_id = team_id
        self._events: dict[str, Event] = {e.key: e for e in pack.events}

    # -- lock / advance state machine (O1, O3) -----------------------------------------

    def _team_row(self) -> m.TeamStateRow:
        row = self.session.get(m.TeamStateRow, (self.instance_id, self.team_id))
        if row is None:
            raise LockStateError("no team_state row for this instance/team")
        return row

    def is_locked(self, round: int) -> bool:
        row = self.session.get(m.TeamStateRow, (self.instance_id, self.team_id))
        return row is not None and row.locked_round is not None and row.locked_round >= round

    def assert_writable(self, round: int) -> None:
        """Reject a decision write against a locked round (O3: lock freezes input)."""
        if self.is_locked(round):
            raise LockStateError(f"round {round} is locked; decisions cannot be written")

    def lock(self, round: int) -> None:
        """Freeze the round's input sheet. 2.3 decides *when* to call this (spec section 1)."""
        row = self._team_row()
        row.locked_round = round
        self.session.flush()

    def unlock(self, round: int) -> None:
        """Instructor-only unlock (O1). It INVALIDATES the RoundResult (deletes it) rather than
        editing it -- so the result is never mutated (I6); a re-advance writes a fresh row."""
        row = self._team_row()
        if row.locked_round is not None and row.locked_round >= round:
            row.locked_round = round - 1 if round > 1 else None
        rr = self.session.get(m.RoundResult, (self.instance_id, self.team_id, round))
        if rr is not None:
            self.session.delete(rr)  # invalidate, never edit (O1); delete is not an UPDATE (I6)
        if row.advanced_round is not None and row.advanced_round >= round:
            row.advanced_round = round - 1 if round > 1 else None
        row.current_round = round
        self.session.flush()

    # -- decision sheet writing (partial-update semantics, decision 7 / I8) ------------

    def write_decision_sheet(self, round: int, lines: list[dict]) -> None:
        """Apply a decision-sheet payload with PARTIAL-UPDATE semantics (decision 7, I8): only the
        categories PRESENT in ``lines`` are rewritten this round; a category absent from the payload
        is left untouched (a full-replace payload silently wiping unsent categories is the GSCM bug
        decision 7 names). Rejected when the round is locked (O3: lock freezes input)."""
        self.assert_writable(round)
        categories = {ln["category"] for ln in lines}
        for cat in categories:
            existing = self.session.scalars(
                snap._scoped(m.DecisionLineRow, self.instance_id, self.team_id, round)
                .where(m.DecisionLineRow.category == cat)
            ).all()
            for e in existing:
                self.session.delete(e)
        for ln in lines:
            self.session.add(m.DecisionLineRow(
                instance_id=self.instance_id, team_id=self.team_id, round=round,
                key=ln["key"], category=ln["category"], capability=ln.get("capability"),
                capex=ln.get("capex", 0), rgt_tag=ln.get("rgt_tag", "run"),
                is_maintenance=ln.get("is_maintenance", False),
                action_type=ln.get("action_type"), target_key=ln.get("target_key"),
            ))
        self.session.flush()

    # -- step 1: validate the locked sheet ---------------------------------------------

    def _validate_sheet(self, round: int) -> None:
        lines = self.session.scalars(
            snap._scoped(m.DecisionLineRow, self.instance_id, self.team_id, round)
        ).all()
        for line in lines:
            if line.category not in DECISION_CATEGORIES:
                raise SheetValidationError(f"line {line.key!r}: unknown category {line.category!r}")
            if line.action_type is not None and line.action_type not in ACTION_TYPES:
                raise SheetValidationError(
                    f"line {line.key!r}: illegal action_type {line.action_type!r}"
                )
            if line.capex < 0:
                raise SheetValidationError(f"line {line.key!r}: negative capex {line.capex}")
        # affordability: committed spend must not exceed the round's authored budget.
        budget = self.pack.metadata.budget.capex_per_round
        cap = budget[round - 1] if round - 1 < len(budget) else 0
        committed = sum(max(0, int(line.capex)) for line in lines)
        if committed > cap:
            raise SheetValidationError(
                f"round {round}: committed {committed} exceeds budget {cap}"
            )

    # -- step 3: materialise in_flight arrivals ----------------------------------------

    def _materialise_in_flight(self, round: int) -> None:
        """Lead-time purchases become real nodes only at their arrival_round (O2): not in the
        graph early, which would inflate capacity."""
        arrivals = self.session.scalars(
            snap._scoped(m.InFlightRow, self.instance_id, self.team_id)
            .where(m.InFlightRow.arrival_round == round, m.InFlightRow.materialised == False)  # noqa: E712
        ).all()
        for order in arrivals:
            payload = dict(order.node_payload or {})
            exists = self.session.scalars(
                snap._scoped(m.ArchNodeRow, self.instance_id, self.team_id, round)
                .where(m.ArchNodeRow.key == order.key)
            ).first()
            if exists is None and payload:
                self.session.add(m.ArchNodeRow(
                    instance_id=self.instance_id, team_id=self.team_id, round=round,
                    key=order.key, roles_filled=payload.get("roles_filled", []),
                    availability=payload.get("availability", 0.99),
                    installed_round=payload.get("installed_round", round),
                    service_life_rounds=payload.get("service_life_rounds", 6),
                    serves=payload.get("serves", []), throughput=payload.get("throughput"),
                    owns_entities=payload.get("owns_entities", []),
                    placement=payload.get("placement"),
                    opex_contribution=payload.get("opex_contribution", 0),
                ))
            order.materialised = True
        self.session.flush()

    # -- opex ratchet (step 4/7): recomputed from live nodes, never accumulated (I7) ---

    def _recompute_opex(self, round: int) -> int:
        nodes = self.session.scalars(
            snap._scoped(m.ArchNodeRow, self.instance_id, self.team_id, round)
        ).all()
        return sum(int(n.opex_contribution) for n in nodes)  # SUM, never += (I7)

    # -- fired-event history (fire-once across rounds, 1.5 section 7.2) -----------------

    def _already_fired(self) -> frozenset[str]:
        prior = self.session.scalars(
            snap._scoped(m.RoundResult, self.instance_id, self.team_id)
        ).all()
        fired: set[str] = set()
        for rr in prior:
            for ev in (rr.payload or {}).get("events", []):
                fired.add(ev["key"])
        return frozenset(fired)

    def _fired_signal_keys(self, fired_events: tuple[str, ...]) -> frozenset[str]:
        """The SIGNAL keys a set of fired events stamps -- the `signal_open` precondition signals
        of each fired event. `advance_ledger(fired_signals=...)` matches these against watch-rule
        keys to stamp `fire_round` (binding to the engine's frozen signature, decision 11)."""
        keys: set[str] = set()
        for ev_key in fired_events:
            event = self._events.get(ev_key)
            if event is None:
                continue
            for pc in event.preconditions:
                if pc.type == "signal_open" and pc.signal is not None:
                    keys.add(pc.signal)
        return frozenset(keys)

    # -- step 13: debt accrual + TCO reconciliation ------------------------------------

    def _accrue_debt(self, round: int, ledger: tuple) -> None:
        """Deferral accrues debt (decision 6): an actionable signal first shown this round with no
        clearing action is a deferred fix. Visible only in the ledger, not the Tier-1 dashboard."""
        for s in ledger:
            if s.first_shown_round != round:
                continue
            if s.was_actionable and s.status != "cleared" and s.cheapest_fix_when_raised:
                self.session.add(m.DebtItemRow(
                    instance_id=self.instance_id, team_id=self.team_id, round=round,
                    capability=s.capability, amount=int(s.cheapest_fix_when_raised),
                    source_key=s.key, reason="deferral",
                ))
        self.session.flush()

    def _tco_variance(self, round: int) -> list[dict]:
        rows = self.session.scalars(
            snap._scoped(m.TcoForecastRow, self.instance_id, self.team_id, round)
        ).all()
        return [{"item": r.item, "forecast": int(r.forecast), "actual": int(r.actual)} for r in rows]

    # -- step 14 payload helpers -------------------------------------------------------

    @staticmethod
    def _row_dict(s) -> dict:
        return {
            "key": s.key, "episode_id": s.episode_id, "capability": s.capability,
            "metric": s.metric, "metric_kind": s.metric_kind, "value": s.value,
            "severity": s.severity, "status": s.status,
            "first_shown_round": s.first_shown_round, "cleared_round": s.cleared_round,
            "fire_round": s.fire_round, "cleared_by": list(s.cleared_by),
            "was_actionable": s.was_actionable, "cheapest_fix_when_raised": s.cheapest_fix_when_raised,
        }

    def _bucket_signals(self, ledger: tuple, round: int) -> dict:
        raised = [self._row_dict(s) for s in ledger if s.first_shown_round == round]
        cleared = [self._row_dict(s) for s in ledger if s.status == "cleared"]
        open_ = [self._row_dict(s) for s in ledger if s.status == "open"]
        fired = [self._row_dict(s) for s in ledger if s.status == "fired"]
        return {"raised": raised, "cleared": cleared, "open": open_, "fired": fired}

    def _missed_signals(self, ledger: tuple) -> list[dict]:
        """Signals that were actionable and never credited -- what prints 'you were told in round N'
        (spec section 5.3). `cheapest_fix_when_raised` is the 1.5 lookup, not an authored figure.

        Keyed by EPISODE identity, not by signal key (finding 1.6-A-001). `project_signal_state`
        returns one `SignalState` per ledger row in ledger order, so it is zipped element-for-element
        with the episodes: a later cleared episode must never mask an earlier open-then-fired episode
        of the same signal (that dropped a genuine "you were told in round N" from the debrief)."""
        out: list[dict] = []
        for s, p in zip(ledger, ledger_mod.project_signal_state(ledger)):
            if s.was_actionable and not p.acted_before_fire:
                out.append({
                    "key": s.key, "episode_id": s.episode_id,
                    "first_shown_round": s.first_shown_round,
                    "cheapest_fix_when_raised": s.cheapest_fix_when_raised,
                })
        return out

    # -- persistence -------------------------------------------------------------------

    def _persist_ledger(self, ledger: tuple, round: int) -> None:
        """Append-only, immutable (I9). A terminal or non-latest episode is carried forward
        byte-identical by ``advance_ledger``; ``merge`` re-persists each row by its episode PK
        (instance,team,key,episode_id), inserting new episodes and re-writing only the latest open
        episode as it legitimately transitions -- a prior episode row is never overwritten (I9)."""
        for s in ledger:
            self.session.merge(m.SignalRow(
                instance_id=self.instance_id, team_id=self.team_id, key=s.key,
                episode_id=s.episode_id, round=round, capability=s.capability, metric=s.metric,
                metric_kind=s.metric_kind, value=s.value, severity=s.severity, status=s.status,
                first_shown_round=s.first_shown_round, cleared_round=s.cleared_round,
                fire_round=s.fire_round, cleared_by=list(s.cleared_by),
                was_actionable=s.was_actionable, cheapest_fix_when_raised=s.cheapest_fix_when_raised,
            ))
        self.session.flush()

    # -- the resolution order (steps 1-14) ---------------------------------------------

    def advance(self, round: int) -> dict:
        """Run the fixed resolution order for one round and write the immutable RoundResult.
        Requires the round's sheet to be locked (O3: results are produced at advance, not lock)."""
        if not self.is_locked(round):
            raise LockStateError(f"round {round} is not locked; lock before advancing (O3)")

        self._validate_sheet(round)                 # 1  validate the locked sheet
        # 2 retirements/cancellations and 4-6 estate deltas are the round's persisted estate
        #   (seed-authored post-application state); the runner recomputes and derives from it.
        self._materialise_in_flight(round)          # 3  materialise in_flight arrivals
        opex = self._recompute_opex(round)          # 4/7 opex ratchet, recomputed (I7)

        prior_ledger = snap.load_prior_ledger(self.session, self.instance_id, self.team_id)

        # 9  raw tech/org/mgmt terms only; the responsiveness number here is provisional and
        #    discarded (O4 ruling / finding 1.6-SR-001). No signals projected into this pass.
        state_raw = snap.build_team_state(
            self.session, self.instance_id, self.team_id, round, self.pack, signals=()
        )
        _raw = score_team(self.pack, state_raw)  # provisional pre-event pass; discarded

        # 10 watch rules: raise / escalate / clear (no fires yet), then project -> SignalState
        ledger = ledger_mod.advance_ledger(prior_ledger, state_raw, self.pack)
        state_10 = snap.build_team_state(
            self.session, self.instance_id, self.team_id, round, self.pack,
            signals=ledger_mod.project_signal_state(ledger, current_round=round),
        )

        # 11 events: fire (O2 cap + suppression), blast radius, outcome application
        fired, suppressed = events_mod.resolve_events(
            state_10, self.pack, ledger, already_fired=self._already_fired()
        )
        event_records: list[dict] = []
        for ev_key in fired:
            event = self._events[ev_key]
            primary = events_mod.primary_capability(event, self.pack)
            node = events_mod.failed_node(event, state_10, self.pack)
            if node is not None and primary is not None:
                evidence = dict(events_mod.outage_duration(state_10, node, primary, self.pack))
            else:
                # no bound node -> empty radius, no duration (honest, not an error; spec 5.3)
                evidence = {"node": None, "blast_radius": []}
            evidence["key"] = ev_key
            evidence["outcomes"] = dict(event.outcomes or {})
            event_records.append(evidence)

        # second advance pass only stamps fire_round for the signals the fired events armed
        ledger = ledger_mod.advance_ledger(
            ledger, state_10, self.pack, fired_signals=self._fired_signal_keys(fired)
        )
        state_12 = snap.build_team_state(
            self.session, self.instance_id, self.team_id, round, self.pack,
            signals=ledger_mod.project_signal_state(ledger, current_round=round),
        )

        # 12 the single, authoritative re-score (I5). `signal_responsiveness` is read HERE, from
        #    the freshly-advanced ledger (O4). This score_team call is the ONLY re-entry (rescore).
        final_score = score_team(self.pack, state_12)

        # 13 accrue debt for deferrals; reconcile TCO forecasts
        self._accrue_debt(round, ledger)
        tco_variance = self._tco_variance(round)

        # 14 roll up the Balanced Scorecard and write the immutable RoundResult
        scorecard = self._rolled_scorecard(final_score, event_records)
        capex_spent = snap.committed_spend(self.session, self.instance_id, self.team_id, round)
        debt_total = self._debt_total(round)
        payload = {
            "instance_id": self.instance_id, "team_id": self.team_id, "round": round,
            "capabilities": [c for c in final_score.record()["capabilities"]],
            "scorecard": scorecard,
            "signals": self._bucket_signals(ledger, round),
            "events": event_records,
            "suppressed_events": [
                {"key": s.event_key, "reason": s.reason, "capability": s.capability}
                for s in suppressed
            ],
            "financials": {"capex_spent": capex_spent, "opex_runrate": opex, "debt_total": debt_total},
            "tco_variance": tco_variance,
            "missed_signals": self._missed_signals(ledger),
            "firm_score": final_score.firm_score,
        }

        self._persist_ledger(ledger, round)
        self._write_result(round, payload)

        # advance the pointer (O3): results are produced, move to the next round
        team_row = self._team_row()
        team_row.opex_runrate = opex
        team_row.advanced_round = round
        team_row.current_round = round + 1
        self.session.flush()
        return payload

    def _rolled_scorecard(self, final_score, event_records: list[dict]) -> dict:
        """Balanced Scorecard from the engine rollup, then apply fired events' scorecard deltas
        (spec step 14; events change the round's outcome)."""
        bsc = final_score.balanced_scorecard
        sc = {
            "financial": bsc.financial, "customer": bsc.customer,
            "internal_process": bsc.internal_process, "learning_growth": bsc.learning_growth,
        }
        for ev in event_records:
            for dim, delta in (ev.get("outcomes", {}).get("scorecard", {}) or {}).items():
                if dim in sc and isinstance(sc[dim], (int, float)):
                    sc[dim] = sc[dim] + delta
        return sc

    def _debt_total(self, round: int) -> int:
        rows = self.session.scalars(
            snap._scoped(m.DebtItemRow, self.instance_id, self.team_id)
            .where(m.DebtItemRow.round <= round)
        ).all()
        return sum(int(r.amount) for r in rows)

    def _write_result(self, round: int, payload: dict) -> None:
        """Write the immutable RoundResult. Re-running a round produces a NEW row only after the
        old one is invalidated by ``unlock`` (O1); an existing row is never UPDATEd (I6, decision 2)."""
        existing = self.session.get(m.RoundResult, (self.instance_id, self.team_id, round))
        if existing is not None:
            raise LockStateError(
                f"round {round} already has an immutable RoundResult; unlock to invalidate it (O1)"
            )
        self.session.add(m.RoundResult(
            instance_id=self.instance_id, team_id=self.team_id, round=round, payload=payload
        ))
        self.session.flush()
