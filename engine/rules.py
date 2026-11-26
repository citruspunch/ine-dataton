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
PERIOD_RE = re.compile(r"^(\d{4})(?:-(\d{2}))?$")

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


def parse_period(value: str) -> tuple[int, int | None]:
    match = PERIOD_RE.match(str(value).strip())
    if not match:
        raise ValueError(f"periodo inválido: {value!r}; se espera AAAA o AAAA-MM")
    year = int(match.group(1))
    month = int(match.group(2)) if match.group(2) else None
    if month is not None and not 1 <= month <= 12:
        raise ValueError(f"mes inválido en {value!r}")
    return year, month


def month_range(start: str, end: str) -> list[str]:
    y0, m0 = parse_period(start)
    y1, m1 = parse_period(end)
    if m0 is None or m1 is None:
        raise ValueError("un rango mensual exige periodos AAAA-MM")
    out = []
    year, month = y0, m0
    while (year, month) <= (y1, m1):
        out.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return out


def year_range(start: str, end: str) -> list[str]:
    y0, _ = parse_period(start)
    y1, _ = parse_period(end)
    return [f"{year:04d}" for year in range(y0, y1 + 1)]


def declared_periods(profile: dict[str, Any]) -> list[str]:
    dates = profile.get("dates") or {}
    if dates.get("expected"):
        return [str(p) for p in dates["expected"]]
    window = dates.get("range")
    if window:
        if dates.get("month"):
            return month_range(window["from"], window["to"])
        return year_range(window["from"], window["to"])
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
    if year_field in values:
        for row_number in table.row_numbers:
            year = values[year_field].get(row_number)
            if not isinstance(year, int):
                continue
            if month_field:
                month = values.get(month_field, {}).get(row_number)
                if not isinstance(month, int):
                    continue
                text = f"{year:04d}-{month:02d}"
            else:
                text = f"{year:04d}"
            period_of_row[row_number] = text
            row_of_period.setdefault(text, row_number)

    return Parsed(table, values, period_of_row, row_of_period)


def build_variables_summary(parsed: Parsed, profile: dict[str, Any]) -> dict[str, Any]:
    """Summarize declared columns without exposing individual observations.

    A missing header has unknown counts, not zero counts. Blank values are
    counted separately from nonblank values that could not be parsed.
    """
    table = parsed.table
    columns = []
    for entry in profile["schema"]:
        index = _field_index(table, entry)
        valid = null = excluded = None
        if index is not None:
            valid = null = excluded = 0
            values = parsed.values[entry["name"]]
            for row in table.row_numbers:
                if _is_blank(table.cell(row, index)):
                    null += 1
                elif row in values and values[row] is not None:
                    valid += 1
                else:
                    excluded += 1
        columns.append(
            {
                "name": entry["name"],
                "column": entry["column"],
                "type": entry["type"],
                "unit": entry.get("unit"),
                "reference": entry.get("reference"),
                "nullable": bool(entry.get("nullable", False)),
                "notes": entry.get("notes"),
                "present": index is not None,
                "valid_count": valid,
                "null_count": null,
                "excluded_count": excluded,
            }
        )
    display = profile.get("display") or {}
    return {
        "row_count": len(table.row_numbers),
        "columns": columns,
        "coverage": {
            "period": display.get("period"),
            "notes": profile.get("summary_notes"),
        },
    }


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

    # CONT-06 variables, units and reference scopes
    summary = build_variables_summary(parsed, profile)
    findings.append(
        _finding(
            meta,
            "CONT-06",
            OK,
            "Las variables declaradas, sus tipos, unidades y referencias están resumidos.",
            {
                "row_count": summary["row_count"],
                "variables": [
                    {
                        "name": column["name"],
                        "column": column["column"],
                        "type": column["type"],
                        "unit": column["unit"],
                        "reference": column["reference"],
                        "nullable": column["nullable"],
                        "valid_count": column["valid_count"],
                        "null_count": column["null_count"],
                        "excluded_count": column["excluded_count"],
                    }
                    for column in summary["columns"]
                ],
                "coverage": summary["coverage"],
            },
        )
    )

    return findings


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
    files: dict[str, str] = {}
    variables_summary: dict[str, Any] | None = None
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
                        "Bytes y SHA-256 coinciden con el manifiesto del corte.",
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
            variables_summary = build_variables_summary(parsed, profile)
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
            "variables_summary": variables_summary,
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
