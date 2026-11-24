"""Local application: review inbox, human gate and consultation portal.

Single server, no JS build and no external services. Templates render on the
server; forms use POST + redirect.
"""

from __future__ import annotations

import html
import json
import urllib.parse
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .. import config, engine, gate, public_api, store
from ..model import WARNING, FAILURE, NOT_EVALUATED, OK

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

STATE_CLASS = {
    "habilitado_para_consulta": "is-ok",
    "en_revision": "is-warn",
    "no_habilitado": "is-fail",
    "cerrado": "is-none",
    "borrador": "is-none",
}
SEVERITY_CLASS = {
    OK: "is-ok",
    FAILURE: "is-fail",
    WARNING: "is-warn",
    NOT_EVALUATED: "is-none",
}
SEVERITY_LABEL = {
    OK: "ok",
    FAILURE: "falla",
    WARNING: "advertencia",
    NOT_EVALUATED: "no evaluado",
}
DECISION_LABEL = gate.DECISION_LABEL


def _fmt_pct(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):+.2f}%".replace(".", ",")
    except (TypeError, ValueError):
        return str(value)


def _fmt_index(value: Any) -> str:
    try:
        return (
            f"{float(value):,.6f}".replace(",", "_").replace(".", ",").replace("_", ".")
        )
    except (TypeError, ValueError):
        return "—"


def _redirect(url: str, msg: str | None = None, kind: str = "ok") -> RedirectResponse:
    if msg:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}msg={urllib.parse.quote(msg)}&kind={kind}"
    return RedirectResponse(url=url, status_code=303)


def create_app() -> FastAPI:
    app = FastAPI(
        title="INE Data Trust · prototipo",
        description="Validación técnica de agregados oficiales publicados.",
        docs_url=None,
        redoc_url=None,
    )
    app.mount(
        "/static",
        StaticFiles(directory=str(BASE_DIR / "static")),
        name="static",
    )
    app.state.templates = templates

    # ------------------------------------------------------------------
    # Review inbox
    # ------------------------------------------------------------------

    def subject_rows() -> list[dict[str, Any]]:
        rows = []
        for case in config.load_cases():
            try:
                result = engine.validate(case["id"], write_receipt=False)
            except Exception as exc:  # a broken case must not take the inbox down
                rows.append(
                    {
                        "id": case["id"],
                        "label": case["label"],
                        "state": "borrador",
                        "state_text": f"Error: {exc}",
                        "profile": case["profile"],
                        "origin": "caso",
                        "critical": "—",
                        "quarantined": False,
                        "override": False,
                    }
                )
                continue
            rows.append(
                {
                    "id": result.case_id,
                    "label": result.label,
                    "state": result.state,
                    "state_text": result.state_text,
                    "profile": (result.entity.get("profile") or case["profile"]),
                    "origin": "demostración",
                    "critical": f"{result.coverage.get('critical_evaluated')}/"
                    f"{result.coverage.get('critical_total')}",
                    "override": config.has_override(result.case_id),
                }
            )
        for upload in store.list_uploads():
            try:
                result = engine.validate(upload["id"], write_receipt=False)
            except Exception:
                continue
            rows.append(
                {
                    "id": result.case_id,
                    "label": upload["label"],
                    "state": result.state,
                    "state_text": result.state_text,
                    "profile": upload["profile_id"],
                    "origin": "archivo cargado",
                    "critical": f"{result.coverage.get('critical_evaluated')}/"
                    f"{result.coverage.get('critical_total')}",
                    "override": config.has_override(result.case_id),
                }
            )
        return rows

    @app.get("/", response_class=HTMLResponse)
    def public_index(request: Request) -> HTMLResponse:
        index = public_api.load_index()
        aggregates = []
        for entry in index.get("aggregates", []):
            aggregate = public_api.get_aggregate(entry["case_id"])
            if not aggregate:
                continue
            entity = aggregate.get("entity", {})
            aggregates.append(
                {
                    **entry,
                    "topic": entity.get("topic"),
                    "series_count": len(entity.get("series", [])),
                    "sha256": entity.get("sha256"),
                }
            )
        return templates.TemplateResponse(
            request,
            "public_index.html",
            {
                "snapshot_id": index.get("snapshot_id"),
                "aggregates": aggregates,
                "msg": request.query_params.get("msg"),
                "kind": request.query_params.get("kind", "ok"),
                "active": "public",
            },
        )

    @app.get("/review", response_class=HTMLResponse)
    def review_inbox(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "review_inbox.html",
            {
                "rows": subject_rows(),
                "profiles": config.list_profiles(),
                "licenses": store.LICENSE_CHOICES,
                "state_class": STATE_CLASS,
                "msg": request.query_params.get("msg"),
                "kind": request.query_params.get("kind", "ok"),
                "active": "review",
            },
        )

    @app.post("/review/upload")
    async def review_upload(
        request: Request,
        file: UploadFile = File(...),
        profile: str = Form(...),
        license: str = Form("cc-by"),
    ) -> Response:
        content = await file.read()
        try:
            entry = store.register_upload(
                file.filename or "archivo",
                content,
                profile,
                license,
            )
        except store.UploadError as exc:
            return _redirect("/review", str(exc), "err")
        return _redirect(
            f"/review/{entry['id']}",
            "Archivo recibido. SHA-256 calculado y registrado en el manifiesto de cargas.",
        )

    @app.post("/review/examples/{case_id}")
    def load_example(case_id: str) -> Response:
        try:
            case = config.load_case(case_id)
        except config.ConfigError:
            return _redirect("/review", "Caso desconocido", "err")
        return _redirect(f"/review/{case_id}", f"Caso cargado: {case['label']}")

    # ------------------------------------------------------------------
    # Review detail and human gate
    # ------------------------------------------------------------------

    def _context(case_id: str, request: Request) -> dict[str, Any]:
        result = engine.validate(case_id)
        decision = config.latest_decision(case_id)
        return {
            "result": result,
            "entity": result.entity,
            "decision": decision,
            "decision_label": DECISION_LABEL.get(
                (decision or {}).get("gate_decision", ""), None
            ),
            "blocking": gate.blocking_reasons(result),
            "warnings": gate.pending_warnings(result),
            "has_override": config.has_override(case_id),
            "in_public": gate.aggregate_path(case_id).exists(),
            "severity_label": SEVERITY_LABEL,
            "severity_class": SEVERITY_CLASS,
            "state_class": STATE_CLASS,
            "fmt_pct": _fmt_pct,
            "fmt_index": _fmt_index,
            "msg": request.query_params.get("msg"),
            "kind": request.query_params.get("kind", "ok"),
            "active": "review",
        }

    @app.get("/review/{case_id}", response_class=HTMLResponse)
    def review_detail(request: Request, case_id: str) -> Response:
        try:
            context = _context(case_id, request)
        except config.ConfigError as exc:
            return _redirect("/review", str(exc), "err")
        return templates.TemplateResponse(request, "review_detail.html", context)

    @app.post("/review/{case_id}/gate")
    async def review_gate(request: Request, case_id: str) -> Response:
        form = await request.form()
        operator = str(form.get("operator") or "")
        rationale = str(form.get("rationale") or "")
        decision = str(form.get("decision") or "aprobar")

        justifications: dict[str, dict[str, Any]] = {}
        for key in form.keys():
            if not key.startswith("just_owner__"):
                continue
            rule_id = key.split("__", 1)[1]
            justifications[rule_id] = {
                "owner": str(form.get(f"just_owner__{rule_id}") or ""),
                "reason": str(form.get(f"just_reason__{rule_id}") or ""),
                "policy": str(form.get(f"just_policy__{rule_id}") or ""),
            }

        try:
            result = gate.decide(case_id, operator, rationale, decision, justifications)
        except gate.GateError as exc:
            return _redirect(f"/review/{case_id}", f"No se registró: {exc}", "err")

        if decision == "rechazar":
            return _redirect(
                f"/review/{case_id}",
                "Decisión registrada: rechazado. El agregado no se publica.",
            )
        return _redirect(
            f"/review/{case_id}",
            f"Habilitado. Estado: {result.state_text}. Publicado en el portal de consulta.",
        )

    @app.post("/review/{case_id}/simulate")
    def simulate_change(case_id: str) -> Response:
        try:
            subject = engine.resolve_subject(case_id)
            profile = config.load_profile(subject.profile_id)
        except config.ConfigError as exc:
            return _redirect(f"/review/{case_id}", str(exc), "err")
        if config.has_override(case_id):
            return _redirect(
                f"/review/{case_id}", "Ya hay una simulación activa.", "err"
            )

        version = str(profile.get("version", "1.0.0"))
        profile["version"] = f"{version}+sim"
        config.save_override(
            case_id,
            profile,
            "Simulación: versión del perfil enmendada para demostrar la invalidación.",
        )
        gate.verify()
        return _redirect(
            f"/review/{case_id}",
            "Simulación aplicada: el perfil cambió de versión. El digest cambió y la "
            "decisión quedó invalidada; el agregado se retiró del portal público.",
            "warn",
        )

    @app.post("/review/{case_id}/simulate/undo")
    def undo_simulation(case_id: str) -> Response:
        removed = config.clear_override(case_id)
        if not removed:
            return _redirect(f"/review/{case_id}", "No había simulación activa.", "err")
        result = engine.validate(case_id, write_receipt=False)
        if result.state == "habilitado_para_consulta":
            gate.write_public_aggregate(engine.validate(case_id, write_receipt=False))
            return _redirect(
                f"/review/{case_id}",
                "Simulación retirada. La decisión vuelve a sostener el agregado y se "
                "republica en el portal de consulta.",
            )
        return _redirect(
            f"/review/{case_id}",
            "Simulación retirada. El caso no queda habilitado: la decisión anterior no "
            "sostiene el digest actual.",
            "warn",
        )

    @app.post("/review/verify")
    def run_verify() -> Response:
        report = gate.verify()
        quarantined = [e["case_id"] for e in report if e["quarantined"]]
        invalid = [
            e["case_id"] for e in report if e["decision"] and not e["decision_valid"]
        ]
        if quarantined:
            return _redirect(
                "/review",
                f"Retirados del portal público: {', '.join(quarantined)}.",
                "warn",
            )
        if invalid:
            return _redirect(
                "/review", f"Decisiones invalidadas: {', '.join(invalid)}.", "warn"
            )
        return _redirect(
            "/review", "Verificación correcta: todas las decisiones vigentes."
        )

    @app.get("/review/{case_id}/receipt.json")
    def private_receipt(case_id: str) -> Response:
        path = config.RECEIPT_DIR / f"{case_id}.json"
        if not path.exists():
            engine.validate(case_id)
        if not path.exists():
            return JSONResponse({"error": "sin recibo"}, status_code=404)
        return Response(
            content=path.read_text(encoding="utf-8"),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="recibo-{case_id}.json"'
            },
        )

    # ------------------------------------------------------------------
    # Consultation portal
    # ------------------------------------------------------------------

    def _public_context(
        case_id: str,
        request: Request,
        comparison: dict[str, Any] | None = None,
        selection: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        aggregate = public_api.get_aggregate(case_id)
        if not aggregate:
            return None
        series = public_api.series_catalog(aggregate)
        default = next(
            (s for s in series if s["comparable"]), series[0] if series else None
        )
        default_periods = default["periods"] if default else []
        query = request.query_params
        periods = sorted({p for s in series for p in s["periods"]})
        chosen = selection or {}
        return {
            "aggregate": aggregate,
            "entity": aggregate.get("entity", {}),
            "series": series,
            "periods": periods,
            "comparison": comparison,
            "sel": {
                "series_a": chosen.get("series_a")
                or query.get("series_a")
                or (default["series_id"] if default else ""),
                "period_a": chosen.get("period_a")
                or query.get("period_a")
                or (default_periods[0] if default_periods else ""),
                "series_b": chosen.get("series_b")
                or query.get("series_b")
                or (default["series_id"] if default else ""),
                "period_b": chosen.get("period_b")
                or query.get("period_b")
                or (default_periods[-1] if default_periods else ""),
            },
            "receipt": public_api.get_receipt(case_id),
            "severity_label": SEVERITY_LABEL,
            "severity_class": SEVERITY_CLASS,
            "state_class": STATE_CLASS,
            "fmt_pct": _fmt_pct,
            "fmt_index": _fmt_index,
            "msg": query.get("msg"),
            "kind": query.get("kind", "ok"),
            "active": "public",
        }

    @app.get("/a/{case_id}", response_class=HTMLResponse)
    def public_detail(request: Request, case_id: str) -> Response:
        context = _public_context(case_id, request)
        if context is None:
            return _redirect(
                "/", "Ese agregado no está habilitado para consulta.", "err"
            )
        return templates.TemplateResponse(request, "public_detail.html", context)

    @app.post("/a/{case_id}/compare", response_class=HTMLResponse)
    async def public_compare(request: Request, case_id: str) -> Response:
        form = await request.form()
        series_a = str(form.get("series_a") or "")
        series_b = str(form.get("series_b") or "")
        period_a = str(form.get("period_a") or "")
        period_b = str(form.get("period_b") or "")
        try:
            comparison = public_api.compare(
                case_id, series_a, period_a, series_b, period_b
            )
        except public_api.PublicError as exc:
            comparison = exc.to_dict()
        query = urllib.parse.urlencode(
            {
                "series_a": series_a,
                "period_a": period_a,
                "series_b": series_b,
                "period_b": period_b,
            }
        )
        context = _public_context(
            case_id,
            request,
            comparison,
            selection={
                "series_a": series_a,
                "period_a": period_a,
                "series_b": series_b,
                "period_b": period_b,
            },
        )
        if context is None:
            return _redirect(
                "/", "Ese agregado no está habilitado para consulta.", "err"
            )
        context["back_url"] = f"/a/{case_id}?{query}"
        return templates.TemplateResponse(request, "public_detail.html", context)

    @app.get("/a/{case_id}/receipt.json")
    def public_receipt(case_id: str) -> Response:
        receipt = public_api.get_receipt(case_id)
        if not receipt:
            return JSONResponse({"error": "recibo no publicado"}, status_code=404)
        return Response(
            content=json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="recibo-{case_id}.json"'
            },
        )

    @app.get("/a/{case_id}/ficha", response_class=HTMLResponse)
    def public_ficha(request: Request, case_id: str) -> Response:
        context = _public_context(case_id, request)
        if context is None:
            return _redirect(
                "/", "Ese agregado no está habilitado para consulta.", "err"
            )
        return templates.TemplateResponse(request, "ficha.html", context)

    return app


app = create_app()
