from dataclasses import dataclass

from app.core.errors import NormalizationError
from app.core.variables import SOURCE_PARAMETERS


@dataclass(frozen=True)
class MonthlyObservation:
    grid_id: str
    latitude: float
    longitude: float
    elevation_m: float | None
    year: int
    month: int
    variable: str
    value: float | None
    source_unit: str
    source_parameter: str
    data_quality_status: str


@dataclass(frozen=True)
class AnnualApiStatistic:
    """API month-code 13. This is not a monthly observation and not an annual total."""

    grid_id: str
    latitude: float
    longitude: float
    year: int
    variable: str
    value: float | None
    source_unit: str
    source_parameter: str


@dataclass(frozen=True)
class ParsedPowerResponse:
    source_parameter: str
    variable: str
    source_unit: str
    long_name: str
    fill_value: float
    sources: list[str]
    time_standard: str | None
    messages: list[str]
    observations: list[MonthlyObservation]
    annual_statistics: list[AnnualApiStatistic]
    feature_count: int


def parse_power_response(payload: dict, parameter: str | None = None) -> ParsedPowerResponse:
    if not isinstance(payload, dict):
        raise NormalizationError("NASA POWER payload must be a JSON object.")

    features = _features(payload)
    parameter_meta = payload.get("parameters")
    if not isinstance(parameter_meta, dict) or not parameter_meta:
        raise NormalizationError("NASA POWER payload is missing parameter metadata.")

    requested = parameter or next(iter(parameter_meta))
    if requested not in parameter_meta:
        raise NormalizationError(f"Response does not include parameter {requested}.")

    definition = SOURCE_PARAMETERS.get(requested)
    if definition is None:
        raise NormalizationError(f"Parameter {requested} is not in the project whitelist.")

    meta = parameter_meta[requested]
    if not isinstance(meta, dict) or "units" not in meta:
        raise NormalizationError(f"Parameter {requested} is missing units.")

    source_unit = str(meta["units"])
    if source_unit != definition.source_unit:
        raise NormalizationError(
            f"Parameter {requested} returned unit {source_unit!r}, "
            f"expected verified unit {definition.source_unit!r}."
        )

    header = payload.get("header")
    if not isinstance(header, dict) or "fill_value" not in header:
        raise NormalizationError("NASA POWER payload is missing header.fill_value.")

    fill_value = float(header["fill_value"])
    sources = [str(item) for item in header.get("sources") or []]
    time_standard = header.get("time_standard")
    messages = [str(item) for item in payload.get("messages") or []]

    observations: list[MonthlyObservation] = []
    annual_statistics: list[AnnualApiStatistic] = []

    for feature in features:
        latitude, longitude, elevation = _coordinates(feature)
        grid_id = f"{latitude:.4f},{longitude:.4f}"
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            raise NormalizationError("A NASA POWER feature is missing properties.")
        parameter_block = properties.get("parameter")
        if not isinstance(parameter_block, dict) or requested not in parameter_block:
            raise NormalizationError(f"A feature is missing the {requested} series.")
        series = parameter_block[requested]
        if not isinstance(series, dict):
            raise NormalizationError(f"The {requested} series must be an object of time keys.")

        for key, raw_value in series.items():
            year, month = _time_key(str(key))
            value, status = _value(raw_value, fill_value)
            if month == 13:
                annual_statistics.append(
                    AnnualApiStatistic(
                        grid_id=grid_id,
                        latitude=latitude,
                        longitude=longitude,
                        year=year,
                        variable=definition.id,
                        value=value,
                        source_unit=source_unit,
                        source_parameter=requested,
                    )
                )
                continue
            observations.append(
                MonthlyObservation(
                    grid_id=grid_id,
                    latitude=latitude,
                    longitude=longitude,
                    elevation_m=elevation,
                    year=year,
                    month=month,
                    variable=definition.id,
                    value=value,
                    source_unit=source_unit,
                    source_parameter=requested,
                    data_quality_status=status,
                )
            )

    return ParsedPowerResponse(
        source_parameter=requested,
        variable=definition.id,
        source_unit=source_unit,
        long_name=str(meta.get("longname") or definition.long_name),
        fill_value=fill_value,
        sources=sources,
        time_standard=str(time_standard) if time_standard is not None else None,
        messages=messages,
        observations=observations,
        annual_statistics=annual_statistics,
        feature_count=len(features),
    )


def _features(payload: dict) -> list[dict]:
    geometry_type = payload.get("type")
    if geometry_type == "FeatureCollection":
        features = payload.get("features")
        if not isinstance(features, list):
            raise NormalizationError("FeatureCollection is missing a features list.")
        return features
    if geometry_type == "Feature":
        return [payload]
    raise NormalizationError(
        "Unrecognized NASA POWER geometry. Expected a Feature or FeatureCollection."
    )


def _coordinates(feature: dict) -> tuple[float, float, float | None]:
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict) or geometry.get("type") != "Point":
        raise NormalizationError("Only Point geometries are supported.")
    coordinates = geometry.get("coordinates")
    if not isinstance(coordinates, list) or len(coordinates) < 2:
        raise NormalizationError("Point geometry is missing longitude and latitude.")
    longitude = float(coordinates[0])
    latitude = float(coordinates[1])
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise NormalizationError(f"Impossible coordinate: {longitude}, {latitude}.")
    elevation = float(coordinates[2]) if len(coordinates) > 2 else None
    return latitude, longitude, elevation


def _time_key(key: str) -> tuple[int, int]:
    if len(key) != 6 or not key.isdigit():
        raise NormalizationError(f"Unrecognized NASA POWER time key: {key}.")
    year = int(key[:4])
    month = int(key[4:])
    if month < 1 or month > 13:
        raise NormalizationError(f"Time key {key} has a month outside 01–13.")
    return year, month


def _value(raw_value: object, fill_value: float) -> tuple[float | None, str]:
    if raw_value is None:
        return None, "missing"
    if isinstance(raw_value, bool) or not isinstance(raw_value, (int, float)):
        raise NormalizationError(f"Climate value must be numeric, got {raw_value!r}.")
    value = float(raw_value)
    if value == fill_value:
        return None, "missing"
    return value, "valid"
