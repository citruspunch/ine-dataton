"""Rule engine of the prototype.

Rules are resolved by semantic schema: columns by header, periods by year and
month. No profile declares rows or column letters; the cells that appear in the
evidence are discovered while reading the file and are only informational
metadata.

The engine does not correct, does not fill in and does not decide: it emits
state, severity, coverage and evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from . import config, profiles
from .canonical import digest, file_sha256
from .model import (
    FAILURE,
    NOT_EVALUATED,
    OK,
    WARNING,
    Comparison,
    Finding,
    ValidationResult,
    derive_state,
    summarize_coverage,
)
from .reader import (
    ReadError,
    Table,
    UnexpectedSheet,
    coerce,
    coerce_month,
    read_table,
)

MAX_EVIDENCE_ITEMS = 8
PERIOD_RE = re.compile(r"^(\d{4})-(\d{2})$")

ALL_CONTRACT_RULES = ["CONT-02", "CONT-03", "CONT-04", "CONT-05", "CONT-06"]


# --------------------------------------------------------------------------
# Subject: what is evaluated (a closed-list case or an uploaded file)
# --------------------------------------------------------------------------


@dataclass
class Subject:
    case_id: str
    label: str
    method: str
    profile_id: str
    items: list[dict[str, Any]]
    requested_comparisons: list[str] = field(default_factory=list)
    resources: list[dict[str, Any]] = field(default_factory=list)
    origin: str = "case"


def resolve_subject(subject_id: str) -> Subject:
    from . import store

    upload = store.get_upload(subject_id)
    if upload:
        return Subject(
            case_id=upload["id"],
            label=upload["label"],
            method="contract",
            profile_id=upload["profile_id"],
            items=[upload["item"]],
            origin="upload",
        )

    case = config.load_case(subject_id)
    items = []
    if case.get("manifest_item"):
        items = [config.manifest_item(case["manifest_item"])]
    return Subject(
        case_id=case["id"],
        label=case["label"],
        method=case["method"],
        profile_id=case["profile"],
        items=items,
        requested_comparisons=list(case.get("requested_comparisons") or []),
        resources=list(case.get("resources") or []),
        origin="case",
    )


# --------------------------------------------------------------------------
# Typed reading
# --------------------------------------------------------------------------


@dataclass
class Parsed:
    table: Table
    values: dict[str, dict[int, Any]]
    period_of_row: dict[int, str]
    row_of_period: dict[str, int]


def parse_period(value: str) -> tuple[int, int]:
    match = PERIOD_RE.match(str(value).strip())
    if not match:
        raise ValueError(f"periodo inválido: {value!r}; se espera AAAA-MM")
    year, month = int(match.group(1)), int(match.group(2))
    if not 1 <= month <= 12:
        raise ValueError(f"mes inválido en {value!r}")
    return year, month


def month_range(start: str, end: str) -> list[str]:
    y0, m0 = parse_period(start)
    y1, m1 = parse_period(end)
    out = []
    year, month = y0, m0
    while (year, month) <= (y1, m1):
        out.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return out


def declared_periods(profile: dict[str, Any]) -> list[str]:
    dates = profile.get("dates") or {}
    if dates.get("expected"):
        return [str(p) for p in dates["expected"]]
    window = dates.get("range")
    if window:
        return month_range(window["from"], window["to"])
    return []


def _cell_ref(table: Table, row: int, index: int | None) -> dict[str, Any]:
    """Informational metadata: the cell is discovered, never declared."""
    ref: dict[str, Any] = {"row": row}
    if index is not None and table.sheet is not None:
        ref["cell"] = f"{table.letter(index)}{row}"
        ref["sheet"] = table.sheet
    return ref


def _field_index(table: Table, entry: dict[str, Any]) -> int | None:
    return table.column_index(entry["column"])


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _convert(
    entry: dict[str, Any],
    raw: Any,
    month_field: str,
    month_format: str,
) -> Any:
    if entry["name"] == month_field:
        return coerce_month(raw, month_format)
    return coerce(raw, entry["type"])


def parse_table(table: Table, profile: dict[str, Any]) -> Parsed:
    schema = profile["schema"]
    dates = profile.get("dates") or {}
    month_field = dates.get("month", "")
    month_format = dates.get("month_format", "name_es")

    values: dict[str, dict[int, Any]] = {e["name"]: {} for e in schema}
    for entry in schema:
        index = _field_index(table, entry)
        if index is None:
            continue
        for row_number in table.row_numbers:
            raw = table.cell(row_number, index)
            if _is_blank(raw) and entry.get("nullable"):
                values[entry["name"]][row_number] = None
                continue
            try:
                values[entry["name"]][row_number] = _convert(
                    entry, raw, month_field, month_format
                )
            except ValueError:
                continue

    period_of_row: dict[int, str] = {}
    row_of_period: dict[str, int] = {}
    year_field = dates.get("year", "year")
    if year_field in values and month_field in values:
        for row_number in table.row_numbers:
            year = values[year_field].get(row_number)
            month = values[month_field].get(row_number)
            if not isinstance(year, int) or not isinstance(month, int):
                continue
            text = f"{year:04d}-{month:02d}"
            period_of_row[row_number] = text
            row_of_period.setdefault(text, row_number)

    return Parsed(table, values, period_of_row, row_of_period)


def _finding(
    meta: dict[str, dict[str, Any]],
    rule_id: str,
    status: str,
    message: str,
    evidence: dict[str, Any] | None = None,
    justified: bool = False,
) -> Finding:
    spec = meta[rule_id]
    return Finding(
        rule_id=rule_id,
        title=spec["title"],
        status=status,
        critical=bool(spec["critical"]),
        message=message,
        evidence=evidence or {},
        justified=justified,
    )


def _not_evaluated(
    meta: dict[str, dict[str, Any]], rule_ids: list[str], reason: str
) -> list[Finding]:
    return [
        _finding(meta, rid, NOT_EVALUATED, f"No evaluado: {reason}.")
        for rid in rule_ids
    ]


# --------------------------------------------------------------------------
# P0.1 contract
# --------------------------------------------------------------------------


def _eval_contract(
    parsed: Parsed, profile: dict[str, Any], meta: dict[str, dict[str, Any]]
) -> list[Finding]:
    table = parsed.table
    findings: list[Finding] = []
    schema = profile["schema"]
    dates = profile.get("dates") or {}
    month_field = dates.get("month", "")
    month_format = dates.get("month_format", "name_es")

    missing = [e["column"] for e in schema if _field_index(table, e) is None]
    if missing:
        findings.append(
            _finding(
                meta,
                "CONT-02",
                FAILURE,
                f"Faltan {len(missing)} columna(s) declaradas en el perfil.",
                {
                    "missing_columns": missing,
                    "observed_header": table.header,
                    "expected_header": [e["column"] for e in schema],
                    "header_row": table.header_row,
                },
            )
        )
        return findings + _not_evaluated(
            meta, ["CONT-03", "CONT-04", "CONT-05", "CONT-06"], "faltan columnas"
        )

    findings.append(
        _finding(
            meta,
            "CONT-02",
            OK,
            "Todas las columnas declaradas están presentes con su encabezado.",
            {
                "columns": [
                    {
                        "column": e["column"],
                        "cell_column": table.letter(_field_index(table, e) or 0),
                    }
                    for e in schema
                ],
                "header_row": table.header_row,
            },
        )
    )

    # CONT-03 types
    errors: list[dict[str, Any]] = []
    for entry in schema:
        index = _field_index(table, entry)
        for row_number in table.row_numbers:
            raw = table.cell(row_number, index)
            if _is_blank(raw) and entry.get("nullable"):
                continue
            try:
                _convert(entry, raw, month_field, month_format)
            except ValueError as exc:
                if len(errors) < MAX_EVIDENCE_ITEMS:
                    errors.append(
                        {
                            "column": entry["column"],
                            "type": entry["type"],
                            "value": None if raw is None else str(raw),
                            "error": str(exc),
                            **_cell_ref(table, row_number, index),
                        }
                    )
    if errors:
        findings.append(
            _finding(
                meta,
                "CONT-03",
                FAILURE,
                "Hay valores que no parsean al tipo declarado.",
                {"errors": errors},
            )
        )
        return findings + _not_evaluated(
            meta, ["CONT-04", "CONT-05", "CONT-06"], "tipos no parseables"
        )

    findings.append(
        _finding(
            meta,
            "CONT-03",
            OK,
            f"Los {len(schema)} campos declarados parsean a su tipo.",
            {"rows_checked": len(table.rows)},
        )
    )

    # CONT-04 grain
    grain = profile["grain"]
    seen: dict[tuple[Any, ...], list[int]] = {}
    for row_number in table.row_numbers:
        combo = tuple(parsed.values[name].get(row_number) for name in grain)
        if all(value is None for value in combo):
            continue
        seen.setdefault(combo, []).append(row_number)
    duplicates = [
        {"grain": list(combo), "rows": rows}
        for combo, rows in seen.items()
        if len(rows) > 1
    ]
    if duplicates:
        findings.append(
            _finding(
                meta,
                "CONT-04",
                FAILURE,
                f"El grano declarado se repite en {len(duplicates)} combinación(es).",
                {"grain": grain, "duplicates": duplicates[:MAX_EVIDENCE_ITEMS]},
            )
        )
    else:
        findings.append(
            _finding(
                meta,
                "CONT-04",
                OK,
                "El grano declarado es único en todas las filas.",
                {"grain": grain, "rows": len(table.rows)},
            )
        )

    # CONT-05 periods
    expected = declared_periods(profile)
    if not expected:
        findings.append(
            _finding(meta, "CONT-05", NOT_EVALUATED, "El perfil no declara periodo.")
        )
    else:
        invalid_dates = []
        for text in expected:
            try:
                parse_period(text)
            except ValueError:
                invalid_dates.append(text)
        missing_periods = [p for p in expected if p not in parsed.row_of_period]
        if invalid_dates:
            findings.append(
                _finding(
                    meta,
                    "CONT-05",
                    FAILURE,
                    "El perfil declara periodos con formato inválido.",
                    {"invalid_periods": invalid_dates},
                )
            )
        elif missing_periods:
            findings.append(
                _finding(
                    meta,
                    "CONT-05",
                    FAILURE,
                    "El periodo declarado no está presente en el archivo.",
                    {
                        "missing_periods": missing_periods[:MAX_EVIDENCE_ITEMS],
                        "observed_first": min(parsed.row_of_period)
                        if parsed.row_of_period
                        else None,
                        "observed_last": max(parsed.row_of_period)
                        if parsed.row_of_period
                        else None,
                    },
                )
            )
        else:
            findings.append(
                _finding(
                    meta,
                    "CONT-05",
                    OK,
                    "Los periodos declarados están presentes y son válidos.",
                    {
                        "declared_periods": len(expected),
                        "first": expected[0],
                        "last": expected[-1],
                        "mode": "rango" if dates.get("range") else "lista",
                    },
                )
            )

    # CONT-06 unit and base
    block = profile.get("comparability") or {}
    unit = block.get("unit")
    series = block.get("series") or []
    bases = {s["index"]: s.get("base") for s in series if s.get("base")}
    unit_field = block.get("unit_field")
    unit_issues: list[dict[str, Any]] = []
    if unit_field and unit and unit_field in parsed.values:
        entry = next(e for e in schema if e["name"] == unit_field)
        index = _field_index(table, entry)
        for row_number in table.row_numbers:
            raw = table.cell(row_number, index)
            observed = "" if raw is None else str(raw).strip()
            if observed != unit and len(unit_issues) < MAX_EVIDENCE_ITEMS:
                unit_issues.append(
                    {"observed": observed, **_cell_ref(table, row_number, index)}
                )
    if unit_issues:
        findings.append(
            _finding(
                meta,
                "CONT-06",
                FAILURE,
                "La unidad observada no coincide con la declarada.",
                {"declared_unit": unit, "issues": unit_issues},
            )
        )
    elif not unit or not bases:
        findings.append(
            _finding(
                meta,
                "CONT-06",
                NOT_EVALUATED,
                "El perfil no declara unidad o base.",
                {"declared_unit": unit, "declared_bases": bases},
            )
        )
    else:
        findings.append(
            _finding(
                meta,
                "CONT-06",
                OK,
                "Unidad y base coinciden con lo declarado en el perfil.",
                {"declared_unit": unit, "declared_bases": bases},
            )
        )

    return findings


# --------------------------------------------------------------------------
# P0.3 comparability
# --------------------------------------------------------------------------


def _base_of(profile: dict[str, Any], field_name: str) -> str | None:
    for series in (profile.get("comparability") or {}).get("series") or []:
        if series.get("index") == field_name:
            return series.get("base")
    return None


def _column_of(profile: dict[str, Any], field_name: str) -> dict[str, Any]:
    for entry in profile["schema"]:
        if entry["name"] == field_name:
            return entry
    raise config.ConfigError(f"el perfil no declara el campo {field_name}")


def _resolve_point(parsed: Parsed, ref: dict[str, Any]) -> tuple[int, Any] | None:
    row = parsed.row_of_period.get(str(ref.get("period")))
    if row is None:
        return None
    value = parsed.values.get(ref.get("field"), {}).get(row)
    if value is None:
        return None
    return row, value


def _eval_comparisons(
    parsed: Parsed, profile: dict[str, Any], requested: list[str]
) -> list[Comparison]:
    block = profile.get("comparability") or {}
    specs = {c["id"]: c for c in block.get("checks") or []}
    results: list[Comparison] = []

    for comparison_id in requested:
        spec = specs.get(comparison_id)
        if spec is None:
            results.append(
                Comparison(
                    comparison_id=comparison_id,
                    label=comparison_id,
                    status="bloqueada",
                    reason="La comparación solicitada no está declarada en el perfil.",
                )
            )
            continue

        num_field = spec["numerator"]["field"]
        den_field = spec["denominator"]["field"]
        num_entry = _column_of(profile, num_field)
        den_entry = _column_of(profile, den_field)
        num = _resolve_point(parsed, spec["numerator"])
        den = _resolve_point(parsed, spec["denominator"])

        evidence: dict[str, Any] = {
            "numerator_column": num_entry["column"],
            "denominator_column": den_entry["column"],
            "numerator_base": _base_of(profile, num_field),
            "denominator_base": _base_of(profile, den_field),
            "numerator_period": spec["numerator"]["period"],
            "denominator_period": spec["denominator"]["period"],
            "unit": spec.get("unit") or block.get("unit"),
        }
        if num:
            evidence["numerator_cell"] = _cell_ref(
                parsed.table, num[0], _field_index(parsed.table, num_entry)
            ).get("cell")
        if den:
            evidence["denominator_cell"] = _cell_ref(
                parsed.table, den[0], _field_index(parsed.table, den_entry)
            ).get("cell")

        if num is None or den is None:
            results.append(
                Comparison(
                    comparison_id=comparison_id,
                    label=spec["label"],
                    status="bloqueada",
                    reason="El periodo o la columna no están disponibles en el archivo.",
                    public_evidence=evidence,
                    rules=["IPC-01"],
                )
            )
            continue

        num_row, num_value = num
        den_row, den_value = den

        if _base_of(profile, num_field) != _base_of(profile, den_field):
            raw = (num_value / den_value - 1.0) * 100.0
            results.append(
                Comparison(
                    comparison_id=comparison_id,
                    label=spec["label"],
                    status="bloqueada",
                    reason=(
                        "Bases distintas: el cociente entre índices de bases distintas "
                        "no es una variación y no se puede comparar directamente."
                    ),
                    public_evidence=evidence,
                    private_evidence={
                        "computed_pct": raw,
                        "computed_pct_rounded": round(raw, 4),
                        "display_public": False,
                        "note": (
                            "Se calculó solo para la pantalla de revisión. El número no "
                            "se copia al snapshot público, ni al export, ni a la ficha."
                        ),
                    },
                    rules=["IPC-01"],
                )
            )
            continue

        den_period = parse_period(str(spec["denominator"]["period"]))
        num_period = parse_period(str(spec["numerator"]["period"]))
        gap = (num_period[0] - den_period[0]) * 12 + (num_period[1] - den_period[1])
        if gap != 1:
            results.append(
                Comparison(
                    comparison_id=comparison_id,
                    label=spec["label"],
                    status="bloqueada",
                    reason=(
                        "Los periodos solicitados no son contiguos; la variación "
                        "mensual exige meses consecutivos."
                    ),
                    public_evidence={**evidence, "months_between": gap},
                    rules=["IPC-02"],
                )
            )
            continue

        computed = (num_value / den_value - 1.0) * 100.0
        submitted: dict[str, Any] = {
            **evidence,
            "period": str(spec["numerator"]["period"]),
            "computed_pct": round(computed, 6),
        }

        published_spec = spec.get("published")
        if published_spec:
            published = _resolve_point(parsed, published_spec)
            pub_entry = _column_of(profile, published_spec["field"])
            cell = None
            if published:
                cell = _cell_ref(
                    parsed.table, published[0], _field_index(parsed.table, pub_entry)
                ).get("cell")
            submitted["published_cell"] = cell
            submitted["published_pct"] = (
                None if published is None else round(float(published[1]), 6)
            )
            if published is None:
                results.append(
                    Comparison(
                        comparison_id=comparison_id,
                        label=spec["label"],
                        status="bloqueada",
                        reason="La variación publicada no está disponible.",
                        public_evidence=submitted,
                        rules=["IPC-03"],
                    )
                )
                continue
            tolerance = float(spec.get("tolerance_pp", 0.005))
            delta = abs(computed - float(published[1]))
            if delta > tolerance:
                results.append(
                    Comparison(
                        comparison_id=comparison_id,
                        label=spec["label"],
                        status="bloqueada",
                        reason="La variación calculada no coincide con la publicada.",
                        public_evidence={**submitted, "delta_pp": round(delta, 6)},
                        rules=["IPC-03"],
                    )
                )
                continue

        results.append(
            Comparison(
                comparison_id=comparison_id,
                label=spec["label"],
                status="ok",
                reason="Misma base, periodos contiguos y variación publicada.",
                public_evidence=submitted,
                rules=["IPC-01", "IPC-02", "IPC-03"]
                if published_spec
                else ["IPC-01", "IPC-02"],
            )
        )
    return results


# --------------------------------------------------------------------------
# Publishable series
# --------------------------------------------------------------------------


def build_series(parsed: Parsed, profile: dict[str, Any]) -> list[dict[str, Any]]:
    table = parsed.table
    block = profile.get("comparability") or {}
    out: list[dict[str, Any]] = []
    for spec in block.get("series") or []:
        field_name = spec["index"]
        if field_name not in parsed.values:
            continue
        entry = _column_of(profile, field_name)
        index = _field_index(table, entry)
        variation_field = spec.get("variation")
        var_entry = _column_of(profile, variation_field) if variation_field else None
        var_index = _field_index(table, var_entry) if var_entry else None

        points = []
        for period in declared_periods(profile):
            row = parsed.row_of_period.get(period)
            if row is None:
                continue
            value = parsed.values[field_name].get(row)
            if value is None:
                continue
            point: dict[str, Any] = {
                "period": period,
                "value": value,
                "cell": _cell_ref(table, row, index).get("cell"),
            }
            if var_entry is not None:
                variation = parsed.values.get(variation_field, {}).get(row)
                point["published_variation_pct"] = variation
                point["variation_cell"] = _cell_ref(table, row, var_index).get("cell")
            points.append(point)

        out.append(
            {
                "series_id": spec["id"],
                "label": spec.get("label", spec["id"]),
                "base": spec.get("base"),
                "unit": block.get("unit"),
                "comparable": bool(spec.get("comparable", True)),
                "not_comparable_reason": spec.get("reason"),
                "has_published_variation": var_entry is not None,
                "points": points,
            }
        )
    return out


# --------------------------------------------------------------------------
# P0.2 identity
# --------------------------------------------------------------------------


def _eval_identity(
    subject: Subject, meta: dict[str, dict[str, Any]]
) -> tuple[list[Finding], dict[str, Any], dict[str, str]]:
    findings: list[Finding] = []
    evidence: dict[str, Any] = {"resources": []}
    files: dict[str, str] = {}

    for resource in subject.resources:
        item = config.manifest_item(resource["manifest_item"])
        path = config.ROOT / item["path"]
        if not path.exists():
            findings.append(
                _finding(meta, "ID-01", NOT_EVALUATED, "Archivo de identidad ausente.")
            )
            return findings, evidence, files
        actual = file_sha256(path)
        files[item["id"]] = actual
        evidence["resources"].append(
            {
                "manifest_item": item["id"],
                "path": item["path"],
                "sha256": actual,
                "declared_sha256": item.get("sha256"),
                "identity": resource["identity"],
            }
        )

    a, b = evidence["resources"][0], evidence["resources"][1]
    same_bytes = a["sha256"] == b["sha256"]
    evidence["same_bytes"] = same_bytes
    evidence["sha256"] = a["sha256"]

    if not same_bytes:
        findings.append(
            _finding(
                meta,
                "ID-01",
                OK,
                "Los dos recursos tienen bytes distintos; no hay conflicto de identidad.",
                {"sha256": [a["sha256"], b["sha256"]]},
            )
        )
        return findings, evidence, files

    mismatched = [
        key
        for key in ("dataset", "title", "period", "base", "unit", "grain")
        if a["identity"].get(key) != b["identity"].get(key)
    ]
    evidence["mismatched_fields"] = mismatched

    if not mismatched:
        findings.append(
            _finding(
                meta,
                "ID-01",
                OK,
                "Mismos bytes e identidad semántica compatible.",
                {"sha256": a["sha256"], "identity": a["identity"]},
            )
        )
        return findings, evidence, files

    policy = config.justification_for(subject.case_id, "ID-01")
    if policy:
        findings.append(
            _finding(
                meta,
                "ID-01",
                WARNING,
                "Mismos bytes con identidad distinta, cubierto por una política "
                "de reutilización documentada.",
                {
                    "sha256": a["sha256"],
                    "mismatched_fields": mismatched,
                    "identities": [a["identity"], b["identity"]],
                    "policy": policy,
                },
                justified=True,
            )
        )
    else:
        findings.append(
            _finding(
                meta,
                "ID-01",
                FAILURE,
                "Mismos bytes con identidad semántica incompatible: requiere revisión.",
                {
                    "sha256": a["sha256"],
                    "mismatched_fields": mismatched,
                    "identities": [a["identity"], b["identity"]],
                },
            )
        )
    return findings, evidence, files


# --------------------------------------------------------------------------
# Digest and orchestration
# --------------------------------------------------------------------------


def _basis_digest(
    files: dict[str, str],
    profile: dict[str, Any],
    rules_doc: dict[str, Any],
    findings: list[Finding],
) -> str:
    """No timestamps: data, contract, profile, rules and findings."""
    clean = {k: v for k, v in profile.items() if not k.startswith("_")}
    return digest(
        {
            "files": files,
            "profile": {
                "id": clean["profile_id"],
                "version": str(clean["version"]),
                "content_sha256": digest(clean),
            },
            "rules": {
                "version": rules_doc["rules_version"],
                "content_sha256": digest(rules_doc),
            },
            "findings": [
                {
                    "rule_id": f.rule_id,
                    "status": f.status,
                    "critical": f.critical,
                    "evidence": f.evidence,
                }
                for f in findings
            ],
        }
    )


def validate(subject_id: str, write_receipt: bool = True) -> ValidationResult:
    subject = resolve_subject(subject_id)
    return validate_subject(subject, write_receipt=write_receipt)


def validate_subject(subject: Subject, write_receipt: bool = True) -> ValidationResult:
    profile = profiles.load_profile(subject.profile_id, case_id=subject.case_id)
    rules_doc = config.load_rules()
    meta = config.rule_meta(rules_doc)

    findings: list[Finding] = []
    comparisons: list[Comparison] = []
    files: dict[str, str] = {}
    series: list[dict[str, Any]] = []
    entity: dict[str, Any] = {}
    license_verified = False

    if subject.method == "identity_pair":
        findings, identity_evidence, files = _eval_identity(subject, meta)
        primary_item = config.manifest_item(subject.resources[0]["manifest_item"])
        entity = {
            "kind": "par de recursos",
            "label": subject.label,
            "resources": [
                {"manifest_item": r["manifest_item"], "identity": r["identity"]}
                for r in subject.resources
            ],
            "same_bytes": identity_evidence.get("same_bytes"),
            "sha256": identity_evidence.get("sha256"),
            "profile": f"{profile['profile_id']}@{profile['version']}",
            "license": primary_item.get("license", {}),
            "topic": profile.get("topic"),
            "display": profile.get("display", {}),
        }
        license_verified = all(
            bool(
                config.manifest_item(r["manifest_item"])
                .get("license", {})
                .get("verified")
            )
            for r in subject.resources
        )
    else:
        item = subject.items[0]
        path = config.ROOT / item["path"]
        display = profile.get("display", {})

        # SNAP-01 integrity
        if not path.exists():
            findings.append(
                _finding(
                    meta,
                    "SNAP-01",
                    FAILURE,
                    "El archivo declarado no existe.",
                    {"path": item["path"]},
                )
            )
            actual_sha = None
        else:
            actual_sha = file_sha256(path)
            files = {item["id"]: actual_sha}
            size = path.stat().st_size
            if actual_sha == item.get("sha256") and size == item.get("bytes"):
                findings.append(
                    _finding(
                        meta,
                        "SNAP-01",
                        OK,
                        "Bytes y SHA-256 coinciden con el manifiesto del snapshot.",
                        {
                            "sha256": actual_sha,
                            "bytes": size,
                            "manifest_item": item["id"],
                            "origin": item.get("origin", "snapshot"),
                        },
                    )
                )
            else:
                findings.append(
                    _finding(
                        meta,
                        "SNAP-01",
                        FAILURE,
                        "El archivo no coincide con los bytes o el hash registrados.",
                        {
                            "expected_sha256": item.get("sha256"),
                            "observed_sha256": actual_sha,
                            "expected_bytes": item.get("bytes"),
                            "observed_bytes": size,
                        },
                    )
                )

        # LIC-01 license
        license_info = item.get("license", {})
        if license_info.get("verified"):
            findings.append(
                _finding(
                    meta,
                    "LIC-01",
                    OK,
                    "Licencia verificada.",
                    {
                        "id": license_info.get("id"),
                        "attribution": license_info.get("attribution"),
                        "evidence": license_info.get("evidence"),
                    },
                )
            )
        else:
            findings.append(
                _finding(
                    meta,
                    "LIC-01",
                    FAILURE,
                    "Sin licencia verificada: el recurso se cierra por defecto.",
                    {
                        "id": license_info.get("id"),
                        "evidence": license_info.get("evidence"),
                    },
                )
            )
        license_verified = bool(license_info.get("verified"))

        table: Table | None = None
        parsed: Parsed | None = None
        read_failure: str | None = None
        is_workbook = profile["kind"] == "xlsx"

        try:
            table = read_table(
                path,
                profile["kind"],
                profile.get("expected_sheet"),
                int(profile.get("header_row") or 1),
            )
        except UnexpectedSheet as exc:
            findings.append(
                _finding(
                    meta,
                    "CONT-01",
                    FAILURE,
                    "La hoja observada no es la declarada en el perfil.",
                    {
                        "expected_sheet": exc.expected,
                        "observed_sheets": exc.observed,
                    },
                )
            )
            read_failure = "hoja inesperada"
        except ReadError as exc:
            read_failure = "archivo ilegible"
            if is_workbook:
                findings.append(
                    _finding(
                        meta,
                        "CONT-01",
                        NOT_EVALUATED,
                        f"Archivo ilegible: {exc}.",
                        {"path": item["path"]},
                    )
                )

        if table is not None and is_workbook:
            if table.sheet is None:
                findings.append(
                    _finding(
                        meta,
                        "CONT-01",
                        FAILURE,
                        "El perfil espera un libro con hojas y el archivo no tiene hojas.",
                        {
                            "expected_sheet": profile.get("expected_sheet"),
                            "observed_sheets": [],
                            "observed_format": item["path"].rsplit(".", 1)[-1],
                        },
                    )
                )
            else:
                findings.append(
                    _finding(
                        meta,
                        "CONT-01",
                        OK,
                        "La hoja declarada está presente.",
                        {
                            "expected_sheet": profile.get("expected_sheet"),
                            "observed_sheets": [table.sheet],
                            "header_row": table.header_row,
                        },
                    )
                )

        if read_failure is None and table is not None:
            parsed = parse_table(table, profile)
            findings.extend(_eval_contract(parsed, profile, meta))
            series = build_series(parsed, profile)
            if subject.requested_comparisons:
                comparisons = _eval_comparisons(
                    parsed, profile, subject.requested_comparisons
                )
        else:
            findings.extend(
                _not_evaluated(
                    meta, ALL_CONTRACT_RULES, read_failure or "lectura fallida"
                )
            )

        entity = {
            "kind": "agregado",
            "manifest_item": item["id"],
            "dataset_id": item.get("dataset_id"),
            "resource_id": item.get("resource_id"),
            "title": item.get("title"),
            "source_url": item.get("source_url"),
            "downloaded_at_utc": item.get("downloaded_at_utc"),
            "sha256": item.get("sha256"),
            "bytes": item.get("bytes"),
            "origin": item.get("origin", "snapshot"),
            "topic": profile.get("topic"),
            "profile": f"{profile['profile_id']}@{profile['version']}",
            "license": license_info,
            "display": display,
            "series": series,
        }

    for finding in findings:
        if finding.status == WARNING and not finding.justified:
            record = config.justification_for(subject.case_id, finding.rule_id)
            if record:
                finding.justified = True
                finding.evidence.setdefault("justification", record)

    warnings_justified = all(f.justified for f in findings if f.status == WARNING)
    result = ValidationResult(
        case_id=subject.case_id,
        label=subject.label,
        method=subject.method,
        entity=entity,
        findings=findings,
        comparisons=comparisons,
        warnings_justified=warnings_justified,
    )
    result.coverage = summarize_coverage(findings)

    basis = _basis_digest(files, profile, rules_doc, findings)
    result.digests = {
        "validation_digest": basis,
        "decision_basis_digest": basis,
        "profile_digest": digest(
            {"id": profile["profile_id"], "v": profile["version"]}
        ),
        "rules_digest": digest(rules_doc),
    }

    decision = config.latest_decision(subject.case_id)
    gate_approved = bool(
        decision
        and decision.get("gate_decision") in ("habilitado", "aprobar_con_excepcion")
        and decision.get("decision_basis_digest") == basis
    )
    result.state = derive_state(
        findings, license_verified, gate_approved, warnings_justified
    )

    if write_receipt:
        from .gate import write_receipt

        write_receipt(result, subject, profile, rules_doc, decision)
    return result
