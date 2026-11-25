"""Local HTTP API consumed by the Next.js web app.

The engine owns all validation, the gate and the two stores. The web app only
renders and collects input; it never decides anything.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from . import config, gate, profiles, public_api, rules, store
from .model import WARNING

app = FastAPI(
    title="INE Data Trust engine",
    description="Deterministic validation core. UI lives in the Next.js app.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Serializers
# --------------------------------------------------------------------------


def _finding(finding: Any) -> dict[str, Any]:
    return finding.to_dict()


def _state(result: Any) -> dict[str, Any]:
    return {
        "state": result.state,
        "state_text": result.state_text,
        "coverage": result.coverage,
        "digest": result.digests.get("validation_digest"),
    }


def _review_payload(case_id: str) -> dict[str, Any]:
    result = rules.validate(case_id)
    decision = config.latest_decision(case_id)
    return {
        "case_id": result.case_id,
        "label": result.label,
        "method": result.method,
        "entity": result.entity,
        **_state(result),
        "findings": [_finding(f) for f in result.findings],
        "comparisons": [c.to_private_dict() for c in result.comparisons],
        "blocking": gate.blocking_reasons(result),
        "warnings": gate.pending_warnings(result),
        "decision": decision,
        "override": config.has_override(case_id),
        "published": gate.aggregate_path(case_id).exists(),
    }


def _case_rows() -> list[dict[str, Any]]:
    rows = []
    for case in config.load_cases():
        try:
            result = rules.validate(case["id"], write_receipt=False)
        except (config.ConfigError, profiles.ProfileError) as exc:
            rows.append(
                {
                    "id": case["id"],
                    "label": case["label"],
                    "state": "borrador",
                    "state_text": f"Error: {exc}",
                    "profile": case["profile"],
                    "origin": "caso",
                    "critical": "—",
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
                "profile": result.entity.get("profile") or case["profile"],
                "origin": "demostración",
                "critical": f"{result.coverage.get('critical_evaluated')}/"
                f"{result.coverage.get('critical_total')}",
                "override": config.has_override(result.case_id),
            }
        )
    for upload in store.list_uploads():
        try:
            result = rules.validate(upload["id"], write_receipt=False)
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


# --------------------------------------------------------------------------
# Meta
# --------------------------------------------------------------------------


@app.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok", "version": app.version, "root": str(config.ROOT)}


# --------------------------------------------------------------------------
# Profiles
# --------------------------------------------------------------------------


class YamlBody(BaseModel):
    yaml: str
    overwrite: bool = False


@app.get("/profiles")
def get_profiles() -> dict[str, Any]:
    return {"profiles": profiles.list_profiles()}


@app.get("/profiles/{profile_id}")
def get_profile(profile_id: str) -> dict[str, Any]:
    try:
        text = profiles.yaml_text(profile_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="perfil no encontrado")
    return {"profile_id": profile_id, "yaml": text}


@app.post("/profiles/validate")
def validate_profile(body: YamlBody) -> dict[str, Any]:
    data, errors = profiles.validate_text(body.yaml)
    return {
        "valid": not errors,
        "errors": errors,
        "profile_id": data.get("profile_id"),
    }


@app.post("/profiles")
def create_profile(body: YamlBody) -> dict[str, Any]:
    data, errors = profiles.validate_text(body.yaml)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})
    try:
        path = profiles.save_profile(data, overwrite=body.overwrite)
    except profiles.ProfileError as exc:
        raise HTTPException(status_code=409, detail={"errors": exc.errors})
    try:
        stored = str(path.relative_to(config.ROOT))
    except ValueError:
        stored = str(path)
    return {"profile_id": data["profile_id"], "path": stored}


# --------------------------------------------------------------------------
# Review
# --------------------------------------------------------------------------


@app.get("/review/cases")
def review_cases() -> dict[str, Any]:
    return {"cases": _case_rows()}


@app.get("/review/{case_id}")
def review_detail(case_id: str) -> dict[str, Any]:
    try:
        return _review_payload(case_id)
    except (config.ConfigError, profiles.ProfileError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))


class GateBody(BaseModel):
    operator: str
    rationale: str
    decision: str = "aprobar"
    justifications: dict[str, dict[str, Any]] | None = None


@app.post("/review/{case_id}/gate")
def review_gate(case_id: str, body: GateBody) -> dict[str, Any]:
    try:
        gate.decide(
            case_id,
            body.operator,
            body.rationale,
            body.decision,
            body.justifications,
        )
    except gate.GateError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except (config.ConfigError, profiles.ProfileError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return _review_payload(case_id)


@app.post("/review/{case_id}/simulate")
def review_simulate(case_id: str) -> dict[str, Any]:
    if config.has_override(case_id):
        raise HTTPException(status_code=409, detail="Ya hay una simulación activa.")
    try:
        subject = rules.resolve_subject(case_id)
        profile = profiles.load_profile(subject.profile_id)
    except (config.ConfigError, profiles.ProfileError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    profile["version"] = f"{profile.get('version', '1.0.0')}+sim"
    config.save_override(
        case_id,
        profile,
        "Simulación: versión del perfil enmendada para demostrar la invalidación.",
    )
    report = gate.verify()
    return {
        "detail": "Simulación aplicada: el digest cambió y el agregado se retiró.",
        "quarantined": [e["case_id"] for e in report if e["quarantined"]],
    }


@app.post("/review/{case_id}/simulate/undo")
def review_simulate_undo(case_id: str) -> dict[str, Any]:
    if not config.clear_override(case_id):
        raise HTTPException(status_code=409, detail="No había simulación activa.")
    result = rules.validate(case_id, write_receipt=False)
    republished = False
    if result.state == "habilitado_para_consulta":
        gate.write_public_aggregate(result)
        republished = True
    return {"detail": "Simulación retirada.", "republished": republished}


@app.post("/review/verify")
def review_verify() -> dict[str, Any]:
    report = gate.verify()
    return {"report": report}


@app.post("/review/upload")
async def review_upload(
    file: UploadFile = File(...),
    profile: str = Form(...),
    license: str = Form("cc-by"),
) -> dict[str, Any]:
    content = await file.read()
    try:
        entry = store.register_upload(
            file.filename or "archivo", content, profile, license
        )
    except store.UploadError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"case_id": entry["id"], "label": entry["label"]}


@app.get("/review/{case_id}/receipt.json")
def review_receipt(case_id: str) -> Response:
    path = config.RECEIPT_DIR / f"{case_id}.json"
    if not path.exists():
        try:
            rules.validate(case_id)
        except (config.ConfigError, profiles.ProfileError) as exc:
            raise HTTPException(status_code=404, detail=str(exc))
    if not path.exists():
        raise HTTPException(status_code=404, detail="sin recibo")
    return Response(
        content=path.read_text(encoding="utf-8"),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="recibo-{case_id}.json"'
        },
    )


# --------------------------------------------------------------------------
# Public snapshot
# --------------------------------------------------------------------------


@app.get("/public")
def public_index() -> dict[str, Any]:
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
    return {"snapshot_id": index.get("snapshot_id"), "aggregates": aggregates}


@app.get("/public/{case_id}")
def public_detail(case_id: str) -> dict[str, Any]:
    aggregate = public_api.get_aggregate(case_id)
    if not aggregate:
        raise HTTPException(status_code=404, detail="agregado no publicado")
    return {
        "aggregate": aggregate,
        "receipt": public_api.get_receipt(case_id),
    }


@app.get("/public/{case_id}/receipt.json")
def public_receipt(case_id: str) -> Response:
    receipt = public_api.get_receipt(case_id)
    if not receipt:
        raise HTTPException(status_code=404, detail="recibo no publicado")
    import json

    return Response(
        content=json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="recibo-{case_id}.json"'
        },
    )


@app.get("/public/{case_id}/warnings")
def public_warnings(case_id: str) -> dict[str, Any]:
    aggregate = public_api.require_aggregate(case_id)
    return {
        "findings": aggregate.get("findings", []),
        "warnings": [
            f for f in aggregate.get("findings", []) if f.get("status") == WARNING
        ],
    }
