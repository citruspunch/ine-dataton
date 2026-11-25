"""Shared vocabulary: CIIU sections, size classes and recoding notices."""

from __future__ import annotations

# CIIU Rev. 4 sections. `name` is the exact label used by DINESE; `short` is a
# reading aid for charts and never replaces the official label in tooltips.
CIIU_SECTIONS = (
    ("A", "Agricultura, ganadería, silvicultura y pesca", "Agricultura y pesca"),
    ("B", "Explotación de minas y canteras", "Minas y canteras"),
    ("C", "Industrias manufactureras", "Industrias manufactureras"),
    (
        "D",
        "Suministro de electricidad, gas, vapor y aire acondicionado",
        "Electricidad y gas",
    ),
    (
        "E",
        "Suministro de agua; evacuación de aguas residuales, gestión de desechos y descontaminación",
        "Agua y desechos",
    ),
    ("F", "Construcción", "Construcción"),
    (
        "G",
        "Comercio al por mayor y al por menor; reparación de vehículos automotores y motocicletas",
        "Comercio y reparación",
    ),
    ("H", "Transporte y almacenamiento", "Transporte y almacenamiento"),
    (
        "I",
        "Actividades de alojamiento y de servicio de comidas",
        "Alojamiento y comidas",
    ),
    ("J", "Información y comunicaciones", "Información y comunicaciones"),
    ("K", "Actividades financieras y de seguros", "Finanzas y seguros"),
    ("L", "Actividades inmobiliarias", "Actividades inmobiliarias"),
    (
        "M",
        "Actividades profesionales, científicas y técnicas",
        "Servicios profesionales",
    ),
    (
        "N",
        "Actividades de servicios administrativos y de apoyo",
        "Servicios administrativos",
    ),
    (
        "O",
        "Administración pública y defensa; planes de seguridad social de afiliación obligatoria",
        "Administración pública",
    ),
    ("P", "Enseñanza", "Enseñanza"),
    (
        "Q",
        "Actividades de atención de la salud humana y de asistencia social",
        "Salud y asistencia social",
    ),
    (
        "R",
        "Actividades artísticas, de entretenimiento y recreativas",
        "Arte y recreación",
    ),
    ("S", "Otras actividades de servicios", "Otros servicios"),
    (
        "T",
        "Actividades de los hogares como empleadores; actividades no diferenciadas de los hogares como productores de bienes y servicios para uso propio",
        "Hogares como empleadores",
    ),
    (
        "U",
        "Actividades de organizaciones y órganos extraterritoriales",
        "Organismos extraterritoriales",
    ),
)

CIIU_BY_NAME = {
    name: {"letter": letter, "short": short} for letter, name, short in CIIU_SECTIONS
}

SIZE_ORDER = ("Micro", "Pequeña", "Mediana", "Grande")

SIZE_LABELS = {
    "Micro": "Micro",
    "Pequeña": "Pequeña",
    "Mediana": "Mediana",
    "Grande": "Grande",
}

# Age group labels in the census table, in order. Kept explicit so the output
# does not depend on spreadsheet header formatting (e.g. "70  - 74").
AGE_GROUPS = (
    "0–4",
    "5–9",
    "10–14",
    "15–19",
    "20–24",
    "25–29",
    "30–34",
    "35–39",
    "40–44",
    "45–49",
    "50–54",
    "55–59",
    "60–64",
    "65–69",
    "70–74",
    "75–79",
    "80–84",
    "85–89",
    "90–94",
    "95–99",
    "100+",
)

CENSUS_AGE_COLUMNS = tuple(f"a{i}" for i in range(len(AGE_GROUPS)))

VIEW_SNAPSHOT = "2024"
VIEW_SERIES = "series"


def _fmt(n: int) -> str:
    return f"{n:,}".replace(",", ",")


def build_notices(totals: dict[int, int], legal_counts: dict[int, int]) -> dict:
    """Return the two non-comparability notices, with live figures."""
    t21 = totals[2021]
    t22 = totals[2022]
    t24 = totals[2024]
    jump = (t24 - t21) / t21 * 100
    series_change = (t22 - t21) / t21 * 100

    return {
        "2024": {
            "id": "2024",
            "label": "Corte 2024",
            "severity": "warning",
            "badges": [
                f"{_fmt(t24)} registros",
                f"+{jump:.1f} % vs. 2021",
                f"{legal_counts[2024]} categorías",
            ],
            "title": "Corte transversal 2024: no lo interpretes como crecimiento",
            "body": (
                f"DINESE 2024 contiene {_fmt(t24)} registros, frente a {_fmt(t21)} en 2021 "
                f"(+{jump:.1f} %). El salto refleja cambios de cobertura y captación, no "
                "necesariamente crecimiento económico. La personería jurídica también se "
                f"recodificó: de {legal_counts[2021]} categorías en 2021 y "
                f"{legal_counts[2022]} en 2022 a {legal_counts[2024]} en 2024. Por eso esta "
                "vista es un corte transversal y no una serie de crecimiento."
            ),
            "footnote": (
                "Compara solo dentro de 2024. No calculamos variaciones 2021→2024 ni "
                "emparejamos personerías entre años."
            ),
        },
        "series": {
            "id": "series",
            "label": "Serie 2021–2022",
            "severity": "info",
            "badges": [
                f"2021: {_fmt(t21)}",
                f"2022: {_fmt(t22)}",
                f"{legal_counts[2021]} / {legal_counts[2022]} categorías",
            ],
            "title": "Serie 2021–2022: comparable entre sí, no con 2024",
            "body": (
                f"Entre 2021 ({_fmt(t21)}) y 2022 ({_fmt(t22)}) los registros cambian "
                f"{series_change:+.1f} %. Esta serie corta se puede leer año contra año, "
                "pero no debe extenderse a 2024: la cobertura pasó a "
                f"{_fmt(t24)} registros y la personería se recodificó a "
                f"{legal_counts[2024]} categorías. Los conteos son establecimientos "
                "registrados, no empleo, ventas ni número de personas trabajadoras."
            ),
            "footnote": (
                "Las etiquetas de personería se muestran tal como aparecen en cada año; "
                "no se fuerza una equivalencia entre 2021 y 2022."
            ),
        },
    }
