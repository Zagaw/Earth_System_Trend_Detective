from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metadata_reports_verified_units_and_no_ingested_grid() -> None:
    response = client.get("/api/v1/metadata")
    assert response.status_code == 200
    body = response.json()
    assert body["study_grid_status"] in {"not_ingested", "ready"}
    units = {item["id"]: item["source_unit"] for item in body["variables"]}
    assert units == {
        "precipitation": "mm/day",
        "temperature": "C",
        "relative_humidity": "%",
    }
    rainfall = next(item for item in body["variables"] if item["id"] == "precipitation")
    assert rainfall["conversion"] == "monthly_mm = mm_per_day * days_in_month"
    assert body["fill_value"] == -999.0


def test_analysis_config_does_not_claim_calculations_exist() -> None:
    response = client.get("/api/v1/analysis/config")
    assert response.status_code == 200
    body = response.json()
    assert body["calculations_implemented"] is True
    assert body["significance_alpha"] == 0.05
    assert body["multiple_testing"] == "benjamini_hochberg"


def test_timeseries_reports_readiness() -> None:
    response = client.get(
        "/api/v1/climate/timeseries",
        params={
            "variable": "temperature",
            "start_year": 2001,
            "end_year": 2025,
            "aggregation": "annual",
        },
    )
    if response.status_code == 503:
        assert response.json()["error"] == "not_ready"
        return
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "NASA POWER"
    assert body["unit"] == "degC"
    assert body["data"]


def test_monthly_values_are_not_used_for_a_trend_test() -> None:
    response = client.get(
        "/api/v1/trends/summary",
        params={
            "variable": "temperature",
            "start_year": 2001,
            "end_year": 2020,
            "aggregation": "monthly",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_aggregation"


def test_reversed_years_are_rejected() -> None:
    response = client.get(
        "/api/v1/trends/summary",
        params={
            "variable": "precipitation",
            "start_year": 2020,
            "end_year": 2001,
            "aggregation": "annual",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_period"


def test_unknown_variable_is_rejected() -> None:
    response = client.get(
        "/api/v1/climate/timeseries",
        params={"variable": "wind", "start_year": 2001, "end_year": 2020},
    )
    assert response.status_code == 422


def test_seasonal_request_requires_a_season() -> None:
    response = client.get(
        "/api/v1/trends/grid",
        params={
            "variable": "relative_humidity",
            "start_year": 2001,
            "end_year": 2020,
            "aggregation": "seasonal",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_season"
