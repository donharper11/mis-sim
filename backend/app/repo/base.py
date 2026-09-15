"""Mandatory instance/team scope for runtime persistence access."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session


class ScopeError(ValueError):
    """A repository operation attempted to escape its bound scope."""


class ScopedRepo:
    """Repository whose every model read is bound to one simulation instance.

    ``instance_id`` is required. ``team_id`` is optional for instance-wide reads,
    but when the selected model has a team column it is applied whenever bound.
    """

    def __init__(self, session: Session, instance_id: int, team_id: int | None = None):
        if type(instance_id) is not int or instance_id <= 0:
            raise ScopeError("instance_id is required and must be a positive integer")
        if team_id is not None and (type(team_id) is not int or team_id <= 0):
            raise ScopeError("team_id must be a positive integer when provided")
        self.session = session
        self.instance_id = instance_id
        self.team_id = team_id

    @staticmethod
    def _columns(model):
        try:
            return inspect(model).mapper.column_attrs
        except (AttributeError, Exception) as exc:
            raise ScopeError(f"{model!r} is not a mapped runtime model") from exc

    def _scope_columns(self, model):
        columns = {column.key: getattr(model, column.key) for column in self._columns(model)}
        if "instance_id" not in columns:
            raise ScopeError(f"{model.__name__} has no instance_id scope")
        return columns

    def select(self, model, *criteria):
        columns = self._scope_columns(model)
        predicates = [columns["instance_id"] == self.instance_id]
        if self.team_id is not None and "team_id" in columns:
            predicates.append(columns["team_id"] == self.team_id)
        predicates.extend(criteria)
        return select(model).where(*predicates)

    def get(self, model, identity):
        columns = self._scope_columns(model)
        mapper = inspect(model).mapper
        if not isinstance(identity, tuple):
            identity = (identity,)
        pk_names = [column.key for column in mapper.primary_key]
        if pk_names and pk_names[0] == "instance_id" and identity:
            if identity[0] != self.instance_id:
                raise ScopeError("identity instance_id differs from repository scope")
        statement = self.select(model)
        if len(identity) != len(pk_names):
            raise ScopeError(f"invalid identity for {model.__name__}")
        for name, value in zip(pk_names, identity):
            statement = statement.where(getattr(model, name) == value)
        return self.session.execute(statement).scalar_one_or_none()

    def add(self, row):
        instance_id = getattr(row, "instance_id", None)
        if instance_id != self.instance_id:
            raise ScopeError("row instance_id differs from repository scope")
        if self.team_id is not None and hasattr(row, "team_id") and row.team_id != self.team_id:
            raise ScopeError("row team_id differs from repository scope")
        self.session.add(row)
        return row
