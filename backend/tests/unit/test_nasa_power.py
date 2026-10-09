import json
from pathlib import Path

import httpx
import pytest

from app.core.config import Settings
from app.core.errors import PowerClientError
from app.services.nasa_power import NasaPowerClient

FIXTURE = Path(__file__).parents[1] / "fixtures" / "power_regional_t2m_2020.json"


def test_regional_request_rejects_boxes_smaller_than_two_degrees(tmp_path: Path) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise AssertionError("A too-small regional box must not call NASA POWER.")

    client = NasaPowerClient(
        settings=Settings(data_dir=tmp_path, cache_enabled=False),
        http=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(PowerClientError, match="2 degree"):
        client.fetch_regional_monthly(
            "T2M",
            start_year=2020,
            end_year=2020,
            latitude_min=16.5,
            latitude_max=17.0,
            longitude_min=96.0,
            longitude_max=98.5,
        )


def test_regional_request_caches_a_successful_response(tmp_path: Path) -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    calls = {"count": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(200, json=payload)

    settings = Settings(data_dir=tmp_path, cache_enabled=True, cache_ttl_seconds=3600)
    client = NasaPowerClient(
        settings=settings,
        http=httpx.Client(transport=httpx.MockTransport(handler)),
    )
    kwargs = {
        "start_year": 2020,
        "end_year": 2020,
        "latitude_min": 16,
        "latitude_max": 18,
        "longitude_min": 96,
        "longitude_max": 98,
    }
    first = client.fetch_regional_monthly("T2M", **kwargs)
    second = client.fetch_regional_monthly("T2M", **kwargs)

    assert first["parameters"]["T2M"]["units"] == "C"
    assert second["parameters"]["T2M"]["units"] == "C"
    assert calls["count"] == 1
    assert list(tmp_path.joinpath("raw").glob("*.json"))


def test_unknown_parameter_is_rejected(tmp_path: Path) -> None:
    client = NasaPowerClient(settings=Settings(data_dir=tmp_path, cache_enabled=False))
    with pytest.raises(PowerClientError, match="not allowed"):
        client.fetch_point_monthly(
            "NOT_A_PARAMETER",
            latitude=16.8,
            longitude=96.1,
            start_year=2020,
            end_year=2020,
        )
