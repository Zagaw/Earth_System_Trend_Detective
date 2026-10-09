import json
from urllib.parse import urlencode

import httpx

from app.core.config import Settings, get_settings
from app.core.errors import PowerClientError
from app.core.variables import REGIONAL_MINIMUM_SPAN_DEGREES, SOURCE_PARAMETERS
from app.repositories.cache import raw_cache_file, read_fresh_cache, write_cache


class NasaPowerClient:
    def __init__(
        self,
        settings: Settings | None = None,
        http: httpx.Client | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._http = http

    def fetch_regional_monthly(
        self,
        parameter: str,
        *,
        start_year: int,
        end_year: int,
        latitude_min: float,
        latitude_max: float,
        longitude_min: float,
        longitude_max: float,
        community: str | None = None,
    ) -> dict:
        self._require_parameter(parameter)
        if end_year < start_year:
            raise PowerClientError("end_year must be greater than or equal to start_year.")
        if latitude_max - latitude_min < REGIONAL_MINIMUM_SPAN_DEGREES:
            raise PowerClientError(
                "NASA POWER regional requests need at least a 2 degree latitude range."
            )
        if longitude_max - longitude_min < REGIONAL_MINIMUM_SPAN_DEGREES:
            raise PowerClientError(
                "NASA POWER regional requests need at least a 2 degree longitude range."
            )

        selected_community = community or self.settings.nasa_power_community
        query = {
            "latitude-min": latitude_min,
            "latitude-max": latitude_max,
            "longitude-min": longitude_min,
            "longitude-max": longitude_max,
            "parameters": parameter,
            "community": selected_community,
            "start": start_year,
            "end": end_year,
            "format": "JSON",
        }
        identity = {
            "endpoint": "temporal/monthly/regional",
            "parameter": parameter,
            "community": selected_community,
            "start": start_year,
            "end": end_year,
            "latitude_min": latitude_min,
            "latitude_max": latitude_max,
            "longitude_min": longitude_min,
            "longitude_max": longitude_max,
            "processing_version": self.settings.processing_version,
        }
        return self._fetch("temporal/monthly/regional", query, identity)

    def fetch_study_grid(self, parameter: str, *, start_year: int, end_year: int) -> dict:
        """Download the configured study area in tiles that respect the 10 degree API limit."""
        merged: dict | None = None
        seen: set[tuple[float, float]] = set()
        features: list[dict] = []
        for latitude_min, latitude_max, longitude_min, longitude_max in _tiles(
            self.settings.latitude_min,
            self.settings.latitude_max,
            self.settings.longitude_min,
            self.settings.longitude_max,
        ):
            payload = self.fetch_regional_monthly(
                parameter,
                start_year=start_year,
                end_year=end_year,
                latitude_min=latitude_min,
                latitude_max=latitude_max,
                longitude_min=longitude_min,
                longitude_max=longitude_max,
            )
            if merged is None:
                merged = payload
            for feature in payload.get("features") or []:
                coordinates = feature.get("geometry", {}).get("coordinates") or []
                if len(coordinates) < 2:
                    continue
                key = (round(float(coordinates[1]), 4), round(float(coordinates[0]), 4))
                if key in seen:
                    continue
                seen.add(key)
                features.append(feature)
        if merged is None:
            raise PowerClientError("The study area did not produce a NASA POWER tile.")
        merged = dict(merged)
        merged["features"] = features
        merged["type"] = "FeatureCollection"
        return merged

    def fetch_point_monthly(
        self,
        parameter: str,
        *,
        latitude: float,
        longitude: float,
        start_year: int,
        end_year: int,
        community: str | None = None,
    ) -> dict:
        self._require_parameter(parameter)
        selected_community = community or self.settings.nasa_power_community
        query = {
            "parameters": parameter,
            "community": selected_community,
            "longitude": longitude,
            "latitude": latitude,
            "start": start_year,
            "end": end_year,
            "format": "JSON",
        }
        identity = {
            "endpoint": "temporal/monthly/point",
            "parameter": parameter,
            "community": selected_community,
            "latitude": latitude,
            "longitude": longitude,
            "start": start_year,
            "end": end_year,
            "processing_version": self.settings.processing_version,
        }
        return self._fetch("temporal/monthly/point", query, identity)

    def _fetch(self, path: str, query: dict[str, object], identity: dict[str, object]) -> dict:
        cache_path = raw_cache_file(self.settings, identity)
        if self.settings.cache_enabled:
            cached = read_fresh_cache(cache_path, self.settings.cache_ttl_seconds)
            if cached is not None:
                return cached

        url = f"{self.settings.nasa_power_base_url.rstrip('/')}/{path}?{urlencode(query)}"
        payload = self._get_json(url)
        if self.settings.cache_enabled:
            write_cache(cache_path, payload)
        return payload

    def _get_json(self, url: str) -> dict:
        last_error: Exception | None = None
        attempts = self.settings.nasa_max_retries
        for attempt in range(1, attempts + 1):
            try:
                response = self._request(url)
            except httpx.TimeoutException as exc:
                last_error = exc
                continue
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt == attempts:
                    break
                continue

            if response.status_code in {429, 500, 502, 503, 504} and attempt < attempts:
                last_error = PowerClientError(
                    f"NASA POWER returned HTTP {response.status_code}.",
                    status_code=response.status_code,
                )
                continue

            if response.status_code >= 400:
                raise PowerClientError(
                    _error_message(response),
                    status_code=response.status_code,
                )

            try:
                payload = response.json()
            except json.JSONDecodeError as exc:
                raise PowerClientError("NASA POWER returned a response that is not JSON.") from exc
            if not isinstance(payload, dict):
                raise PowerClientError("NASA POWER JSON response was not an object.")
            return payload

        raise PowerClientError(f"NASA POWER request failed: {last_error}")

    def _request(self, url: str) -> httpx.Response:
        if self._http is not None:
            return self._http.get(url)
        with httpx.Client(timeout=self.settings.nasa_timeout_seconds) as client:
            return client.get(url)

    @staticmethod
    def _require_parameter(parameter: str) -> None:
        if parameter not in SOURCE_PARAMETERS:
            allowed = ", ".join(sorted(SOURCE_PARAMETERS))
            raise PowerClientError(
                f"Parameter {parameter} is not allowed. Use one of: {allowed}."
            )


def _tiles(
    latitude_min: float,
    latitude_max: float,
    longitude_min: float,
    longitude_max: float,
    maximum_span: float = 10,
) -> list[tuple[float, float, float, float]]:
    tiles: list[tuple[float, float, float, float]] = []
    latitude = latitude_min
    while latitude < latitude_max:
        next_latitude = min(latitude + maximum_span, latitude_max)
        longitude = longitude_min
        while longitude < longitude_max:
            next_longitude = min(longitude + maximum_span, longitude_max)
            tiles.append((latitude, next_latitude, longitude, next_longitude))
            if next_longitude >= longitude_max:
                break
            longitude = next_longitude + 0.01
        if next_latitude >= latitude_max:
            break
        latitude = next_latitude + 0.01
    return tiles


def _error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return f"NASA POWER returned HTTP {response.status_code}."
    messages = payload.get("messages") if isinstance(payload, dict) else None
    if isinstance(messages, list) and messages:
        return " ".join(str(item) for item in messages)
    return f"NASA POWER returned HTTP {response.status_code}."
