"""Quality flags, deduplication and descriptive statistics."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from typing import Any

from .config import GROUP_META, SOURCE_GROUP_ORDER, SourceSpec
from .model import Record
from .parsing import normalize_text


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", normalize_text(value)).strip("-")


def _duplicate_key(record: Record) -> tuple[Any, ...] | None:
    if record.value is None:
        return None
    date_key = record.date or record.date_raw
    if record.source_group == "DPIR":
        return (
            "DPIR",
            record.nog or "",
            normalize_text(record.item),
            normalize_text(record.unit),
            round(record.value, 6),
            date_key,
        )
    if record.source_group == "IPMC":
        return (
            "IPMC",
            normalize_text(record.item),
            normalize_text(record.context),
            date_key,
        )
    if record.source_group == "ICC":
        return (
            "ICC",
            normalize_text(record.item),
            record.level,
            normalize_text(record.context),
            date_key,
        )
    return (
        "BASKETS",
        record.source,
        record.region,
        record.level,
        normalize_text(record.item),
        normalize_text(record.metric),
        date_key,
    )


def _dpir_weak_key(record: Record) -> tuple[Any, ...] | None:
    if record.source_group != "DPIR" or record.value is None:
        return None
    return (
        "DPIR",
        normalize_text(record.item),
        normalize_text(record.unit),
        round(record.value, 6),
        record.date or record.date_raw,
    )


def mark_duplicates(records: Iterable[Record]) -> list[Record]:
    """Mark repeated observations, preferring complete and newer DPIR records.

    A strong key includes the NOG.  When the newer 2023 workbook lost a NOG but
    the 2022 copy has it, a weak key (without NOG) still recognises the repeat:
    the complete record is kept and the incomplete copy is marked duplicate.
    Two records with two different, non-empty NOGs are never collapsed because
    they may be distinct procurement processes.

    Duplicates remain in the output so an auditor can inspect them, but they
    carry ``duplicate`` and ``duplicateOf`` and are excluded from statistics.
    """

    def priority(record: Record) -> tuple[int, int, str]:
        missing_nog = 1 if (record.source_group == "DPIR" and not record.nog) else 0
        if record.dataset == "dpir-2023":
            dataset_priority = 0
        elif record.dataset == "dpir-2022":
            dataset_priority = 1
        else:
            dataset_priority = 2
        return (missing_nog, dataset_priority, record.id)

    ordered = sorted(records, key=priority)
    seen_strong: dict[tuple[Any, ...], str] = {}
    seen_weak: dict[tuple[Any, ...], Record] = {}
    for record in ordered:
        key = _duplicate_key(record)
        if key is None:
            continue
        weak = _dpir_weak_key(record)
        duplicate_of: str | None = None

        if key in seen_strong:
            duplicate_of = seen_strong[key]
        elif weak is not None and weak in seen_weak:
            other = seen_weak[weak]
            if not record.nog or not other.nog:
                duplicate_of = other.id

        if duplicate_of is not None:
            record.add_flag("duplicate")
            record.duplicate_of = duplicate_of
        else:
            seen_strong[key] = record.id

        if weak is not None and weak not in seen_weak:
            seen_weak[weak] = record

    return ordered


def _percentile(sorted_values: list[float], fraction: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * fraction
    low = math.floor(position)
    high = math.ceil(position)
    if low == high:
        return sorted_values[low]
    weight = position - low
    return sorted_values[low] * (1 - weight) + sorted_values[high] * weight


def _group_unit(record: Record) -> str:
    """The unit used to split a metric into comparable bands.

    Prices are split by their presentation (a sack is not a pound), while
    indices and basket costs carry a single metric unit.
    """

    if record.value_kind in {"index", "cost"}:
        return record.metric_unit or record.unit or "Sin unidad"
    return record.unit or record.metric_unit or "Sin unidad"


def _summary_for(items: list[Record]) -> dict[str, Any] | None:
    values = sorted(record.value for record in items if record.value is not None)
    if not values:
        return None
    dates = sorted(record.date for record in items if record.date)
    units = Counter(_group_unit(record) for record in items)
    return {
        "count": len(values),
        "min": values[0],
        "p25": _percentile(values, 0.25),
        "median": _percentile(values, 0.5),
        "p75": _percentile(values, 0.75),
        "max": values[-1],
        "mean": sum(values) / len(values),
        "cutoff": dates[-1] if dates else None,
        "unit": units.most_common(1)[0][0],
    }


def _overall_unit(
    metric: str,
    value_kind: str,
    unit_groups: list[dict[str, Any]],
    metric_unit: str | None,
) -> str:
    if metric == "Precio de referencia":
        return "Q (todas las presentaciones)"
    if metric == "Precio por unidad base":
        return "Q por unidad base (presentaciones distintas)"
    if metric_unit:
        return metric_unit
    if unit_groups:
        return unit_groups[0]["unit"]
    return "—"


def metric_stats(records: Iterable[Record]) -> list[dict[str, Any]]:
    """Stats per metric, with a per-unit breakdown.

    A DPIR price band is only meaningful once the presentation is fixed, so the
    response keeps ``unitGroups`` for the UI's presentation filter.  The
    top-level numbers are still useful as a broad, clearly labelled band.
    """

    groups: dict[str, list[Record]] = defaultdict(list)
    for record in records:
        if "duplicate" in record.flags:
            continue
        if record.value is None or record.date is None:
            continue
        groups[record.metric].append(record)

    output: list[dict[str, Any]] = []
    for metric, items in groups.items():
        overall = _summary_for(items)
        if overall is None:
            continue
        by_unit: dict[str, list[Record]] = defaultdict(list)
        for record in items:
            by_unit[normalize_text(_group_unit(record))].append(record)
        unit_groups: list[dict[str, Any]] = []
        for unit_items in by_unit.values():
            summary = _summary_for(unit_items)
            if summary is None:
                continue
            summary["key"] = normalize_text(summary["unit"])
            unit_groups.append(summary)
        unit_groups.sort(key=lambda item: (-item["count"], item["unit"]))
        output.append(
            {
                "key": _slug(metric),
                "metric": metric,
                "valueKind": items[0].value_kind,
                "currency": items[0].currency,
                **overall,
                "unit": _overall_unit(
                    metric,
                    items[0].value_kind,
                    unit_groups,
                    items[0].metric_unit,
                ),
                "unitGroups": unit_groups,
                "sources": sorted({record.source for record in items}),
                "levels": sorted({record.level for record in items if record.level}),
            }
        )
    output.sort(key=lambda item: (-item["count"], item["metric"]))
    return output


def quality_summary(records: Iterable[Record]) -> dict[str, int]:
    items = list(records)
    flags = Counter(flag for record in items for flag in record.flags)
    canonical = [
        record
        for record in items
        if "duplicate" not in record.flags and record.value is not None and record.date is not None
    ]
    return {
        "totalRecords": len(items),
        "canonicalRecords": len(canonical),
        "excludedFromStats": len(items) - len(canonical),
        "invalidDate": flags.get("invalid_date", 0),
        "missingDate": flags.get("missing_date", 0),
        "duplicates": flags.get("duplicate", 0),
        "thousandsComma": flags.get("thousands_comma", 0),
        "missingNog": flags.get("missing_nog", 0),
        "missingValue": flags.get("missing_value", 0),
        "missingProduct": flags.get("missing_product", 0),
    }


def _top(items: Iterable[str], limit: int = 10) -> list[dict[str, Any]]:
    counts = Counter(item for item in items if item)
    return [{"value": value, "count": count} for value, count in counts.most_common(limit)]


def build_group_summary(group: str, records: list[Record]) -> dict[str, Any]:
    meta = GROUP_META[group]
    items = [record for record in records if record.source_group == group]
    metrics = metric_stats(items)
    quality = quality_summary(items)
    canonical = [record for record in items if "duplicate" not in record.flags]
    dates = sorted(record.date for record in canonical if record.date)
    cutoff = dates[-1] if dates else None
    status_counts = Counter(record.status for record in items)
    status = status_counts.most_common(1)[0][0] if status_counts else "current"

    coverage_notes = {
        "DPIR": (
            "Dos instantáneas congeladas (junio 2022 y agosto 2023). No es una serie mensual "
            "continua. Los registros que aparecen en ambos archivos se deduplican: se conserva "
            "la copia con NOG completo y, en empate, la del archivo 2023; las demás se excluyen "
            "de los resúmenes."
        ),
        "IPMC": (
            "Índice mensual de 89 materiales y servicios, base diciembre 2018 = 100. Cobertura "
            "Región I Metropolitana y municipios seleccionados. No es un precio en quetzales."
        ),
        "ICC": (
            "Índice de costos de la Vivienda Social Básica, 2026 y Región I únicamente. "
            "Período de referencia 2025 = 100. No es un precio de mercado."
        ),
        "BASKETS": (
            "Ventana 2024–2026. El costo per cápita y por grupo es un costo de canasta, no una "
            "cotización de mercado; el precio por producto es implícito y corresponde a la "
            "cantidad base indicada."
        ),
    }

    return {
        "id": group,
        "label": meta["label"],
        "shortLabel": meta["shortLabel"],
        "tagline": meta["tagline"],
        "description": meta["description"],
        "status": status,
        "statusLabel": meta["statusLabel"],
        "cutoff": cutoff,
        "granularity": "day" if group == "DPIR" else "month",
        "recordCount": len(items),
        "canonicalCount": sum(metric["count"] for metric in metrics),
        "flaggedCount": len(items) - sum(metric["count"] for metric in metrics),
        "datasets": sorted({record.dataset for record in items}),
        "metrics": metrics,
        "quality": quality,
        "coverageNote": coverage_notes[group],
        "categories": _top((record.category for record in canonical), limit=12),
        "items": _top((record.item for record in canonical), limit=12),
    }


def build_summary(records: list[Record]) -> dict[str, Any]:
    groups = {group: build_group_summary(group, records) for group in SOURCE_GROUP_ORDER}
    return {
        "groups": groups,
        "totalRecords": len(records),
        "order": list(SOURCE_GROUP_ORDER),
    }


def build_catalog(records: list[Record]) -> dict[str, Any]:
    catalog: dict[str, Any] = {}
    for group in SOURCE_GROUP_ORDER:
        items = [record for record in records if record.source_group == group]
        unique: dict[str, dict[str, Any]] = {}
        for record in items:
            entry = unique.setdefault(
                record.item,
                {
                    "value": record.item,
                    "category": record.category,
                    "metric": record.metric,
                    "count": 0,
                },
            )
            entry["count"] += 1
        ordered = sorted(unique.values(), key=lambda entry: (-entry["count"], entry["value"]))
        catalog[group] = {
            "items": ordered,
            "categories": _top((record.category for record in items), limit=30),
        }
    return catalog


def dataset_counts(records: list[Record]) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for record in records:
        entry = output.setdefault(
            record.dataset,
            {"recordCount": 0, "canonicalCount": 0, "cutoff": None},
        )
        entry["recordCount"] += 1
        # The dataset card must show the true cutoff inside the file, including
        # records that are duplicated by a newer workbook.
        if record.date is not None:
            if entry["cutoff"] is None or record.date > entry["cutoff"]:
                entry["cutoff"] = record.date
        if "duplicate" not in record.flags and record.value is not None and record.date is not None:
            entry["canonicalCount"] += 1
    return output


def build_manifest(
    records: list[Record],
    specs: dict[str, SourceSpec],
    downloads: dict[str, Any],
    dictionary: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = dataset_counts(records)
    datasets: list[dict[str, Any]] = []
    for spec in specs.values():
        acquisition = downloads.get("datasets", {}).get(spec.id, {})
        stat = counts.get(spec.id, {"recordCount": 0, "canonicalCount": 0, "cutoff": None})
        datasets.append(
            {
                "id": spec.id,
                "group": spec.group,
                "title": spec.title,
                "fileName": spec.filename,
                "url": acquisition.get("url"),
                "attemptedUrls": acquisition.get("attemptedUrls", []),
                "sourcePage": spec.source_page,
                "publisher": spec.publisher,
                "downloadedAtUtc": acquisition.get("downloadedAtUtc"),
                "verifiedAtUtc": acquisition.get("verifiedAtUtc"),
                "retrieval": acquisition.get("retrieval"),
                "sha256": acquisition.get("sha256"),
                "bytes": acquisition.get("bytes"),
                "httpStatus": acquisition.get("httpStatus"),
                "contentType": acquisition.get("contentType"),
                "ckanModified": spec.ckan_modified,
                "license": {
                    "id": spec.license_id,
                    "title": spec.license_title,
                    "url": spec.license_url,
                },
                "status": spec.status,
                "coverage": spec.coverage,
                "notes": spec.notes,
                "cutoff": stat["cutoff"],
                "recordCount": stat["recordCount"],
                "canonicalCount": stat["canonicalCount"],
                "isDictionary": spec.dictionary,
            }
        )
    return {
        "datasets": datasets,
        "dictionary": dictionary,
        "groupMeta": GROUP_META,
        "order": list(SOURCE_GROUP_ORDER),
        "privacy": (
            "Salidas agregadas y de observación. No se incluyen nombres de proveedores, "
            "postores ni identificadores de empresas. Los campos de entidad requirente del "
            "DPIR se omiten deliberadamente; no se intenta reidentificar a ninguna persona, "
            "hogar o empresa."
        ),
        "attribution": (
            "Fuente de los datos: Instituto Nacional de Estadística (INE), Guatemala. "
            "Elaboración propia para la Mesa de Precios."
        ),
        "aiDisclosure": (
            "Se utilizaron asistentes de código con IA generativa durante el desarrollo. "
            "Las reglas de limpieza y las cifras se verifican con pruebas automatizadas y "
            "revisión humana; consulte el README."
        ),
    }
