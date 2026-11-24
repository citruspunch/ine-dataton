"""P0.1: contrato de esquema, tipo, grano, periodo, unidad y base."""

from __future__ import annotations

import pytest

from idt import config, engine
from idt.model import ADVERTENCIA, FALLA, NO_EVALUADO, OK


def test_csv_correcto_pasa():
    result = engine.validate("csv_ok", write_receipt=False)
    assert [f.status for f in result.findings] == [OK] * len(result.findings)
    assert result.coverage["complete"]


def test_columna_faltante_falla():
    result = engine.validate("csv_columna_faltante", write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "CONT-02")
    assert finding.status == FALLA
    assert finding.evidence["missing_columns"] == ["unidad"]
    assert result.state == "no_habilitado"


def test_grano_duplicado_falla():
    result = engine.validate("csv_grano_duplicado", write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "CONT-04")
    assert finding.status == FALLA
    assert finding.evidence["duplicates"][0]["grain"] == [
        2025,
        2,
        "serie_mensual_sintetica",
    ]


def test_hoja_inesperada_falla_y_no_es_no_evaluado():
    result = engine.validate("xlsx_hoja_inesperada", write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "CONT-01")
    assert finding.status == FALLA
    assert finding.evidence["expected_sheet"] == "Datos"
    assert "Resumen" in finding.evidence["observed_sheets"]


def test_critica_no_evaluada_bloquea():
    result = engine.validate("xlsx_hoja_inesperada", write_receipt=False)
    assert not result.coverage["complete"]
    assert result.state == "no_habilitado"
    assert any(f.status == NO_EVALUADO for f in result.findings)


def test_segundo_perfil_declarativo_sin_tocar_el_motor():
    csv_result = engine.validate("csv_ok", write_receipt=False)
    xlsx_result = engine.validate("xlsx_ok", write_receipt=False)
    assert csv_result.method == xlsx_result.method == "contract"
    assert [f.status for f in xlsx_result.findings] == [OK] * len(xlsx_result.findings)
    assert xlsx_result.entity["profile"] == "contrato_mensual_xlsx@1.1.0"


def test_segundo_recurso_real_con_forma_distinta():
    """El perfil regional usa una tabla ancha y un rango de periodos."""
    result = engine.validate("ipc_regional", write_receipt=False)
    assert result.coverage["complete"]
    assert [f.status for f in result.findings] == [OK] * len(result.findings)
    series = result.entity["series"]
    assert len(series) == 9
    assert {len(s["points"]) for s in series} == {22}
    assert series[0]["points"][0]["period"] == "2025-01"


def test_los_perfiles_no_declaran_coordenadas_fijas():
    """Desacople: ni filas ni letras de columna en los perfiles."""
    import yaml

    forbidden = {"letter", "row", "row_number", "cell"}
    for path in config.PROFILE_DIR.glob("*.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))

        def walk(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    assert key not in forbidden, f"{path.name} declara {key!r}"
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(data)


def test_la_evidencia_registra_la_celda_como_metadato():
    result = engine.validate("ipc_empalme", write_receipt=False)
    comp = next(c for c in result.comparisons if c.comparison_id == "mensual_ene_2025")
    assert comp.public_evidence["published_cell"] == "G504"
    assert comp.public_evidence["numerator_cell"] == "F504"
    assert comp.public_evidence["denominator_cell"] == "F503"


def test_csv_ilegible_queda_no_evaluado(sandbox):
    from idt import store

    entry = store.register_upload(
        "roto.csv", b"\xff\xfe\x00binario", "contrato_mensual", "cc-by"
    )
    result = engine.validate(entry["id"], write_receipt=False)
    assert result.state == "no_habilitado"
    assert not result.coverage["complete"]
    assert all(
        f.status == NO_EVALUADO for f in result.findings if f.rule_id.startswith("CONT")
    )


def test_xls_heredado_se_lee_y_valida(tmp_path, sandbox):
    """El formato heredado .xls se lee con xlrd, no se rechaza."""
    import xlwt

    from idt import store

    path = tmp_path / "contrato.xls"
    book = xlwt.Workbook()
    sheet = book.add_sheet("Datos")
    header = ["anio", "mes", "indicador", "valor", "unidad"]
    for column, value in enumerate(header):
        sheet.write(0, column, value)
    rows = [
        (2025, 1, "serie_mensual_sintetica", 100.00, "indice"),
        (2025, 2, "serie_mensual_sintetica", 100.42, "indice"),
        (2025, 3, "serie_mensual_sintetica", 100.91, "indice"),
    ]
    for index, row in enumerate(rows, start=1):
        for column, value in enumerate(row):
            sheet.write(index, column, value)
    book.save(str(path))

    entry = store.register_upload(
        "contrato.xls", path.read_bytes(), "contrato_mensual_xlsx", "cc-by"
    )
    result = engine.validate(entry["id"], write_receipt=False)
    assert result.coverage["complete"]
    assert [f.status for f in result.findings] == [OK] * len(result.findings)


def test_xls_con_hoja_inesperada_falla(tmp_path, sandbox):
    import xlwt

    from idt import store

    path = tmp_path / "otra.xls"
    book = xlwt.Workbook()
    sheet = book.add_sheet("Resumen")
    sheet.write(0, 0, "anio")
    sheet.write(1, 0, 2025)
    book.save(str(path))

    entry = store.register_upload(
        "otra.xls", path.read_bytes(), "contrato_mensual_xlsx", "cc-by"
    )
    result = engine.validate(entry["id"], write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "CONT-01")
    assert finding.status == FALLA
    assert finding.evidence["observed_sheets"] == ["Resumen"]


def test_csv_contra_perfil_de_libro_se_reporta(tmp_path, sandbox):
    from idt import store

    entry = store.register_upload(
        "contrato.csv",
        (config.ROOT / "review_store/fixtures/contrato_ok.csv").read_bytes(),
        "contrato_mensual_xlsx",
        "cc-by",
    )
    result = engine.validate(entry["id"], write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "CONT-01")
    assert finding.status == FALLA
    assert finding.evidence["observed_sheets"] == []
