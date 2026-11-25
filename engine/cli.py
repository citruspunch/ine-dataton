"""Prototype CLI. No login, no free URLs, no SQL.

The main interface is the web app (`python app.py`); the CLI exists to show that
the engine and the gate do not depend on the interface.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import config, gate
from .rules import validate
from .model import WARNING, FAILURE, NOT_EVALUATED, OK

STATUS_LABEL = {
    OK: "ok",
    FAILURE: "falla",
    WARNING: "advertencia",
    NOT_EVALUATED: "no evaluado",
}


def _table(headers: list[str], rows: list[list[str]], indent: str = "") -> str:
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    out = [indent + line, indent + "  ".join("-" * w for w in widths)]
    for row in rows:
        out.append(
            indent + "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))
        )
    return "\n".join(out)


def _fmt_pct(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):+.2f}%".replace(".", ",")
    except (TypeError, ValueError):
        return str(value)


def _subject_ids() -> list[str]:
    from . import store

    return [case["id"] for case in config.load_cases()] + [
        upload["id"] for upload in store.list_uploads()
    ]


def cmd_list(args: argparse.Namespace) -> int:
    rows = []
    for subject_id in _subject_ids():
        result = validate(subject_id, write_receipt=False)
        rows.append(
            [
                subject_id,
                result.state,
                f"{result.coverage.get('critical_evaluated', 0)}/"
                f"{result.coverage.get('critical_total', 0)}",
                result.label,
            ]
        )
    print(_table(["sujeto", "estado", "críticas", "etiqueta"], rows))
    return 0


def _print_result(result: Any, verbose: bool = True) -> None:
    print("")
    print(f"caso      {result.case_id}")
    print(f"etiqueta  {result.label}")
    print(f"estado    {result.state}  ·  {result.state_text}")
    print(
        f"cobertura {result.coverage.get('critical_evaluated')}/"
        f"{result.coverage.get('critical_total')} reglas críticas evaluadas"
    )
    print(f"digest    {result.digests.get('validation_digest')}")
    if not verbose:
        return

    rows = [
        [
            f.rule_id,
            STATUS_LABEL.get(f.status, f.status),
            "sí" if f.critical else "no",
            f.message,
        ]
        for f in result.findings
    ]
    print("")
    print(_table(["regla", "estado", "crítica", "mensaje"], rows, indent="  "))

    if result.comparisons:
        print("")
        print("  comparaciones")
        for c in result.comparisons:
            if c.status == "ok":
                detail = (
                    f"publicado {_fmt_pct(c.public_evidence.get('published_pct'))} "
                    f"({c.public_evidence.get('published_cell')})"
                )
            elif c.private_evidence.get("computed_pct") is not None:
                detail = (
                    f"{_fmt_pct(c.private_evidence['computed_pct'])} solo en revisión"
                )
            else:
                detail = "sin valor calculado"
            print(f"    {c.comparison_id:22s} {c.status:10s} {detail}")
            print(f"    {'':22s} {c.reason}")


def cmd_validate(args: argparse.Namespace) -> int:
    ids = args.cases or _subject_ids()
    for subject_id in ids:
        try:
            result = validate(subject_id)
        except config.ConfigError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        _print_result(result, verbose=not args.summary)
    print("")
    print("recibos privados en review_store/receipts/")
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    try:
        result = gate.promote(args.case, args.operator, args.rationale)
    except (gate.GateError, config.ConfigError) as exc:
        print(f"NO HABILITADO: {exc}", file=sys.stderr)
        return 3
    print(f"habilitado: {result.case_id}")
    print(f"  estado    {result.state} · {result.state_text}")
    print(f"  digest    {result.digests['decision_basis_digest']}")
    print(f"  snapshot  {gate.aggregate_path(result.case_id)}")
    return 0


def cmd_revoke(args: argparse.Namespace) -> int:
    try:
        gate.revoke(args.case, args.operator, args.rationale)
    except config.ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"decisión revocada: {args.case}")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    report = gate.verify()
    rows = []
    for entry in report:
        if entry["decision"] is None:
            valid = "sin decisión"
        elif entry["decision_valid"]:
            valid = "válida"
        else:
            valid = "INVALIDADA"
        rows.append(
            [
                entry["case_id"],
                entry["state"],
                valid,
                "sí" if entry["in_public_snapshot"] else "no",
                entry["digest"][:16] + "…",
            ]
        )
    print(_table(["caso", "estado", "decisión", "en snapshot", "digest"], rows))
    invalid = [e for e in report if e["decision"] and not e["decision_valid"]]
    quarantined = [e for e in report if e.get("quarantined")]
    for entry in quarantined:
        print(
            f"Retirado del snapshot público: {entry['case_id']} "
            "(la decisión ya no sostiene el agregado)",
            file=sys.stderr,
        )
    if invalid:
        print(
            f"Atención: {len(invalid)} decisión(es) invalidada(s). Cambió un archivo, "
            "el perfil, la versión de reglas o un hallazgo.",
            file=sys.stderr,
        )
        return 4
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    path = gate.aggregate_path(args.case)
    if not path.exists():
        print(
            f"ERROR: {args.case} no está en el snapshot público. "
            "Solo se exporta lo habilitado por el gate.",
            file=sys.stderr,
        )
        return 3
    data = json.loads(path.read_text(encoding="utf-8"))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        print(f"exportado {args.out}")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    from .api import app

    print(f"INE Data Trust engine · http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="idt",
        description="INE Data Trust: validación técnica de agregados publicados.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="lista la bandeja con su estado")
    p_list.set_defaults(func=cmd_list)

    p_validate = sub.add_parser("validate", help="evalúa uno o todos los sujetos")
    p_validate.add_argument("cases", nargs="*", help="ids; vacío = todos")
    p_validate.add_argument("--summary", action="store_true", help="solo resumen")
    p_validate.set_defaults(func=cmd_validate)

    p_promote = sub.add_parser("promote", help="registra el visto bueno y publica")
    p_promote.add_argument("case")
    p_promote.add_argument("--operator", required=True)
    p_promote.add_argument("--rationale", required=True)
    p_promote.set_defaults(func=cmd_promote)

    p_revoke = sub.add_parser("revoke", help="revoca una decisión y retira el agregado")
    p_revoke.add_argument("case")
    p_revoke.add_argument("--operator", required=True)
    p_revoke.add_argument("--rationale", required=True)
    p_revoke.set_defaults(func=cmd_revoke)

    p_verify = sub.add_parser("verify", help="recalcula digests y valida decisiones")
    p_verify.set_defaults(func=cmd_verify)

    p_export = sub.add_parser("export", help="exporta el JSON público de un caso")
    p_export.add_argument("case")
    p_export.add_argument("--out", help="ruta de salida; vacío = stdout")
    p_export.set_defaults(func=cmd_export)

    p_serve = sub.add_parser("serve", help="arranca la aplicación web local")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.set_defaults(func=cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except config.ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
