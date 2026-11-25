from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from pipeline.suppression import (
    SUPPRESSION_THRESHOLD,
    is_small_count,
    suppress_count,
    suppress_counts,
    suppress_derived,
    suppression_metadata,
)


def test_threshold_is_five():
    assert SUPPRESSION_THRESHOLD == 5
    assert suppression_metadata()["threshold"] == 5


@pytest.mark.parametrize("value", [1, 2, 3, 4, 4.0])
def test_small_non_zero_counts_are_suppressed(value):
    published, suppressed = suppress_count(value)
    assert suppressed is True
    assert published is pd.NA


@pytest.mark.parametrize("value", [0, 5, 6, 1000])
def test_zero_and_counts_at_or_above_threshold_are_published(value):
    published, suppressed = suppress_count(value)
    assert suppressed is False
    assert published == value


def test_missing_values_are_not_treated_as_small_counts():
    assert is_small_count(np.nan) is False
    assert is_small_count(None) is False
    published, suppressed = suppress_count(np.nan)
    assert suppressed is False


def test_dataframe_suppression_flags_and_nulls():
    frame = pd.DataFrame(
        {
            "nacimientos_2025": [3, 0, 5, 28],
            "defunciones_2025": [1, 10, 2, 50],
            "defunciones_menores_5_2025": [0, 2, 9, 4],
            "escuelas_2022": [7, 8, 9, 10],
        }
    )
    result, summary = suppress_counts(frame)

    assert pd.isna(result.loc[0, "nacimientos_2025"])
    assert bool(result.loc[0, "nacimientos_2025_suprimido"]) is True
    assert result.loc[1, "nacimientos_2025"] == 0
    assert bool(result.loc[1, "nacimientos_2025_suprimido"]) is False
    assert pd.isna(result.loc[2, "defunciones_2025"])
    assert pd.isna(result.loc[3, "defunciones_menores_5_2025"])
    assert summary["suppressed_cells_total"] == 5
    assert summary["municipalities_with_suppression"] == 4
    assert summary["suppressed_cells_by_field"]["nacimientos_2025"] == 1


def test_derived_rate_is_withheld_when_component_is_suppressed():
    frame = pd.DataFrame(
        {
            "tasa_mortalidad_menor_5_2025": [20.0, 10.0],
            "defunciones_menores_5_2025_suprimido": [True, False],
            "nacimientos_2025_suprimido": [False, False],
        }
    )
    result, summary = suppress_derived(
        frame,
        {
            "tasa_mortalidad_menor_5_2025": (
                "defunciones_menores_5_2025",
                "nacimientos_2025",
            )
        },
    )
    assert pd.isna(result.loc[0, "tasa_mortalidad_menor_5_2025"])
    assert bool(result.loc[0, "tasa_mortalidad_menor_5_2025_suprimido"]) is True
    assert result.loc[1, "tasa_mortalidad_menor_5_2025"] == 10.0
    assert summary["suppressed_cells_total"] == 1
