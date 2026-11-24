"""Tests del prototipo. Se ejecutan con la biblioteca estándar:

python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from idt import config, gate  # noqa: E402
from idt.canonical import digest  # noqa: E402
from idt.engine import _basis_digest, validate  # noqa: E402
from idt.model import ADVERTENCIA, FALLA, NO_EVALUADO, OK, derive_state  # noqa: E402


class ContractTests(unittest.TestCase):
    def test_csv_correcto_pasa(self) -> None:
        result = validate("csv_ok", write_receipt=False)
        self.assertTrue(all(f.status == OK for f in result.findings))
        self.assertIn(result.state, ("en_revision", "habilitado_para_consulta"))

    def test_columna_faltante_falla(self) -> None:
        result = validate("csv_columna_faltante", write_receipt=False)
        finding = next(f for f in result.findings if f.rule_id == "CONT-02")
        self.assertEqual(finding.status, FALLA)
        self.assertIn("unidad", finding.evidence["missing_columns"])
        self.assertEqual(result.state, "no_habilitado")

    def test_grano_duplicado_falla(self) -> None:
        result = validate("csv_grano_duplicado", write_receipt=False)
        finding = next(f for f in result.findings if f.rule_id == "CONT-04")
        self.assertEqual(finding.status, FALLA)
        self.assertEqual(
            finding.evidence["duplicates"][0]["grain"],
            [2025, 2, "serie_mensual_sintetica"],
        )

    def test_hoja_inesperada_falla_y_no_es_no_evaluado(self) -> None:
        result = validate("xlsx_hoja_inesperada", write_receipt=False)
        finding = next(f for f in result.findings if f.rule_id == "CONT-01")
        self.assertEqual(finding.status, FALLA)
        self.assertEqual(finding.evidence["expected_sheet"], "Datos")
        self.assertIn("Resumen", finding.evidence["observed_sheets"])

    def test_segundo_perfil_declarativo_sin_tocar_el_motor(self) -> None:
        csv_result = validate("csv_ok", write_receipt=False)
        xlsx_result = validate("xlsx_ok", write_receipt=False)
        self.assertEqual(csv_result.method, xlsx_result.method)
        self.assertTrue(all(f.status == OK for f in xlsx_result.findings))
        self.assertEqual(xlsx_result.entity["profile"], "contrato-mensual-xlsx@1.0.0")

    def test_critica_no_evaluada_bloquea(self) -> None:
        result = validate("xlsx_hoja_inesperada", write_receipt=False)
        self.assertFalse(result.coverage["complete"])
        self.assertEqual(result.state, "no_habilitado")
        statuses = {f.status for f in result.findings}
        self.assertIn(NO_EVALUADO, statuses)


class IdentityTests(unittest.TestCase):
    def test_mismos_bytes_identidad_incompatible_falla(self) -> None:
        result = validate("dup_identidad", write_receipt=False)
        finding = next(f for f in result.findings if f.rule_id == "ID-01")
        self.assertEqual(finding.status, FALLA)
        self.assertTrue(result.entity["same_bytes"])
        self.assertEqual(
            finding.evidence["sha256"],
            config.manifest_item("fix-identidad-a")["sha256"],
        )
        self.assertEqual(result.state, "no_habilitado")

    def test_excepcion_documentada_pasa_a_advertencia(self) -> None:
        result = validate("dup_identidad_excepcion", write_receipt=False)
        finding = next(f for f in result.findings if f.rule_id == "ID-01")
        self.assertEqual(finding.status, ADVERTENCIA)
        self.assertTrue(finding.justified)
        self.assertEqual(finding.evidence["policy"]["policy"], "POL-DUP-2026-01")
        self.assertIn(result.state, ("en_revision", "habilitado_para_consulta"))

    def test_los_dos_fixtures_tienen_los_mismos_bytes(self) -> None:
        from idt.canonical import file_sha256

        a = file_sha256(config.FIXTURE_DIR / "identidad_a.csv")
        b = file_sha256(config.FIXTURE_DIR / "identidad_b.csv")
        self.assertEqual(a, b)


class IpcComparabilityTests(unittest.TestCase):
    def test_contrato_ipc_completo(self) -> None:
        result = validate("ipc_empalme", write_receipt=False)
        self.assertTrue(result.coverage["complete"])
        self.assertTrue(all(f.status == OK for f in result.findings))
        self.assertEqual(
            result.entity["sha256"],
            "d0101e366ee6d6bb02345db64b8c725c0a4c65ee85aa800d751d41b8381664d4",
        )

    def test_comparacion_valida_usa_la_variacion_publicada(self) -> None:
        result = validate("ipc_empalme", write_receipt=False)
        valid = next(c for c in result.comparisons if c.comparison_id == "F504/F503")
        self.assertEqual(valid.status, "ok")
        self.assertAlmostEqual(
            valid.public_evidence["computed_pct"], 0.501463, places=6
        )
        self.assertAlmostEqual(
            valid.public_evidence["published_pct"], 0.501463, places=6
        )
        self.assertEqual(valid.public_evidence["published_cell"], "G504")

    def test_comparacion_invalida_se_bloquea(self) -> None:
        result = validate("ipc_empalme", write_receipt=False)
        blocked = next(c for c in result.comparisons if c.comparison_id == "F504/E503")
        self.assertEqual(blocked.status, "bloqueada")
        self.assertAlmostEqual(
            blocked.private_evidence["computed_pct"], -0.673802, places=6
        )
        self.assertFalse(blocked.private_evidence["display_public"])

    def test_el_numero_invalido_no_entra_en_la_evidencia_publica(self) -> None:
        result = validate("ipc_empalme", write_receipt=False)
        public = json.dumps(result.to_public_dict(), ensure_ascii=False)
        self.assertNotIn("0.6738", public)
        self.assertNotIn("0,67", public)
        blocked = next(c for c in result.comparisons if c.comparison_id == "F504/E503")
        self.assertNotIn("computed_pct", blocked.public_evidence)


class StateTests(unittest.TestCase):
    def test_estado_sin_licencia_es_cerrado(self) -> None:
        state = derive_state(
            [], license_verified=False, gate_approved=False, warnings_justified=True
        )
        self.assertEqual(state, "cerrado")

    def test_estado_con_falla_critica_es_no_habilitado(self) -> None:
        from idt.model import Finding

        finding = Finding("X-01", "t", FALLA, True, "m")
        state = derive_state([finding], True, True, True)
        self.assertEqual(state, "no_habilitado")

    def test_estado_con_todo_ok_y_gate_es_habilitado(self) -> None:
        from idt.model import Finding

        finding = Finding("X-01", "t", OK, True, "m")
        self.assertEqual(
            derive_state([finding], True, True, True), "habilitado_para_consulta"
        )
        self.assertEqual(derive_state([finding], True, False, True), "en_revision")

    def test_advertencia_sin_justificar_deja_en_revision(self) -> None:
        from idt.model import Finding

        warning = Finding("X-01", "t", ADVERTENCIA, True, "m", justified=False)
        self.assertEqual(derive_state([warning], True, True, False), "en_revision")


class DigestTests(unittest.TestCase):
    def test_dos_ejecuciones_dan_el_mismo_digest(self) -> None:
        first = validate("ipc_empalme", write_receipt=False)
        second = validate("ipc_empalme", write_receipt=False)
        self.assertEqual(
            first.digests["validation_digest"], second.digests["validation_digest"]
        )

    def test_el_digest_cambia_si_cambia_el_perfil(self) -> None:
        result = validate("ipc_empalme", write_receipt=False)
        rules = config.load_rules()
        profile = config.load_profile("ipc-empalme-rep")
        files = {"ine-ipc-empalme": result.entity["sha256"]}

        other = json.loads(json.dumps(profile))
        other["version"] = "1.0.1"

        base = _basis_digest(files, profile, rules, result.findings)
        changed = _basis_digest(files, other, rules, result.findings)
        self.assertNotEqual(base, changed)

    def test_el_digest_no_depende_de_timestamps(self) -> None:
        result = validate("ipc_empalme", write_receipt=False)
        payload = json.dumps(result.to_public_dict(), sort_keys=True)
        self.assertNotIn("generated_at_utc", payload)
        self.assertNotIn("decided_at_utc", payload)


class GateTests(unittest.TestCase):
    def test_el_gate_rechaza_un_caso_con_falla(self) -> None:
        result = validate("dup_identidad", write_receipt=False)
        problems = gate.preconditions(result)
        self.assertTrue(any("ID-01" in p for p in problems))

    def test_el_gate_acepta_la_excepcion_justificada(self) -> None:
        result = validate("dup_identidad_excepcion", write_receipt=False)
        self.assertEqual(gate.preconditions(result), [])

    def test_el_gate_rechaza_reglas_criticas_no_evaluadas(self) -> None:
        result = validate("xlsx_hoja_inesperada", write_receipt=False)
        problems = gate.preconditions(result)
        self.assertTrue(
            any("no_evaluado" in p or "no evaluadas" in p for p in problems)
        )

    def test_decisiones_registradas_siguen_vigentes(self) -> None:
        report = gate.verify()
        for entry in report:
            if entry["decision"]:
                self.assertTrue(
                    entry["decision_valid"],
                    f"la decisión de {entry['case_id']} quedó invalidada",
                )

    def test_verify_no_retira_agregados_sostenidos(self) -> None:
        report = gate.verify()
        self.assertFalse([e for e in report if e["quarantined"]])
        for entry in report:
            if entry["decision_valid"]:
                self.assertTrue(entry["in_public_snapshot"], entry["case_id"])


class SeparationTests(unittest.TestCase):
    def test_el_snapshot_publico_no_contiene_evidencia_privada(self) -> None:
        directory = config.PUBLIC_DIR / "aggregates"
        for path in directory.glob("*.json"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("private_evidence", text)
            self.assertNotIn("review_store", text)

    def test_el_agregado_publico_del_ipc_no_muestra_el_numero_invalido(self) -> None:
        path = config.PUBLIC_DIR / "aggregates" / "ipc_empalme.json"
        text = path.read_text(encoding="utf-8")
        self.assertNotIn("0.6738", text)
        self.assertNotIn("0,67", text)

    def test_el_motor_no_usa_red(self) -> None:
        for path in (ROOT / "idt").glob("*.py"):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("urllib", source, f"{path.name} importa urllib")
            self.assertNotIn("requests", source, f"{path.name} importa requests")
            self.assertNotIn("socket", source, f"{path.name} usa socket")

    def test_la_lista_es_cerrada(self) -> None:
        ids = [case["id"] for case in config.load_cases()]
        self.assertEqual(len(ids), len(set(ids)))
        for case in config.load_cases():
            self.assertNotIn("url", case)


class FixtureTests(unittest.TestCase):
    def test_los_fixtures_se_rotulan_como_sinteticos(self) -> None:
        for item in config.load_manifest()["items"]:
            if item["id"].startswith("fix-"):
                self.assertTrue(item["synthetic"], item["id"])
                self.assertIn("sintético", item["license"]["attribution"].lower())

    def test_el_recurso_real_conserva_su_licencia(self) -> None:
        item = config.manifest_item("ine-ipc-empalme")
        self.assertEqual(item["license"]["id"], "cc-by")
        self.assertTrue(item["license"]["verified"])
        self.assertEqual(item["bytes"], 68016)

    def test_el_manifiesto_es_coherente_con_los_bytes(self) -> None:
        from idt.canonical import file_sha256

        for item in config.load_manifest()["items"]:
            path = ROOT / item["path"]
            self.assertEqual(file_sha256(path), item["sha256"], item["id"])


class ReceiptTests(unittest.TestCase):
    def test_el_recibo_separa_payload_y_bitacora(self) -> None:
        validate("ipc_empalme", write_receipt=True)
        path = config.RECEIPT_DIR / "ipc_empalme.json"
        receipt = json.loads(path.read_text(encoding="utf-8"))
        self.assertIn("technical_payload", receipt)
        self.assertIn("decision_log", receipt)
        self.assertEqual(
            receipt["technical_payload"]["digest"],
            validate("ipc_empalme", write_receipt=False).digests["validation_digest"],
        )

    def test_dos_recibos_conservan_el_mismo_digest_tecnico(self) -> None:
        first = json.loads(
            (config.RECEIPT_DIR / "ipc_empalme.json").read_text(encoding="utf-8")
        )
        validate("ipc_empalme", write_receipt=True)
        second = json.loads(
            (config.RECEIPT_DIR / "ipc_empalme.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            first["technical_payload"]["digest"],
            second["technical_payload"]["digest"],
        )
        self.assertEqual(
            digest(first["technical_payload"]), digest(second["technical_payload"])
        )


if __name__ == "__main__":
    unittest.main()
