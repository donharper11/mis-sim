"""Fresh-transaction production boundary for versioned simulation runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from contextlib import contextmanager
from copy import deepcopy
from typing import Any, Iterator

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.round import models as round_models
from app.round.models import RoundResult
from app.repo.base import ScopedRepo

from .consequences import quote_transition, resolve_transition
from .content import canonical_json, normalize_patch
from .estate import initialize_state
from .models import SimulationCheckpointV1, SimulationRunV1, SimulationSheetV1
from .types import (
    COMMAND_FIELDS,
    CheckpointStateV1,
    CommandV1,
    PackIdentityV1,
    RunViewV1,
    SheetPatchV1,
    SheetViewV1,
    SimulationError,
    RuntimePackV1,
)


def _positive(value: int, field: str) -> None:
    if type(value) is not int or value <= 0:
        raise SimulationError("invalid_input", field)


def _state_digest(state: CheckpointStateV1) -> str:
    return hashlib.sha256(canonical_json(state)).hexdigest()


def _jsonable(value: Any) -> Any:
    """Convert reducer output to the JSON contract before ORM binding."""
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump(mode="json", exclude_none=False))
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "value") and type(value).__module__ == "enum":
        return value.value
    return value


def _state_payload(state: CheckpointStateV1) -> dict[str, Any]:
    payload = state.model_dump(mode="json", exclude_none=False)
    # CommandV1's strict extra-field boundary distinguishes an omitted field
    # from an explicit null.  P4 repair witnesses contain command DTOs, so
    # retain required nullable fields in the state but use canonical command
    # objects at this nested persistence boundary.
    for assessment in payload.get("repair_assessment_history", []):
        for witness in (*assessment.get("candidates", []), *assessment.get("repaired_but_uncredited", [])):
            witness["commands"] = [{key: value for key, value in command.items() if value is not None} for command in witness.get("commands", [])]
    return payload


def _reducer_prior(state: CheckpointStateV1) -> CheckpointStateV1:
    """Keep the P4 reducer's command DTO boundary independent of persisted history.

    Repair witnesses retain strict command objects; the current P4 merge helper
    serializes those objects before reconstructing a state.  History is restored
    after reduction, while all transition inputs remain otherwise byte-identical.
    """
    if state.repair_assessment_history:
        return state.model_copy(update={"repair_assessment_history": []})
    return state


def _quote(pack: RuntimePackV1, state: CheckpointStateV1, commands: tuple[CommandV1, ...], round: int):
    prior = _reducer_prior(state)
    try:
        return quote_transition(pack, prior, commands, round)
    except Exception as exc:
        # P4 permits an unavoidable event loss to leave operating reserve below
        # zero, while the preview DTO intentionally exposes nonnegative money.
        # Keep the persisted balance untouched and quote future discretionary
        # work from the zero floor; the warning/result accounting remains owned
        # by the transition path.
        if prior.operating_reserve < 0 and "operating forecast" in str(exc):
            return quote_transition(pack, prior.model_copy(update={"operating_reserve": 0}), commands, round)
        raise


def _sheet_digest(round: int, revision: int, commands: list[CommandV1]) -> str:
    payload = {"version": 1, "round": round, "revision": revision,
               "commands": [command.model_dump(mode="json", exclude_none=True) for command in commands]}
    return hashlib.sha256(canonical_json(payload)).hexdigest()


def _commands(raw: Any) -> tuple[CommandV1, ...]:
    if not isinstance(raw, list):
        raise SimulationError("invalid_output", "sheet.commands")
    try:
        result = tuple(CommandV1.model_validate(item) for item in raw)
    except Exception as exc:
        raise SimulationError("invalid_output", "sheet.commands") from exc
    if len({item.key for item in result}) != len(result):
        raise SimulationError("invalid_output", "sheet.commands")
    return result


def _command_payload(command: CommandV1) -> dict[str, Any]:
    """Persist exactly the fields allowed by the command operation.

    Required nullable fields remain explicit (for example ``primary_for`` on
    an application purchase), while unrelated union fields remain omitted so
    strict reconstruction does not treat them as unexpected extras.
    """
    raw = command.model_dump(mode="json", exclude_none=False)
    allowed = {"key", "op", *COMMAND_FIELDS[command.op]}
    return {key: raw[key] for key in allowed if key in raw}


class SimulationService:
    """Own every operation's connection and transaction.

    ``engine`` is deliberately required.  The service never reads an environment
    variable or borrows a caller-owned Session.
    """

    def __init__(self, engine, runtime_pack: RuntimePackV1):
        self.engine = engine
        self.runtime_pack = runtime_pack

    @contextmanager
    def _transaction(self) -> Iterator[Session]:
        connection = self.engine.connect()
        # SQLite has no row-level locks.  BEGIN IMMEDIATE gives the service the
        # same serialized mutation boundary used by PostgreSQL's run-row lock.
        transaction = None
        if self.engine.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        else:
            transaction = connection.begin()
        session = Session(bind=connection, expire_on_commit=False)
        try:
            yield session
            session.flush()
            if transaction is None:
                connection.commit()
            else:
                transaction.commit()
        except Exception:
            if transaction is None:
                connection.rollback()
            else:
                transaction.rollback()
            raise
        finally:
            session.close()
            connection.close()

    def _scope(self, instance_id: int, team_id: int) -> tuple[int, int]:
        _positive(instance_id, "instance_id")
        _positive(team_id, "team_id")
        return instance_id, team_id

    def _check_pack(self, run: SimulationRunV1) -> None:
        if (run.pack_digest != self.runtime_pack.pack_digest
                or run.pack_key != self.runtime_pack.casepack.metadata.pack_key
                or run.pack_version != self.runtime_pack.casepack.metadata.pack_version):
            raise SimulationError("pack_mismatch", "pack_digest")

    def _repo(self, session: Session, instance_id: int, team_id: int) -> ScopedRepo:
        return ScopedRepo(session, instance_id, team_id)

    def _run(self, session: Session, instance_id: int, team_id: int, *, lock: bool = False) -> SimulationRunV1:
        statement = self._repo(session, instance_id, team_id).select(SimulationRunV1)
        if lock:
            statement = statement.with_for_update()
        run = session.execute(statement).scalar_one_or_none()
        if run is None:
            raise SimulationError("not_found", "run")
        self._check_pack(run)
        return run

    def _checkpoint(self, session: Session, instance_id: int, team_id: int, round: int) -> SimulationCheckpointV1:
        row = self._repo(session, instance_id, team_id).get(SimulationCheckpointV1, (instance_id, team_id, round))
        if row is None:
            raise SimulationError("invalid_output", "checkpoint")
        if row.pack_digest != self.runtime_pack.pack_digest:
            raise SimulationError("pack_mismatch", "checkpoint.pack_digest")
        try:
            state = CheckpointStateV1.model_validate(row.state)
        except Exception as exc:
            raise SimulationError("invalid_output", "checkpoint.state") from exc
        if _state_digest(state) != row.state_digest:
            raise SimulationError("invalid_output", "checkpoint.state_digest")
        return row

    def _sheet(self, session: Session, instance_id: int, team_id: int, round: int) -> SimulationSheetV1:
        sheet = self._repo(session, instance_id, team_id).get(SimulationSheetV1, (instance_id, team_id, round))
        if sheet is None:
            raise SimulationError("invalid_output", "sheet")
        return sheet

    def _state(self, session: Session, instance_id: int, team_id: int, round: int) -> CheckpointStateV1:
        row = self._checkpoint(session, instance_id, team_id, round)
        return CheckpointStateV1.model_validate(row.state)

    def _view(self, session: Session, run: SimulationRunV1) -> RunViewV1:
        checkpoint = self._checkpoint(session, run.instance_id, run.team_id, run.advanced_round)
        state = CheckpointStateV1.model_validate(checkpoint.state)
        sheet_view = None
        if run.status != "completed":
            sheet = self._sheet(session, run.instance_id, run.team_id, run.current_round)
            commands = _commands(sheet.commands)
            preview = _quote(self.runtime_pack, state, commands, run.current_round)
            sheet_view = SheetViewV1(
                version=1, round=sheet.round, revision=sheet.revision,
                locked_revision=sheet.locked_revision, commands=list(commands), preview=preview,
            )
        return RunViewV1(
            version=1,
            pack_identity=PackIdentityV1(
                key=run.pack_key, version=run.pack_version, digest=run.pack_digest,
            ),
            current_round=run.current_round, status=run.status,
            checkpoint_round=run.advanced_round, checkpoint_digest=checkpoint.state_digest,
            state=state, sheet=sheet_view,
        )

    def initialize(self, instance_id: int, team_id: int, strategy_key: str) -> RunViewV1:
        instance_id, team_id = self._scope(instance_id, team_id)
        try:
            with self._transaction() as session:
                # Refuse adoption of either historical runner state or a prior
                # versioned run.  Every table is queried with the complete scope.
                all_models = (*round_models.ALL_TABLES, SimulationRunV1, SimulationSheetV1, SimulationCheckpointV1)
                for model in all_models:
                    if session.execute(self._repo(session, instance_id, team_id).select(model)).first() is not None:
                        raise SimulationError("scope_exists", "instance_id")
                state = initialize_state(self.runtime_pack, strategy_key)
                run = SimulationRunV1(
                    instance_id=instance_id, team_id=team_id, version=1,
                    pack_key=self.runtime_pack.casepack.metadata.pack_key,
                    pack_version=self.runtime_pack.casepack.metadata.pack_version,
                    pack_digest=self.runtime_pack.pack_digest, current_round=1,
                    advanced_round=0, status="draft",
                )
                session.add(run)
                session.add(SimulationCheckpointV1(
                    instance_id=instance_id, team_id=team_id, round=0, version=1,
                    pack_digest=self.runtime_pack.pack_digest, sheet_revision=None,
                    state=_state_payload(state), state_digest=_state_digest(state),
                ))
                session.add(SimulationSheetV1(
                    instance_id=instance_id, team_id=team_id, round=1, revision=0,
                    locked_revision=None, commands=[], sheet_digest=None,
                ))
                session.flush()
                return self._view(session, run)
        except IntegrityError as exc:
            raise SimulationError("scope_exists", "instance_id") from exc

    def read(self, instance_id: int, team_id: int) -> RunViewV1:
        instance_id, team_id = self._scope(instance_id, team_id)
        with self._transaction() as session:
            run = self._run(session, instance_id, team_id)
            return self._view(session, run)

    def patch_sheet(self, instance_id: int, team_id: int, round: int, expected_revision: int, patch: SheetPatchV1) -> SheetViewV1:
        instance_id, team_id = self._scope(instance_id, team_id)
        if type(round) is not int or round < 1 or type(expected_revision) is not int or expected_revision < 0:
            raise SimulationError("invalid_input", "revision")
        if not isinstance(patch, SheetPatchV1):
            try:
                patch = SheetPatchV1.model_validate(patch)
            except Exception as exc:
                raise SimulationError("invalid_input", "patch") from exc
        with self._transaction() as session:
            run = self._run(session, instance_id, team_id, lock=True)
            if run.status == "completed" or round != run.current_round:
                raise SimulationError("round_state", "round")
            sheet = self._sheet(session, instance_id, team_id, round)
            if sheet.revision != expected_revision:
                raise SimulationError("revision_conflict", "revision")
            if sheet.locked_revision is not None:
                raise SimulationError("locked", "round")
            existing = _commands(sheet.commands)
            merged = normalize_patch(existing, patch)
            if not patch.replace_categories:
                return SheetViewV1(
                    version=1, round=round, revision=sheet.revision,
                    locked_revision=None, commands=list(existing),
                    preview=_quote(self.runtime_pack, self._state(session, instance_id, team_id, run.advanced_round), existing, round),
                )
            prior = self._state(session, instance_id, team_id, run.advanced_round)
            preview = _quote(self.runtime_pack, prior, merged, round)
            # CommandV1 distinguishes an explicitly supplied nullable field
            # (for example ``primary_for: null`` on a purchase) from an
            # omitted required field.  Preserve those nulls across the
            # persisted sheet so the strict command boundary can reconstruct
            # the same typed command at lock/read time.
            sheet.commands = [_command_payload(command) for command in merged]
            sheet.revision += 1
            session.flush()
            return SheetViewV1(version=1, round=round, revision=sheet.revision, locked_revision=None, commands=list(merged), preview=preview)

    def lock(self, instance_id: int, team_id: int, round: int, expected_revision: int) -> SheetViewV1:
        instance_id, team_id = self._scope(instance_id, team_id)
        with self._transaction() as session:
            run = self._run(session, instance_id, team_id, lock=True)
            if run.status == "completed" or round != run.current_round:
                raise SimulationError("round_state", "round")
            sheet = self._sheet(session, instance_id, team_id, round)
            if sheet.locked_revision is not None:
                if sheet.locked_revision != expected_revision:
                    raise SimulationError("revision_conflict", "revision")
                return self._sheet_view(session, run, sheet)
            if sheet.revision != expected_revision:
                raise SimulationError("revision_conflict", "revision")
            commands = _commands(sheet.commands)
            prior = self._state(session, instance_id, team_id, run.advanced_round)
            preview = _quote(self.runtime_pack, prior, commands, round)
            sheet.locked_revision = sheet.revision
            sheet.sheet_digest = _sheet_digest(round, sheet.revision, list(commands))
            run.status = "locked"
            session.flush()
            return SheetViewV1(version=1, round=round, revision=sheet.revision, locked_revision=sheet.locked_revision, commands=list(commands), preview=preview)

    def _sheet_view(self, session: Session, run: SimulationRunV1, sheet: SimulationSheetV1) -> SheetViewV1:
        commands = _commands(sheet.commands)
        prior = self._state(session, run.instance_id, run.team_id, run.advanced_round)
        return SheetViewV1(version=1, round=sheet.round, revision=sheet.revision, locked_revision=sheet.locked_revision, commands=list(commands), preview=_quote(self.runtime_pack, prior, commands, sheet.round))

    def reopen(self, instance_id: int, team_id: int, round: int, expected_revision: int) -> SheetViewV1:
        instance_id, team_id = self._scope(instance_id, team_id)
        with self._transaction() as session:
            run = self._run(session, instance_id, team_id, lock=True)
            if run.status == "completed" or round != run.current_round or run.advanced_round >= round:
                raise SimulationError("round_state", "round")
            sheet = self._sheet(session, instance_id, team_id, round)
            if sheet.locked_revision is None:
                raise SimulationError("locked", "round")
            if sheet.locked_revision != expected_revision:
                raise SimulationError("revision_conflict", "revision")
            sheet.revision += 1
            sheet.locked_revision = None
            sheet.sheet_digest = None
            run.status = "draft"
            session.flush()
            return self._sheet_view(session, run, sheet)

    def advance(self, instance_id: int, team_id: int, round: int, locked_revision: int) -> dict[str, Any]:
        instance_id, team_id = self._scope(instance_id, team_id)
        if type(round) is not int or round < 1 or type(locked_revision) is not int or locked_revision < 0:
            raise SimulationError("invalid_input", "round")
        with self._transaction() as session:
            run = self._run(session, instance_id, team_id, lock=True)
            # Older completed rounds are immutable and retryable.  The checkpoint's
            # sheet revision is the authoritative idempotency key.
            if run.advanced_round >= round:
                checkpoint = self._checkpoint(session, instance_id, team_id, round)
                if checkpoint.sheet_revision != locked_revision:
                    raise SimulationError("revision_conflict", "revision")
                result = self._repo(session, instance_id, team_id).get(RoundResult, (instance_id, team_id, round))
                if result is None:
                    raise SimulationError("invalid_output", "round_result")
                return deepcopy(result.payload)
            if round != run.current_round:
                raise SimulationError("round_state", "round")
            if run.status != "locked":
                raise SimulationError("locked", "round")
            sheet = self._sheet(session, instance_id, team_id, round)
            if sheet.locked_revision != locked_revision:
                raise SimulationError("revision_conflict", "revision")
            if sheet.sheet_digest != _sheet_digest(round, sheet.revision, _commands(sheet.commands)):
                raise SimulationError("invalid_output", "sheet_digest")
            prior = self._state(session, instance_id, team_id, round - 1)
            commands = _commands(sheet.commands)
            transition = resolve_transition(self.runtime_pack, _reducer_prior(prior), commands, round)
            state = transition.state
            if prior.repair_assessment_history:
                state = state.model_copy(update={
                    "repair_assessment_history": list(prior.repair_assessment_history) + list(state.repair_assessment_history),
                })
            result = _jsonable(dict(transition.result))
            # Force the same finite canonical JSON boundary used by checkpoint
            # digests before touching either result row or pointer.
            result = json.loads(json.dumps(result, allow_nan=False, separators=(",", ":")))
            result.setdefault("round", round)
            session.add(SimulationCheckpointV1(
                instance_id=instance_id, team_id=team_id, round=round, version=1,
                pack_digest=self.runtime_pack.pack_digest, sheet_revision=locked_revision,
                state=_state_payload(state), state_digest=_state_digest(state),
            ))
            existing_result = self._repo(session, instance_id, team_id).get(RoundResult, (instance_id, team_id, round))
            if existing_result is not None:
                raise SimulationError("round_state", "round")
            session.add(RoundResult(instance_id=instance_id, team_id=team_id, round=round, payload=result))
            run.advanced_round = round
            if round == self.runtime_pack.casepack.metadata.rounds:
                run.current_round = round
                run.status = "completed"
            else:
                run.current_round = round + 1
                run.status = "draft"
                session.add(SimulationSheetV1(
                    instance_id=instance_id, team_id=team_id, round=round + 1,
                    revision=0, locked_revision=None, commands=[], sheet_digest=None,
                ))
            session.flush()
            return deepcopy(result)
