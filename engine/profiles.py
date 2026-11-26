"""Declarative YAML profiles: load, validate, list and save.

A profile is the contract a candidate file is checked against. Validation is
structural and returns field-level errors so the editor can point at the exact
key that is wrong.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from . import config

ALLOWED_TYPES = ("integer", "float", "string", "date")
MONTH_FORMATS = ("name_es", "number")
KINDS = ("xlsx", "delimited", "pair")
PERIOD_RE = re.compile(r"^(\d{4})(?:-(\d{2}))?$")

REQUIRED_FIELDS = (
    "profile_id",
    "version",
    "kind",
    "title",
    "expected_sheet",
    "header_row",
    "schema",
    "types",
    "grain",
    "dates",
)

BASE_FIELDS = ("profile_id", "version", "kind", "title")


class ProfileError(Exception):
    """Validation failed. `errors` is a list of {field, message}."""

    def __init__(self, errors: list[dict[str, str]]) -> None:
        super().__init__("; ".join(f"{e['field']}: {e['message']}" for e in errors))
        self.errors = errors


def profile_path(profile_id: str) -> Path:
    return config.PROFILE_DIR / f"{profile_id}.yaml"


def parse_yaml(text: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ProfileError(
            [{"field": "yaml", "message": f"YAML inválido: {exc}"}]
        ) from exc
    if not isinstance(data, dict):
        raise ProfileError(
            [{"field": "yaml", "message": "el perfil debe ser un mapa YAML"}]
        )
    return data


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise config.ConfigError(f"falta {path.name}") from exc
    return parse_yaml(text)


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------


def validate_profile(data: dict[str, Any]) -> list[dict[str, str]]:
    """Return a list of field errors. Empty list means the profile is valid."""
    errors: list[dict[str, str]] = []

    def err(field: str, message: str) -> None:
        errors.append({"field": field, "message": message})

    for field in BASE_FIELDS:
        if field not in data:
            err(field, "campo obligatorio ausente")

    kind = data.get("kind")
    if kind is not None and kind not in KINDS:
        err("kind", f"debe ser uno de {', '.join(KINDS)}")
    if kind == "pair":
        return errors

    for field in REQUIRED_FIELDS:
        if field in BASE_FIELDS:
            continue
        if field not in data:
            err(field, "campo obligatorio ausente")

    profile_id = data.get("profile_id")
    if profile_id is not None and not re.match(r"^[a-z0-9_]+$", str(profile_id)):
        err("profile_id", "solo minúsculas, dígitos y guion bajo")

    if kind == "xlsx" and "expected_sheet" in data and not data.get("expected_sheet"):
        err("expected_sheet", "obligatorio para perfiles XLSX")
    if kind == "delimited" and data.get("expected_sheet") not in (None, ""):
        err("expected_sheet", "debe ser null en perfiles CSV")

    header_row = data.get("header_row")
    if header_row is not None:
        if not isinstance(header_row, int) or header_row < 1:
            err("header_row", "debe ser un entero mayor o igual a 1")

    if "schema" in data:
        errors.extend(_validate_schema(data))
    if "grain" in data:
        errors.extend(_validate_grain(data))
    if "dates" in data:
        errors.extend(_validate_dates(data))
    if (
        "summary_notes" in data
        and data["summary_notes"] is not None
        and not isinstance(data["summary_notes"], str)
    ):
        err("summary_notes", "debe ser texto o null")
    return errors


def _validate_schema(data: dict[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    schema = data.get("schema")
    if not isinstance(schema, list) or not schema:
        return [{"field": "schema", "message": "debe declarar al menos una columna"}]

    declared_types = data.get("types")
    allowed_here = set(ALLOWED_TYPES)
    if declared_types is not None:
        if not isinstance(declared_types, list) or not declared_types:
            errors.append({"field": "types", "message": "debe ser una lista no vacía"})
        else:
            unknown = [t for t in declared_types if t not in ALLOWED_TYPES]
            if unknown:
                errors.append(
                    {
                        "field": "types",
                        "message": f"tipos no permitidos: {', '.join(map(str, unknown))}",
                    }
                )
            allowed_here = {
                t for t in declared_types if t in ALLOWED_TYPES
            } or allowed_here

    names: set[str] = set()
    for index, entry in enumerate(schema):
        prefix = f"schema[{index}]"
        if not isinstance(entry, dict):
            errors.append({"field": prefix, "message": "debe ser un mapa"})
            continue
        name = entry.get("name")
        if not name:
            errors.append({"field": f"{prefix}.name", "message": "obligatorio"})
        elif name in names:
            errors.append({"field": f"{prefix}.name", "message": f"duplicado: {name}"})
        else:
            names.add(str(name))

        if not entry.get("column"):
            errors.append({"field": f"{prefix}.column", "message": "obligatorio"})

        type_name = entry.get("type")
        if type_name not in ALLOWED_TYPES:
            errors.append(
                {
                    "field": f"{prefix}.type",
                    "message": f"debe ser uno de {', '.join(ALLOWED_TYPES)}",
                }
            )
        elif type_name not in allowed_here:
            errors.append(
                {
                    "field": f"{prefix}.type",
                    "message": f"{type_name} no está declarado en types",
                }
            )
        for key in ("unit", "reference", "notes"):
            if (
                key in entry
                and entry[key] is not None
                and not isinstance(entry[key], str)
            ):
                errors.append(
                    {"field": f"{prefix}.{key}", "message": "debe ser texto o null"}
                )
        if "nullable" in entry and not isinstance(entry["nullable"], bool):
            errors.append(
                {"field": f"{prefix}.nullable", "message": "debe ser booleano"}
            )
    return errors


def _validate_grain(data: dict[str, Any]) -> list[dict[str, str]]:
    grain = data.get("grain")
    if not isinstance(grain, list) or not grain:
        return [{"field": "grain", "message": "debe ser una lista no vacía"}]
    names = {e.get("name") for e in data.get("schema") or [] if isinstance(e, dict)}
    errors = []
    for index, name in enumerate(grain):
        if name not in names:
            errors.append(
                {"field": f"grain[{index}]", "message": f"{name} no existe en schema"}
            )
    return errors


def _validate_dates(data: dict[str, Any]) -> list[dict[str, str]]:
    dates = data.get("dates")
    if not isinstance(dates, dict):
        return [{"field": "dates", "message": "debe ser un mapa"}]

    errors: list[dict[str, str]] = []
    names = {e.get("name") for e in data.get("schema") or [] if isinstance(e, dict)}
    if not dates.get("year"):
        errors.append({"field": "dates.year", "message": "obligatorio"})
    elif dates["year"] not in names:
        errors.append(
            {
                "field": "dates.year",
                "message": f"{dates['year']} no existe en schema",
            }
        )

    has_month = bool(dates.get("month"))
    if has_month and dates["month"] not in names:
        errors.append(
            {
                "field": "dates.month",
                "message": f"{dates['month']} no existe en schema",
            }
        )

    month_format = dates.get("month_format")
    if has_month and month_format not in MONTH_FORMATS:
        errors.append(
            {
                "field": "dates.month_format",
                "message": f"debe ser uno de {', '.join(MONTH_FORMATS)}",
            }
        )

    expected = dates.get("expected")
    period_range = dates.get("range")
    if not expected and not period_range:
        errors.append(
            {"field": "dates", "message": "declare expected o range con periodos"}
        )
    period_hint = "AAAA-MM" if has_month else "AAAA"
    if expected:
        if not isinstance(expected, list):
            errors.append({"field": "dates.expected", "message": "debe ser una lista"})
        else:
            for index, period in enumerate(expected):
                if not isinstance(period, str) or not _period_matches(
                    period, has_month
                ):
                    errors.append(
                        {
                            "field": f"dates.expected[{index}]",
                            "message": f"formato {period_hint}",
                        }
                    )
    if period_range:
        if not isinstance(period_range, dict):
            errors.append({"field": "dates.range", "message": "debe ser from/to"})
        else:
            for key in ("from", "to"):
                value = period_range.get(key)
                if not isinstance(value, str) or not _period_matches(value, has_month):
                    errors.append(
                        {
                            "field": f"dates.range.{key}",
                            "message": f"formato {period_hint}",
                        }
                    )
            if (
                isinstance(period_range.get("from"), str)
                and isinstance(period_range.get("to"), str)
                and period_range["from"] > period_range["to"]
            ):
                errors.append(
                    {"field": "dates.range", "message": "from debe ser anterior a to"}
                )
    return errors


def _period_matches(value: str, has_month: bool) -> bool:
    match = PERIOD_RE.match(value)
    return bool(match) and bool(match.group(2)) == has_month


# --------------------------------------------------------------------------
# Loading and listing
# --------------------------------------------------------------------------


def load_profile(profile_id: str, case_id: str | None = None) -> dict[str, Any]:
    """Load a profile, applying a simulation override when one exists."""
    if case_id:
        override = config.OVERRIDE_DIR / f"{case_id}.yaml"
        if override.exists():
            data = read_yaml(override)
            if data.get("profile_id") == profile_id:
                data["_override"] = True
                return data

    data = read_yaml(profile_path(profile_id))
    errors = validate_profile(data)
    if errors:
        raise ProfileError(errors)
    return data


def list_profiles() -> list[dict[str, Any]]:
    """Profiles available to the selector. IPC profiles come first."""
    kind_label = {"delimited": "CSV", "xlsx": "XLSX"}
    out = []
    for path in sorted(config.PROFILE_DIR.glob("*.yaml")):
        try:
            data = read_yaml(path)
        except (config.ConfigError, ProfileError):
            continue
        if data.get("kind") == "pair":
            continue
        errors = validate_profile(data)
        out.append(
            {
                "profile_id": data.get("profile_id", path.stem),
                "version": str(data.get("version", "")),
                "kind": data.get("kind"),
                "kind_label": kind_label.get(data.get("kind"), data.get("kind")),
                "topic": data.get("topic"),
                "title": data.get("title", path.stem),
                "description": (data.get("description") or "").strip(),
                "expected_sheet": data.get("expected_sheet"),
                "valid": not errors,
                "errors": errors,
            }
        )
    out.sort(key=lambda p: (p["topic"] != "ipc", p["profile_id"]))
    return out


def yaml_text(profile_id: str) -> str:
    return profile_path(profile_id).read_text(encoding="utf-8")


def save_profile(data: dict[str, Any], overwrite: bool = False) -> Path:
    """Validate and persist a profile under profiles/. Returns its path."""
    errors = validate_profile(data)
    if errors:
        raise ProfileError(errors)

    profile_id = data["profile_id"]
    path = profile_path(profile_id)
    if path.exists() and not overwrite:
        raise ProfileError(
            [{"field": "profile_id", "message": f"ya existe un perfil {profile_id}"}]
        )
    config.PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)
    return path


def validate_text(text: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Parse and validate raw YAML text. Returns (data, errors)."""
    try:
        data = parse_yaml(text)
    except ProfileError as exc:
        return {}, exc.errors
    return data, validate_profile(data)


# --------------------------------------------------------------------------
# Contract validator entry point: python -m engine.profiles [paths...]
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="python -m engine.profiles",
        description="Valida contratos YAML de profiles/ y reporta errores por campo.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="archivos YAML; por defecto todos los de profiles/",
    )
    args = parser.parse_args(argv)

    paths = [Path(item) for item in args.paths] or sorted(
        config.PROFILE_DIR.glob("*.yaml")
    )
    if not paths:
        print("no hay perfiles para validar")
        return 0

    failed = 0
    for path in paths:
        try:
            data = parse_yaml(path.read_text(encoding="utf-8"))
        except (OSError, ProfileError) as exc:
            failed += 1
            print(f"✗ {path.name}: {exc}")
            continue
        errors = validate_profile(data)
        if errors:
            failed += 1
            print(f"✗ {path.name}")
            for error in errors:
                print(f"    {error['field']}: {error['message']}")
        else:
            print(f"✓ {path.name}")

    print(f"\n{len(paths) - failed}/{len(paths)} contratos válidos")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
