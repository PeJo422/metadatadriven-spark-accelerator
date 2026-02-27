from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ColumnSpec:
    name: str
    type: str


@dataclass(frozen=True)
class BusinessKeySpec:
    columns: list[str]


@dataclass(frozen=True)
class FilterSpec:
    column: str
    operator: str
    value: Optional[Any] = None


@dataclass(frozen=True)
class JoinOnSpec:
    left_alias: str
    left_column: str
    right_column: str


@dataclass(frozen=True)
class JoinSpec:
    table: str
    type: str
    on: list[JoinOnSpec] = field(default_factory=list)
    alias: Optional[str] = None


@dataclass(frozen=True)
class ModelSpec:
    name: str
    source: str
    target: str
    scd_type: str
    business_key: BusinessKeySpec
    columns: list[ColumnSpec]
    row_hash_columns: list[str] = field(default_factory=list)
    row_filters: list[FilterSpec] = field(default_factory=list)
    joins: list[JoinSpec] = field(default_factory=list)
