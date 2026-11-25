"""Unified observation record shared by all sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .parsing import normalize_text, truncate


@dataclass
class Record:
    id: str
    source: str
    source_group: str
    dataset: str
    item: str
    category: str
    metric: str
    value_kind: str
    value: float | None
    unit: str | None
    currency: str | None
    date: str | None
    date_raw: str | None
    date_status: str
    year: int | None
    month: int | None
    metric_unit: str | None = None
    region: str | None = None
    level: str | None = None
    context: str | None = None
    nog: str | None = None
    description: str | None = None
    status: str = "current"
    flags: list[str] = field(default_factory=list)
    duplicate_of: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def add_flag(self, flag: str) -> None:
        if flag not in self.flags:
            self.flags.append(flag)

    def search_text(self) -> str:
        parts = [
            self.item,
            self.category,
            self.metric,
            self.unit,
            self.region,
            self.level,
            self.context,
            self.nog,
        ]
        return " ".join(normalize_text(part) for part in parts if part)

    def to_public(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "source": self.source,
            "sourceGroup": self.source_group,
            "dataset": self.dataset,
            "item": self.item,
            "category": self.category,
            "metric": self.metric,
            "unit": self.unit,
            "metricUnit": self.metric_unit,
            "value": self.value,
            "valueKind": self.value_kind,
            "currency": self.currency,
            "date": self.date,
            "dateRaw": self.date_raw,
            "dateStatus": self.date_status,
            "year": self.year,
            "month": self.month,
            "region": self.region,
            "level": self.level,
            "context": self.context,
            "nog": self.nog,
            "description": truncate(self.description, 240),
            "status": self.status,
            "flags": self.flags,
            "s": self.search_text(),
        }
        if self.duplicate_of:
            payload["duplicateOf"] = self.duplicate_of
        for key, value in self.extra.items():
            if value is not None:
                payload[key] = value
        return payload
