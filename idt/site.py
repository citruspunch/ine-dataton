"""Generación de las dos superficies estáticas.

`review_store/site/` es privada y muestra todo, incluida la evidencia privada.
`public_snapshot/site/` solo lee el snapshot público y no puede ver la revisión.
Sin JS, sin red, sin login.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from . import config
from .engine import validate
from .model import ADVERTENCIA, FALLA, NO_EVALUADO, OK

CSS = """
:root {
  --ink: #14181f; --muted: #5b6573; --line: #d8dee7; --bg: #f6f7f9;
  --ok: #1c6b3f; --ok-bg: #e6f3ea;
  --warn: #8a5a00; --warn-bg: #fdf2da;
  --fail: #96231f; --fail-bg: #fbe9e7;
  --none: #4a4f57; --none-bg: #eceef1;
  --accent: #1d3f6e;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 15px/1.55 -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
header.top {
  background: var(--accent); color: #fff; padding: 18px 24px;
  border-bottom: 4px solid #0d2244;
}
header.top .brand { font-size: 19px; font-weight: 650; letter-spacing: .2px; }
header.top .brand .tag {
  font-size: 11px; text-transform: uppercase; letter-spacing: .08em;
  background: rgba(255,255,255,.18); padding: 2px 7px; border-radius: 3px;
  margin-left: 8px; vertical-align: 2px;
}
header.top .sub { color: #c9d6ea; font-size: 13px; margin-top: 3px; }
main { max-width: 1000px; margin: 0 auto; padding: 26px 24px 60px; }
h1 { font-size: 24px; margin: 0 0 6px; letter-spacing: -.2px; }
h2 { font-size: 15px; text-transform: uppercase; letter-spacing: .07em;
     color: var(--muted); margin: 30px 0 10px; }
p.lead { color: var(--muted); margin: 0 0 18px; }
a { color: var(--accent); }
table { width: 100%; border-collapse: collapse; background: #fff;
        border: 1px solid var(--line); }
th, td { text-align: left; padding: 8px 11px; border-bottom: 1px solid var(--line);
         vertical-align: top; font-size: 14px; }
th { background: #eef1f5; font-size: 12px; text-transform: uppercase;
     letter-spacing: .05em; color: var(--muted); font-weight: 600; }
tr:last-child td { border-bottom: none; }
code, .mono { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
              font-size: 12.5px; }
td.mono { word-break: break-all; }
td.nw, th.nw { white-space: nowrap; }
td.ev { max-width: 380px; word-break: break-word; }
td.ev .mono { font-size: 12px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 999px;
         font-size: 12px; font-weight: 600; white-space: nowrap; }
.b-ok { color: var(--ok); background: var(--ok-bg); }
.b-warn { color: var(--warn); background: var(--warn-bg); }
.b-fail { color: var(--fail); background: var(--fail-bg); }
.b-none { color: var(--none); background: var(--none-bg); }
.b-syn { color: #5b2e86; background: #f0e7fa; }
dl.ficha { display: grid; grid-template-columns: 220px 1fr; gap: 0;
           background: #fff; border: 1px solid var(--line); margin: 0; }
dl.ficha dt, dl.ficha dd { margin: 0; padding: 8px 11px;
                            border-bottom: 1px solid var(--line); font-size: 14px; }
dl.ficha dt { color: var(--muted); background: #fafbfc; font-size: 13px; }
dl.ficha dd { word-break: break-word; }
dl.ficha dt:last-of-type, dl.ficha dd:last-of-type { border-bottom: none; }
.note { background: #fff; border-left: 3px solid var(--accent);
        padding: 10px 14px; margin: 16px 0; font-size: 14px; }
.warnbox { background: var(--warn-bg); border-left: 3px solid var(--warn);
           padding: 10px 14px; margin: 16px 0; font-size: 14px; }
footer { max-width: 1000px; margin: 0 auto; padding: 0 24px 40px;
         color: var(--muted); font-size: 12.5px; }
.cards { display: grid; gap: 10px; }
.card { background: #fff; border: 1px solid var(--line); padding: 13px 15px;
        display: flex; justify-content: space-between; gap: 14px; align-items: center; }
.card .t { font-weight: 600; }
.card .m { color: var(--muted); font-size: 13px; }
"""

BADGE_CLASS = {
    OK: "b-ok",
    FALLA: "b-fail",
    ADVERTENCIA: "b-warn",
    NO_EVALUADO: "b-none",
    "habilitado_para_consulta": "b-ok",
    "no_habilitado": "b-fail",
    "en_revision": "b-warn",
    "cerrado": "b-none",
    "borrador": "b-none",
    "bloqueada": "b-fail",
}


def _esc(value: Any) -> str:
    if value is None:
        return "—"
    return html.escape(str(value))


def _badge(status: str, text: str | None = None) -> str:
    css = BADGE_CLASS.get(status, "b-none")
    return f'<span class="badge {css}">{_esc(text or status)}</span>'


def _page(title: str, subtitle: str, body: str, footer: str) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
<header class="top">
  <div class="brand">INE Data Trust <span class="tag">prototipo</span></div>
  <div class="sub">{_esc(subtitle)}</div>
</header>
<main>
{body}
</main>
<footer>{footer}</footer>
</body>
</html>
"""


def fmt_pct(value: Any) -> str:
    if value is None:
        return "—"
    try:
        return f"{float(value):+.2f}%".replace(".", ",")
    except (TypeError, ValueError):
        return _esc(value)


def _ficha(rows: list[tuple[str, str]]) -> str:
    inner = "".join(f"<dt>{_esc(k)}</dt><dd>{v}</dd>" for k, v in rows)
    return f'<dl class="ficha">{inner}</dl>'


# --------------------------------------------------------------------------
# Sitio público (solo snapshot público)
# --------------------------------------------------------------------------


def build_public_site() -> Path:
    out = config.PUBLIC_DIR / "site"
    out.mkdir(parents=True, exist_ok=True)

    index_file = config.PUBLIC_DIR / "index.json"
    index = (
        json.loads(index_file.read_text(encoding="utf-8"))
        if index_file.exists()
        else {
            "snapshot_id": config.load_manifest()["snapshot_id"],
            "aggregates": [],
        }
    )

    for entry in index["aggregates"]:
        data = json.loads(
            (config.PUBLIC_DIR / entry["file"]).read_text(encoding="utf-8")
        )
        (out / f"{entry['case_id']}.html").write_text(
            _public_detail(data, index["snapshot_id"]), encoding="utf-8"
        )

    (out / "index.html").write_text(_public_index(index), encoding="utf-8")
    return out


def _public_index(index: dict[str, Any]) -> str:
    items = index.get("aggregates", [])
    if items:
        cards = "".join(
            f"""<div class="card">
  <div>
    <div class="t"><a href="{_esc(a["case_id"])}.html">{_esc(a["label"])}</a></div>
    <div class="m mono">{_esc(a["case_id"])} · digest {_esc(a["digest"][:16])}…</div>
  </div>
  <div>{_badge(a["state"], a["state_text"])}
  {'<span class="badge b-syn">sintético</span>' if a.get("synthetic") else ""}</div>
</div>"""
            for a in items
        )
        body = f'<div class="cards">{cards}</div>'
    else:
        body = (
            '<div class="note">El snapshot público está vacío. Un agregado solo '
            "entra aquí después del gate humano.</div>"
        )

    body = f"""
<h1>Agregados habilitados para consulta</h1>
<p class="lead">Snapshot <span class="mono">{_esc(index["snapshot_id"])}</span>.
Solo aparecen agregados que pasaron las reglas críticas, tienen licencia
verificada y recibieron visto bueno humano.</p>
{body}
"""
    return _page(
        "INE Data Trust · consulta",
        "Validación técnica del prototipo",
        body,
        "<p>Validación técnica del prototipo. No certifica, no corrige, no publica "
        "en CKAN. Los datos conservan su licencia original.</p>",
    )


def _public_detail(data: dict[str, Any], snapshot_id: str) -> str:
    entity = data.get("entity", {})
    display = entity.get("display", {})
    synthetic = entity.get("kind") == "par de recursos" or entity.get("synthetic")

    rows: list[tuple[str, str]] = [
        ("Fuente", _esc(entity.get("title") or entity.get("kind"))),
        ("Snapshot", f'<span class="mono">{_esc(snapshot_id)}</span>'),
        (
            "Dataset (CKAN)",
            f'<span class="mono">{_esc(entity.get("dataset_id"))}</span>',
        ),
        (
            "Recurso (CKAN)",
            f'<span class="mono">{_esc(entity.get("resource_id"))}</span>',
        ),
        ("Periodo", _esc(display.get("period"))),
        ("Base", _esc(display.get("base"))),
        ("Unidad", _esc(display.get("unit"))),
        ("URL de origen", _esc(entity.get("source_url"))),
        ("Descargado (UTC)", _esc(entity.get("downloaded_at_utc"))),
        ("SHA-256", f'<span class="mono">{_esc(entity.get("sha256"))}</span>'),
        ("Perfil", f'<span class="mono">{_esc(entity.get("profile"))}</span>'),
        (
            "Estado",
            _badge(data["state"], data["state_text"]),
        ),
        (
            "Digest de validación",
            f'<span class="mono">{_esc(data.get("digest"))}</span>',
        ),
    ]
    license_info = entity.get("license") or {}
    if license_info:
        rows.append(
            (
                "Licencia",
                f"{_esc(license_info.get('id'))} · {_esc(license_info.get('attribution'))}",
            )
        )

    findings = data.get("findings", [])
    rule_rows = "".join(
        f"<tr><td class='mono nw'>{_esc(f['rule_id'])}</td>"
        f"<td>{_esc(f['title'])}</td>"
        f"<td class='nw'>{_badge(f['status'])}</td>"
        f"<td>{_esc(f['message'])}</td></tr>"
        for f in findings
    )

    comparisons = data.get("comparisons", [])
    comparison_html = ""
    if comparisons:
        comp_rows = []
        for c in comparisons:
            ev = c.get("evidence", {})
            if c["status"] == "ok":
                detail = (
                    f"calculado {fmt_pct(ev.get('computed_pct'))} · "
                    f"publicado {fmt_pct(ev.get('published_pct'))} "
                    f"en {_esc(ev.get('published_cell'))}"
                )
            else:
                detail = "no se muestra ningún valor: la comparación está bloqueada"
            comp_rows.append(
                f"<tr><td>{_esc(c['label'])}</td>"
                f"<td>{_badge(c['status'])}</td>"
                f"<td>{_esc(c['reason'])}</td>"
                f"<td>{detail}</td></tr>"
            )
        comparison_html = f"""
<h2>Comparaciones solicitadas</h2>
<table>
<thead><tr><th>Comparación</th><th>Resultado</th><th>Motivo</th><th>Dato</th></tr></thead>
<tbody>{"".join(comp_rows)}</tbody>
</table>"""

    body = f"""
<p><a href="index.html">← Volver al índice</a></p>
<h1>{_esc(data["label"])}</h1>
<p class="lead">{_badge(data["state"], data["state_text"])}
{'<span class="badge b-syn">fixture sintético</span>' if synthetic else ""}</p>
{_ficha(rows)}
<h2>Reglas evaluadas</h2>
<table>
<thead><tr><th>Regla</th><th>Título</th><th>Estado</th><th>Mensaje</th></tr></thead>
<tbody>{rule_rows}</tbody>
</table>
{comparison_html}
<div class="note">La habilitación es del prototipo, no del INE. Falla, advertencia y
no evaluado se muestran sin convertir en un puntaje. El digest no incluye
timestamps de ejecución ni de decisión.</div>
"""
    return _page(
        f"{data['label']} · consulta",
        "Validación técnica del prototipo",
        body,
        "<p>Validación técnica del prototipo. No certifica, no corrige, no publica "
        "en CKAN.</p>",
    )


# --------------------------------------------------------------------------
# Sitio de revisión (privado)
# --------------------------------------------------------------------------


def build_review_site() -> Path:
    out = config.REVIEW_SITE_DIR
    out.mkdir(parents=True, exist_ok=True)

    results = [
        validate(case["id"], write_receipt=False) for case in config.load_cases()
    ]
    for result in results:
        (out / f"{result.case_id}.html").write_text(
            _review_detail(result), encoding="utf-8"
        )
    (out / "index.html").write_text(_review_index(results), encoding="utf-8")
    return out


def _review_index(results: list[Any]) -> str:
    method_label = {"contract": "contrato", "identity_pair": "identidad"}
    rows = "".join(
        f"<tr><td class='mono nw'>{_esc(r.case_id)}</td>"
        f"<td><a href='{_esc(r.case_id)}.html'>{_esc(r.label)}</a></td>"
        f"<td class='nw'>{_esc(method_label.get(r.method, r.method))}</td>"
        f"<td class='nw'>{_badge(r.state, r.state_text)}</td>"
        f"<td class='nw'>{_esc(r.coverage.get('critical_evaluated'))}/"
        f"{_esc(r.coverage.get('critical_total'))}</td></tr>"
        for r in results
    )
    body = f"""
<h1>Revisión privada</h1>
<p class="lead">Esta carpeta es local y privada. Contiene candidatos, fixtures,
recibos y decisiones. Ni la ficha pública ni el MCP leen aquí.</p>
<table>
<thead><tr><th>Caso</th><th>Etiqueta</th><th>Método</th><th>Estado</th>
<th>Críticas evaluadas</th></tr></thead>
<tbody>{rows}</tbody>
</table>
<div class="warnbox">Ningún caso entra al snapshot público sin visto bueno humano
registrado. Una advertencia sin dueño, fecha y motivo deja el caso en revisión.</div>
"""
    return _page(
        "INE Data Trust · revisión",
        "Pantalla privada de revisión",
        body,
        "<p>Bitácora: review_store/decisions/decisions.jsonl · recibos: "
        "review_store/receipts/</p>",
    )


def _review_detail(result: Any) -> str:
    entity = result.entity
    decision = config.latest_decision(result.case_id)

    if entity.get("kind") == "par de recursos":
        rows = [
            ("Caso", f'<span class="mono">{_esc(result.case_id)}</span>'),
            (
                "SHA-256 (ambos)",
                f'<span class="mono">{_esc(entity.get("sha256"))}</span>',
            ),
            ("Mismos bytes", _esc(entity.get("same_bytes"))),
            (
                "Recursos",
                "<br>".join(
                    f"{_esc(r['manifest_item'])} · {_esc(r['identity'])}"
                    for r in entity.get("resources", [])
                ),
            ),
            ("Estado", _badge(result.state, result.state_text)),
        ]
    else:
        display = entity.get("display", {})
        rows = [
            ("Caso", f'<span class="mono">{_esc(result.case_id)}</span>'),
            ("Fuente", _esc(entity.get("title"))),
            ("Periodo", _esc(display.get("period"))),
            ("Base", _esc(display.get("base"))),
            ("Unidad", _esc(display.get("unit"))),
            ("URL", _esc(entity.get("source_url"))),
            ("Descargado (UTC)", _esc(entity.get("downloaded_at_utc"))),
            ("SHA-256", f'<span class="mono">{_esc(entity.get("sha256"))}</span>'),
            ("Perfil", f'<span class="mono">{_esc(entity.get("profile"))}</span>'),
            ("Estado", _badge(result.state, result.state_text)),
        ]

    findings_rows = "".join(
        f"<tr><td class='mono nw'>{_esc(f.rule_id)}</td>"
        f"<td>{_esc(f.title)}</td>"
        f"<td class='nw'>{_badge(f.status)}</td>"
        f"<td class='nw'>{'sí' if f.critical else 'no'}</td>"
        f"<td>{_esc(f.message)}</td>"
        f"<td class='mono ev'>{_esc(json.dumps(f.evidence, ensure_ascii=False, sort_keys=True)[:700])}</td></tr>"
        for f in result.findings
    )

    comparisons_html = ""
    if result.comparisons:
        comp_rows = []
        for c in result.comparisons:
            pub = json.dumps(c.public_evidence, ensure_ascii=False, sort_keys=True)
            prv = json.dumps(c.private_evidence, ensure_ascii=False, sort_keys=True)
            if c.status == "ok":
                value = fmt_pct(c.public_evidence.get("computed_pct"))
            else:
                value = (
                    f"<strong>{fmt_pct(c.private_evidence.get('computed_pct'))}</strong> (solo revisión)"
                    if c.private_evidence
                    else "—"
                )
            comp_rows.append(
                f"<tr><td>{_esc(c.label)}</td><td class='nw'>{_badge(c.status)}</td>"
                f"<td>{_esc(c.reason)}</td><td class='nw'>{value}</td>"
                f"<td class='mono ev'>{_esc(pub)}<br>{_esc(prv)}</td></tr>"
            )
        comparisons_html = f"""
<h2>Comparaciones (evidencia privada)</h2>
<table>
<thead><tr><th>Comparación</th><th>Resultado</th><th>Motivo</th><th>Valor</th>
<th>Evidencia</th></tr></thead>
<tbody>{"".join(comp_rows)}</tbody>
</table>
<div class="warnbox">El valor de una comparación bloqueada se muestra aquí y no se
copia al snapshot público, al export ni a la ficha de consulta.</div>"""

    decision_html = (
        f"""<tr><td class="mono">{_esc(decision["decision_id"])}</td>
<td>{_esc(decision["decided_at_utc"])}</td><td>{_esc(decision["operator"])}</td>
<td>{_esc(decision["rationale"])}</td><td>{_esc(decision["gate_decision"])}</td>
<td class="mono">{_esc(decision["decision_basis_digest"][:24])}…</td></tr>"""
        if decision
        else "<tr><td colspan='6'>Sin decisión registrada.</td></tr>"
    )

    body = f"""
<p><a href="index.html">← Volver a la bandeja</a></p>
<h1>{_esc(result.label)}</h1>
<p class="lead">{_badge(result.state, result.state_text)}</p>
{_ficha(rows)}
<h2>Hallazgos</h2>
<table>
<thead><tr><th>Regla</th><th>Título</th><th>Estado</th><th>Crítica</th>
<th>Mensaje</th><th>Evidencia</th></tr></thead>
<tbody>{findings_rows}</tbody>
</table>
{comparisons_html}
<h2>Bitácora de decisiones</h2>
<table>
<thead><tr><th>Decisión</th><th>Fecha UTC</th><th>Responsable</th><th>Motivo</th>
<th>Resultado</th><th>Digest</th></tr></thead>
<tbody>{decision_html}</tbody>
</table>
<div class="note">Cobertura: {_esc(result.coverage.get("critical_evaluated"))} de
{_esc(result.coverage.get("critical_total"))} reglas críticas evaluadas. Digest de
validación <span class="mono">{_esc(result.digests.get("validation_digest"))}</span>.</div>
"""
    return _page(
        f"{result.label} · revisión",
        "Pantalla privada de revisión",
        body,
        f"<p>Recibo privado: review_store/receipts/{_esc(result.case_id)}.json</p>",
    )
