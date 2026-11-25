"""Pipeline orchestration."""

from __future__ import annotations

from pathlib import Path

from .aggregate import (
    build_catalog,
    build_manifest,
    build_summary,
    mark_duplicates,
)
from .baskets import load_baskets
from .config import (
    DOWNLOADS_MANIFEST,
    GROUP_META,
    RAW_DIR,
    SOURCE_GROUP_ORDER,
    SOURCES,
)
from .download import acquire_all
from .dpir import dictionary_entries, load_dpir
from .export import write_outputs
from .icc import load_icc
from .ipmc import load_ipmc
from .provenance import load_manifest, sha256_file


def build(force_download: bool = False, offline: bool = False) -> dict:
    """Acquire missing inputs, parse them, and write processed artifacts."""

    if offline:
        missing = [spec.filename for spec in SOURCES.values() if not spec.path.exists()]
        if missing:
            raise FileNotFoundError(
                "Modo sin conexión: faltan archivos locales " + ", ".join(missing)
            )
        downloads = load_manifest()
    else:
        downloads, errors = acquire_all(SOURCES, force=force_download)
        if errors:
            raise RuntimeError(
                "No se pudieron obtener todos los archivos oficiales:\n- " + "\n- ".join(errors)
            )

    specs = list(SOURCES.values())
    dpir_specs = [spec for spec in specs if spec.group == "DPIR" and not spec.dictionary]
    ipmc_specs = [spec for spec in specs if spec.group == "IPMC" and not spec.dictionary]
    icc_specs = [spec for spec in specs if spec.group == "ICC" and not spec.dictionary]
    basket_specs = [spec for spec in specs if spec.group == "BASKETS"]

    records = []
    records.extend(load_dpir(dpir_specs, RAW_DIR))
    for spec in ipmc_specs:
        records.extend(load_ipmc(spec, RAW_DIR))
    for spec in icc_specs:
        records.extend(load_icc(spec, RAW_DIR))
    records.extend(load_baskets(basket_specs, RAW_DIR))

    records = mark_duplicates(records)
    summary = build_summary(records)
    catalog = build_catalog(records)
    dictionary = dictionary_entries(RAW_DIR / "diccionario-pr.xlsx")
    manifest = build_manifest(records, SOURCES, downloads, dictionary)
    paths = write_outputs(
        records,
        summary,
        manifest,
        catalog,
        dictionary,
        list(SOURCE_GROUP_ORDER),
    )

    print("\nResumen de datos procesados")
    print("-" * 78)
    for group in SOURCE_GROUP_ORDER:
        info = summary["groups"][group]
        cutoff = info["cutoff"] or "sin fecha válida"
        print(
            f"{GROUP_META[group]['shortLabel']:<12} {info['recordCount']:>7,} registros  "
            f"{info['canonicalCount']:>7,} en resúmenes  corte: {cutoff}"
        )
        for metric in info["metrics"]:
            print(
                f"  · {metric['metric']}: n={metric['count']:,}, "
                f"min={metric['min']:,.2f}, mediana={metric['median']:,.2f}, "
                f"max={metric['max']:,.2f} [{metric['unit']}]"
            )
    print("-" * 78)
    print(f"Parquet: {paths['parquet']}")
    print(f"Web:     {paths['summary'].parent}")
    return {"records": records, "summary": summary, "manifest": manifest, "paths": paths}


def verify() -> list[str]:
    """Check that cached files still match their recorded SHA-256."""

    manifest = load_manifest()
    problems: list[str] = []
    for dataset_id, entry in manifest.get("datasets", {}).items():
        path = Path(entry.get("path", ""))
        if not path.is_absolute():
            path = Path.cwd() / path
        if not path.exists():
            # Fall back to the canonical raw location.
            path = RAW_DIR / entry.get("fileName", "")
        if not path.exists():
            problems.append(f"{dataset_id}: no existe {path}")
            continue
        actual = sha256_file(path)
        if actual != entry.get("sha256"):
            problems.append(
                f"{dataset_id}: SHA-256 no coincide (esperado {entry.get('sha256')}, real {actual})"
            )
    if not DOWNLOADS_MANIFEST.exists():
        problems.append(f"No existe el manifiesto {DOWNLOADS_MANIFEST}")
    return problems
