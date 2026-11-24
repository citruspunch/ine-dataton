"""Motor de reglas del prototipo.

Cada regla declarada en rules/rules.json tiene un evaluador aquí. El motor no
corrige, no rellena y no decide: emite estado, severidad, cobertura y evidencia.
"""

from __future__ import annotations

import datetime as dt
from typing import Any

from . import config
from .canonical import digest, file_sha256
from .model import (
    ADVERTENCIA,
    FALLA,
    NO_EVALUADO,
    OK,
    Comparison,
    Finding,
    ValidationResult,
    derive_state,
    summarize_coverage,
)
from .reader import ReadError, Table, UnexpectedSheet, coerce, read_table

MAX_EVIDENCE_ITEMS = 8


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
    meta: dict[str, dict[str, Any]],
    rule_ids: list[str],
    reason: str,
) -> list[Finding]:
    return [
        _finding(meta, rid, NO_EVALUADO, f"No evaluado: {reason}.") for rid in rule_ids
    ]


# --------------------------------------------------------------------------
# Contrato de esquema, tipo, grano, fechas, periodo, unidad y base (P0.1)
# --------------------------------------------------------------------------


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")


def _column_index(table: Table, spec: dict[str, Any]) -> int | None:
    """Devuelve el índice del encabezado declarado, verificando la letra."""
    idx = table.column_index(spec["header"])
    if idx is None:
        return None
    letter = spec.get("letter")
    if letter is not None and table.letter_index(letter) != idx:
        return None
    return idx


def _eval_contract(
    table: Table,
    profile: dict[str, Any],
    meta: dict[str, dict[str, Any]],
) -> list[Finding]:
    findings: list[Finding] = []
    columns: list[dict[str, Any]] = profile["columns"]

    # CONT-02 columnas requeridas
    missing = [c["header"] for c in columns if _column_index(table, c) is None]
    if missing:
        findings.append(
            _finding(
                meta,
                "CONT-02",
                FALLA,
                f"Faltan {len(missing)} columna(s) declaradas en el perfil.",
                {
                    "missing_columns": missing,
                    "observed_header": table.header,
                    "expected_header": [c["header"] for c in columns],
                },
            )
        )
        return findings + _not_evaluated(
            meta,
            ["CONT-03", "CONT-04", "CONT-05", "CONT-06"],
            "faltan columnas requeridas",
        )

    findings.append(
        _finding(
            meta,
            "CONT-02",
            OK,
            "Todas las columnas declaradas están presentes en su posición.",
            {"columns": [c["header"] for c in columns]},
        )
    )

    resolved = {
        c["key"]: {"spec": c, "index": _column_index(table, c)} for c in columns
    }

    # CONT-03 tipos
    type_errors: list[dict[str, Any]] = []
    values: dict[str, dict[int, Any]] = {key: {} for key in resolved}
    for key, entry in resolved.items():
        spec = entry["spec"]
        index = entry["index"]
        for row_number in table.row_numbers:
            raw = table.cell(row_number, index)
            if _is_blank(raw) and spec.get("nullable"):
                values[key][row_number] = None
                continue
            try:
                values[key][row_number] = coerce(raw, spec["type"])
            except ValueError as exc:
                if len(type_errors) < MAX_EVIDENCE_ITEMS:
                    type_errors.append(
                        {
                            "row": row_number,
                            "column": spec["header"],
                            "value": None if raw is None else str(raw),
                            "error": str(exc),
                        }
                    )
    if type_errors:
        findings.append(
            _finding(
                meta,
                "CONT-03",
                FALLA,
                "Hay valores que no parsean al tipo declarado.",
                {"errors": type_errors},
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
            f"Los {len(values)} campos declarados parsean a su tipo.",
            {"rows_checked": len(table.rows)},
        )
    )

    # CONT-04 grano único
    grain_keys = profile["grain"]
    seen: dict[tuple[Any, ...], list[int]] = {}
    for row_number in table.row_numbers:
        combo = tuple(values[key][row_number] for key in grain_keys)
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
                FALLA,
                f"El grano declarado se repite en {len(duplicates)} combinación(es).",
                {"grain": grain_keys, "duplicates": duplicates[:MAX_EVIDENCE_ITEMS]},
            )
        )
    else:
        findings.append(
            _finding(
                meta,
                "CONT-04",
                OK,
                "El grano declarado es único en todas las filas.",
                {"grain": grain_keys, "rows": len(table.rows)},
            )
        )

    # CONT-05 periodos esperados
    period = profile.get("period")
    if not period:
        findings.append(
            _finding(
                meta,
                "CONT-05",
                NO_EVALUADO,
                "El perfil no declara periodo; no se puede evaluar.",
                {},
            )
        )
    else:
        year_key = period["year_column"]
        month_key = period["month_column"]
        observed = set(zip(values[year_key].values(), values[month_key].values()))
        missing_periods = [
            {"year": item["year"], "month": item["month"]}
            for item in period["expected"]
            if (item["year"], item["month"]) not in observed
        ]
        if missing_periods:
            findings.append(
                _finding(
                    meta,
                    "CONT-05",
                    FALLA,
                    "El periodo declarado no está presente en el archivo.",
                    {"missing_periods": missing_periods},
                )
            )
        else:
            findings.append(
                _finding(
                    meta,
                    "CONT-05",
                    OK,
                    "Los periodos declarados están presentes y son válidos.",
                    {"expected_periods": period["expected"]},
                )
            )

    # CONT-06 unidad y base
    unit_issues: list[dict[str, Any]] = []
    unit_column = profile.get("unit_column")
    declared_unit = profile.get("unit")
    if unit_column and declared_unit:
        index = resolved[unit_column]["index"]
        for row_number in table.row_numbers:
            raw = table.cell(row_number, index)
            observed_unit = "" if raw is None else str(raw).strip()
            if observed_unit != declared_unit:
                if len(unit_issues) < MAX_EVIDENCE_ITEMS:
                    unit_issues.append({"row": row_number, "observed": observed_unit})
    bases = {
        c["key"]: c["base"]
        for c in columns
        if c.get("role") == "index" and c.get("base")
    }
    if unit_issues:
        findings.append(
            _finding(
                meta,
                "CONT-06",
                FALLA,
                "La unidad observada no coincide con la declarada.",
                {"declared_unit": declared_unit, "issues": unit_issues},
            )
        )
    elif not declared_unit or not bases:
        findings.append(
            _finding(
                meta,
                "CONT-06",
                NO_EVALUADO,
                "El perfil no declara unidad o base; no se puede evaluar.",
                {"declared_unit": declared_unit, "declared_bases": bases},
            )
        )
    else:
        findings.append(
            _finding(
                meta,
                "CONT-06",
                OK,
                "Unidad y base coinciden con lo declarado en el perfil.",
                {"declared_unit": declared_unit, "declared_bases": bases},
            )
        )

    return findings


# --------------------------------------------------------------------------
# Comparabilidad del IPC (P0.3)
# --------------------------------------------------------------------------


def _period_of(
    values: dict[str, dict[int, Any]], row: int, profile: dict[str, Any]
) -> tuple[int, int] | None:
    period = profile.get("period")
    if not period:
        return None
    year = values[period["year_column"]].get(row)
    month = values[period["month_column"]].get(row)
    if year is None or month is None:
        return None
    return int(year), int(month)


def _month_gap(a: tuple[int, int], b: tuple[int, int]) -> int:
    return (b[0] - a[0]) * 12 + (b[1] - a[1])


def _eval_comparisons(
    table: Table,
    profile: dict[str, Any],
    values: dict[str, dict[int, Any]],
    requested: list[str],
) -> list[Comparison]:
    specs = {c["id"]: c for c in profile.get("comparisons", [])}
    resolved = {c["key"]: c for c in profile["columns"]}
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

        num_spec = resolved[spec["numerator"]["column"]]
        den_spec = resolved[spec["denominator"]["column"]]
        num_row = int(spec["numerator"]["row"])
        den_row = int(spec["denominator"]["row"])

        num_value = values.get(num_spec["key"], {}).get(num_row)
        den_value = values.get(den_spec["key"], {}).get(den_row)
        if num_value is None or den_value is None:
            results.append(
                Comparison(
                    comparison_id=comparison_id,
                    label=spec["label"],
                    status="bloqueada",
                    reason="Fila o columna no disponible en el archivo declarado.",
                    public_evidence={
                        "numerator_cell": f"{num_spec.get('letter', '?')}{num_row}",
                        "denominator_cell": f"{den_spec.get('letter', '?')}{den_row}",
                    },
                )
            )
            continue

        num_base = num_spec.get("base")
        den_base = den_spec.get("base")
        public = {
            "numerator_cell": f"{num_spec['letter']}{num_row}",
            "denominator_cell": f"{den_spec['letter']}{den_row}",
            "numerator_base": num_base,
            "denominator_base": den_base,
            "unit": spec.get("unit") or profile.get("unit"),
        }
        private: dict[str, Any] = {}

        if num_base != den_base:
            raw = (num_value / den_value - 1.0) * 100.0
            private = {
                "computed_pct": raw,
                "computed_pct_rounded": round(raw, 4),
                "display_public": False,
                "note": (
                    "Se calculó solo para la pantalla de revisión. El número no se "
                    "muestra en la ficha de consulta ni se exporta al snapshot público."
                ),
            }
            results.append(
                Comparison(
                    comparison_id=comparison_id,
                    label=spec["label"],
                    status="bloqueada",
                    reason=(
                        "Bases distintas: el cociente entre índices de bases distintas "
                        "no es una variación y no se puede comparar directamente."
                    ),
                    public_evidence=public,
                    private_evidence=private,
                )
            )
            continue

        period_num = _period_of(values, num_row, profile)
        period_den = _period_of(values, den_row, profile)
        if period_num is None or period_den is None:
            results.append(
                Comparison(
                    comparison_id=comparison_id,
                    label=spec["label"],
                    status="bloqueada",
                    reason="No se puede verificar la contigüidad del periodo.",
                    public_evidence=public,
                )
            )
            continue

        gap = _month_gap(period_den, period_num)
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
                    public_evidence={**public, "months_between": gap},
                )
            )
            continue

        computed = (num_value / den_value - 1.0) * 100.0
        submitted: dict[str, Any] = {
            **public,
            "period": f"{period_num[0]:04d}-{period_num[1]:02d}",
            "computed_pct": round(computed, 6),
        }

        published_spec = spec.get("published")
        if published_spec:
            published_value = values.get(published_spec["column"], {}).get(
                int(published_spec["row"])
            )
            tolerance = float(spec.get("tolerance_pp", 0.005))
            cell = f"{resolved[published_spec['column']]['letter']}{int(published_spec['row'])}"
            submitted["published_cell"] = cell
            submitted["published_pct"] = (
                None if published_value is None else round(float(published_value), 6)
            )
            if published_value is None:
                results.append(
                    Comparison(
                        comparison_id=comparison_id,
                        label=spec["label"],
                        status="bloqueada",
                        reason="La variación publicada no está disponible en la celda declarada.",
                        public_evidence=submitted,
                    )
                )
                continue
            delta = abs(computed - float(published_value))
            if delta > tolerance:
                results.append(
                    Comparison(
                        comparison_id=comparison_id,
                        label=spec["label"],
                        status="bloqueada",
                        reason="La variación calculada no coincide con la publicada.",
                        public_evidence={**submitted, "delta_pp": round(delta, 6)},
                    )
                )
                continue

        results.append(
            Comparison(
                comparison_id=comparison_id,
                label=spec["label"],
                status="ok",
                reason="Misma serie, misma base, periodos contiguos y variación publicada.",
                public_evidence=submitted,
            )
        )
    return results


# --------------------------------------------------------------------------
# Identidad por SHA-256 (P0.2)
# --------------------------------------------------------------------------


def _eval_identity(
    case: dict[str, Any],
    meta: dict[str, dict[str, Any]],
) -> tuple[list[Finding], dict[str, Any], dict[str, str]]:
    findings: list[Finding] = []
    evidence: dict[str, Any] = {"resources": []}
    files: dict[str, str] = {}

    for resource in case["resources"]:
        item = config.manifest_item(resource["manifest_item"])
        path = config.ROOT / item["path"]
        if not path.exists():
            findings.append(
                _finding(
                    meta, "ID-01", NO_EVALUADO, "Archivo de identidad ausente.", {}
                )
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

    policy = config.justification_for(case["id"], "ID-01")
    if policy:
        findings.append(
            _finding(
                meta,
                "ID-01",
                ADVERTENCIA,
                (
                    "Mismos bytes con identidad distinta, cubierto por una política "
                    "de reutilización documentada."
                ),
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
                FALLA,
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
# Orquestación
# --------------------------------------------------------------------------


def _basis_digest(
    files: dict[str, str],
    profile: dict[str, Any],
    rules_doc: dict[str, Any],
    findings: list[Finding],
) -> str:
    """Digest técnico reproducible: datos, contrato, perfil, reglas, hallazgos.

    No incluye timestamps de ejecución ni de decisión.
    """
    return digest(
        {
            "files": files,
            "profile": {
                "id": profile["profile_id"],
                "version": profile["version"],
                "content_sha256": digest(profile),
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


def validate(case_id: str, write_receipt: bool = True) -> ValidationResult:
    case = config.load_case(case_id)
    profile = config.load_profile(case["profile"])
    rules_doc = config.load_rules()
    meta = config.rule_meta(rules_doc)

    method = case["method"]
    findings: list[Finding] = []
    comparisons: list[Comparison] = []
    files: dict[str, str] = {}
    entity: dict[str, Any] = {}

    if method == "identity_pair":
        findings, identity_evidence, files = _eval_identity(case, meta)
        entity = {
            "kind": "par de recursos",
            "label": case["label"],
            "resources": [
                {
                    "manifest_item": r["manifest_item"],
                    "identity": r["identity"],
                }
                for r in case["resources"]
            ],
            "same_bytes": identity_evidence.get("same_bytes"),
            "sha256": identity_evidence["resources"][0]["sha256"],
            "display": profile.get("display", {}),
        }
        license_verified = all(
            bool(
                config.manifest_item(r["manifest_item"])
                .get("license", {})
                .get("verified")
            )
            for r in case["resources"]
        )
        items = [config.manifest_item(r["manifest_item"]) for r in case["resources"]]
    else:
        item = config.manifest_item(case["manifest_item"])
        items = [item]
        path = config.ROOT / item["path"]

        # SNAP-01 integridad de bytes contra el manifiesto
        if not path.exists():
            findings.append(
                _finding(
                    meta,
                    "SNAP-01",
                    FALLA,
                    "El archivo declarado no existe.",
                    {"path": item["path"]},
                )
            )
            actual_sha = None
            files = {}
        else:
            actual_sha = file_sha256(path)
            files = {item["id"]: actual_sha}
            size = path.stat().st_size
            size_ok = size == item.get("bytes")
            hash_ok = actual_sha == item.get("sha256")
            if size_ok and hash_ok:
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
                        },
                    )
                )
            else:
                findings.append(
                    _finding(
                        meta,
                        "SNAP-01",
                        FALLA,
                        "El archivo no coincide con los bytes o el hash del manifiesto.",
                        {
                            "expected_sha256": item.get("sha256"),
                            "observed_sha256": actual_sha,
                            "expected_bytes": item.get("bytes"),
                            "observed_bytes": size,
                        },
                    )
                )

        # LIC-01 licencia
        license_info = item.get("license", {})
        if license_info.get("verified"):
            findings.append(
                _finding(
                    meta,
                    "LIC-01",
                    OK,
                    "Licencia verificada en los metadatos del recurso.",
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
                    FALLA,
                    "Sin licencia verificada: el recurso se cierra por defecto.",
                    {
                        "id": license_info.get("id"),
                        "evidence": license_info.get("evidence"),
                    },
                )
            )

        table: Table | None = None
        values: dict[str, dict[int, Any]] = {}
        read_failure: str | None = None
        is_xlsx = profile["kind"] == "xlsx"

        try:
            table = read_table(path, profile["kind"], profile.get("expected_sheet"))
        except UnexpectedSheet as exc:
            findings.append(
                _finding(
                    meta,
                    "CONT-01",
                    FALLA,
                    "La hoja observada no es la declarada en el perfil.",
                    {"expected_sheet": exc.expected, "observed_sheets": exc.observed},
                )
            )
            read_failure = "hoja inesperada"
        except ReadError as exc:
            if is_xlsx:
                findings.append(
                    _finding(
                        meta,
                        "CONT-01",
                        NO_EVALUADO,
                        f"Archivo ilegible: {exc}.",
                        {"path": item["path"]},
                    )
                )
            read_failure = "archivo ilegible"

        if table is not None and is_xlsx:
            findings.append(
                _finding(
                    meta,
                    "CONT-01",
                    OK,
                    "La hoja declarada está presente.",
                    {
                        "expected_sheet": profile.get("expected_sheet"),
                        "observed_sheets": [table.sheet],
                    },
                )
            )

        if read_failure is None:
            findings.extend(_eval_contract(table, profile, meta))
            values = _collect_values(table, profile)
        else:
            findings.extend(
                _not_evaluated(
                    meta,
                    ["CONT-02", "CONT-03", "CONT-04", "CONT-05", "CONT-06"],
                    read_failure,
                )
            )

        if table is not None and case.get("requested_comparisons"):
            comparisons = _eval_comparisons(
                table, profile, values, case["requested_comparisons"]
            )

        license_verified = bool(license_info.get("verified"))
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
            "profile": f"{profile['profile_id']}@{profile['version']}",
            "license": license_info,
            "display": profile.get("display", {}),
        }

    warnings_justified = all(f.justified for f in findings if f.status == ADVERTENCIA)

    result = ValidationResult(
        case_id=case["id"],
        label=case["label"],
        method=method,
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
        "profile_digest": digest(profile),
        "rules_digest": digest(rules_doc),
    }

    decision = config.latest_decision(case["id"])
    gate_approved = bool(
        decision
        and decision.get("gate_decision") == "habilitado"
        and decision.get("decision_basis_digest") == basis
    )
    result.state = derive_state(
        findings, license_verified, gate_approved, warnings_justified
    )

    if write_receipt:
        _write_receipt(result, case, profile, rules_doc, items, decision, gate_approved)
    return result


def _collect_values(table: Table, profile: dict[str, Any]) -> dict[str, dict[int, Any]]:
    resolved = {c["key"]: c for c in profile["columns"]}
    values: dict[str, dict[int, Any]] = {key: {} for key in resolved}
    for key, spec in resolved.items():
        index = table.column_index(spec["header"])
        if index is None:
            continue
        for row_number in table.row_numbers:
            raw = table.cell(row_number, index)
            try:
                values[key][row_number] = coerce(raw, spec["type"])
            except ValueError:
                continue
    return values


def _write_receipt(
    result: ValidationResult,
    case: dict[str, Any],
    profile: dict[str, Any],
    rules_doc: dict[str, Any],
    items: list[dict[str, Any]],
    decision: dict[str, Any] | None,
    gate_approved: bool,
) -> None:
    manifest = config.load_manifest()
    display = profile.get("display", {})
    item = items[0]
    payload = {
        "snapshot_id": manifest["snapshot_id"],
        "source_id": item.get("source_id"),
        "resource_id": item.get("resource_id"),
        "period": display.get("period"),
        "base": display.get("base"),
        "unit": display.get("unit"),
        "source_url": item.get("source_url"),
        "downloaded_at_utc": item.get("downloaded_at_utc"),
        "sha256": item.get("sha256"),
        "profile_version": f"{profile['profile_id']}@{profile['version']}",
        "rules_version": rules_doc["rules_version"],
        "findings": [f.to_dict() for f in result.findings],
        "comparisons": [c.to_private_dict() for c in result.comparisons],
        "coverage": result.coverage,
        "state": result.state,
        "digest": result.digests["validation_digest"],
    }
    receipt: dict[str, Any] = {
        "receipt_id": f"rec-{manifest['snapshot_id']}-{result.case_id}",
        "generated_at_utc": _utc_now(),
        "technical_payload": payload,
        "decision_log": None,
    }
    if decision:
        receipt["decision_log"] = {
            "decided_at_utc": decision.get("decided_at_utc"),
            "operator": decision.get("operator"),
            "rationale": decision.get("rationale"),
            "gate_decision": decision.get("gate_decision"),
            "decision_basis_digest": decision.get("decision_basis_digest"),
            "still_valid": gate_approved,
        }

    config.RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RECEIPT_DIR / f"{result.case_id}.json"
    with open(path, "w", encoding="utf-8") as fh:
        _dump(receipt, fh)


def _dump(obj: Any, fh: Any) -> None:
    import json

    json.dump(obj, fh, ensure_ascii=False, indent=2, sort_keys=True)
    fh.write("\n")


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
