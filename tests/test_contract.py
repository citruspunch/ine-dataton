"""P0.1: contract of schema, type, grain, period, unit and base."""

from __future__ import annotations

import pytest

from engine import config, rules
from engine.model import WARNING, FAILURE, NOT_EVALUATED, OK


def test_valid_csv_passes():
    result = rules.validate("csv_ok", write_receipt=False)
    assert [f.status for f in result.findings] == [OK] * len(result.findings)
    assert result.coverage["complete"]


def test_missing_column_fails():
    result = rules.validate("csv_columna_faltante", write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "CONT-02")
    assert finding.status == FAILURE
    assert finding.evidence["missing_columns"] == ["unidad"]
    assert result.state == "no_habilitado"


def test_duplicate_grain_fails():
    result = rules.validate("csv_grano_duplicado", write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "CONT-04")
    assert finding.status == FAILURE
    assert finding.evidence["duplicates"][0]["grain"] == [
        2025,
        2,
        "serie_mensual_sintetica",
    ]


def test_unexpected_sheet_fails_and_is_not_not_evaluated():
    result = rules.validate("xlsx_hoja_inesperada", write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "CONT-01")
    assert finding.status == FAILURE
    assert finding.evidence["expected_sheet"] == "Datos"
    assert "Resumen" in finding.evidence["observed_sheets"]


def test_not_evaluated_critical_blocks():
    result = rules.validate("xlsx_hoja_inesperada", write_receipt=False)
    assert not result.coverage["complete"]
    assert result.state == "no_habilitado"
    assert any(f.status == NOT_EVALUATED for f in result.findings)


def test_second_declarative_profile_without_touching_engine():
    csv_result = rules.validate("csv_ok", write_receipt=False)
    xlsx_result = rules.validate("xlsx_ok", write_receipt=False)
    assert csv_result.method == xlsx_result.method == "contract"
    assert [f.status for f in xlsx_result.findings] == [OK] * len(xlsx_result.findings)
    assert xlsx_result.entity["profile"] == "contrato_mensual_xlsx_v1@2.0.0"


def test_second_real_resource_with_different_shape():
    """The regional profile uses a wide table and a period range."""
    result = rules.validate("ipc_regional", write_receipt=False)
    assert result.coverage["complete"]
    assert [f.status for f in result.findings] == [OK] * len(result.findings)
    summary = result.entity["variables_summary"]
    assert summary["row_count"] == 22
    assert len(summary["columns"]) == 11
    regional = next(c for c in summary["columns"] if c["name"] == "region_1")
    assert regional["unit"] == "índice"
    assert regional["reference"] == "2024=100"
    assert regional["valid_count"] == 22


def test_profiles_declare_no_fixed_coordinates():
    """Decoupling: neither rows nor column letters in the profiles."""
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


def test_evidence_records_cell_as_metadata():
    result = rules.validate("ipc_empalme", write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "CONT-02")
    cells = {
        item["column"]: item["cell_column"] for item in finding.evidence["columns"]
    }
    assert cells["Variación Mensual e/"] == "G"
    assert cells["Índice año Base  2024=100.00 d/"] == "F"


def test_unreadable_csv_is_not_evaluated(sandbox):
    from engine import store

    entry = store.register_upload(
        "roto.csv", b"\xff\xfe\x00binario", "contrato_mensual_v1", "cc-by"
    )
    result = rules.validate(entry["id"], write_receipt=False)
    assert result.state == "no_habilitado"
    assert not result.coverage["complete"]
    assert all(
        f.status == NOT_EVALUATED
        for f in result.findings
        if f.rule_id.startswith("CONT")
    )


def test_legacy_xls_is_read_and_validated(tmp_path, sandbox):
    """The legacy .xls format is read with xlrd, not rejected."""
    import xlwt

    from engine import store

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
        "contrato.xls", path.read_bytes(), "contrato_mensual_xlsx_v1", "cc-by"
    )
    result = rules.validate(entry["id"], write_receipt=False)
    assert result.coverage["complete"]
    assert [f.status for f in result.findings] == [OK] * len(result.findings)


def test_xls_with_unexpected_sheet_fails(tmp_path, sandbox):
    import xlwt

    from engine import store

    path = tmp_path / "otra.xls"
    book = xlwt.Workbook()
    sheet = book.add_sheet("Resumen")
    sheet.write(0, 0, "anio")
    sheet.write(1, 0, 2025)
    book.save(str(path))

    entry = store.register_upload(
        "otra.xls", path.read_bytes(), "contrato_mensual_xlsx_v1", "cc-by"
    )
    result = rules.validate(entry["id"], write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "CONT-01")
    assert finding.status == FAILURE
    assert finding.evidence["observed_sheets"] == ["Resumen"]


def test_csv_against_workbook_profile_is_reported(tmp_path, sandbox):
    from engine import store

    entry = store.register_upload(
        "contrato.csv",
        (config.FIXTURE_DIR / "contrato_ok.csv").read_bytes(),
        "contrato_mensual_xlsx_v1",
        "cc-by",
    )
    result = rules.validate(entry["id"], write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "CONT-01")
    assert finding.status == FAILURE
    assert finding.evidence["observed_sheets"] == []
