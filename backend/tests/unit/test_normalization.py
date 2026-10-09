import json
from pathlib import Path

import pytest

from app.core.errors import NormalizationError
from app.services.normalization import parse_power_response

FIXTURE = Path(__file__).parents[1] / "fixtures" / "power_regional_t2m_2020.json"


def test_regional_fixture_parses_monthly_values_and_excludes_api_annual_keys() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    parsed = parse_power_response(payload, "T2M")

    assert parsed.variable == "temperature"
    assert parsed.source_unit == "C"
    assert parsed.feature_count == 15
    assert len(parsed.observations) == 180
    assert len(parsed.annual_statistics) == 15
    assert {item.month for item in parsed.observations} == set(range(1, 13))
    assert all(item.data_quality_status == "valid" for item in parsed.observations)
    assert parsed.observations[0].elevation_m is not None


def test_fill_value_is_missing_and_zero_precipitation_stays_valid() -> None:
    payload = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [96.1, 16.8, 12.0]},
        "properties": {
            "parameter": {
                "PRECTOTCORR": {
                    "202001": 0.0,
                    "202002": -999.0,
                    "202013": 1.5,
                }
            }
        },
        "header": {"fill_value": -999.0, "sources": ["MERRA2"]},
        "parameters": {
            "PRECTOTCORR": {"units": "mm/day", "longname": "Precipitation Corrected"}
        },
        "messages": [],
    }
    parsed = parse_power_response(payload, "PRECTOTCORR")
    by_month = {item.month: item for item in parsed.observations}

    assert by_month[1].value == 0.0
    assert by_month[1].data_quality_status == "valid"
    assert by_month[2].value is None
    assert by_month[2].data_quality_status == "missing"
    assert parsed.annual_statistics[0].year == 2020
    assert parsed.annual_statistics[0].value == 1.5
    assert parsed.variable == "precipitation"


def test_unexpected_unit_fails_instead_of_being_converted_silently() -> None:
    payload = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [96.1, 16.8]},
        "properties": {"parameter": {"T2M": {"202001": 300.0}}},
        "header": {"fill_value": -999},
        "parameters": {"T2M": {"units": "K", "longname": "Temperature at 2 Meters"}},
        "messages": [],
    }
    with pytest.raises(NormalizationError, match="expected verified unit"):
        parse_power_response(payload, "T2M")
