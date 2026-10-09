from datetime import UTC, datetime

import numpy as np
import pandas as pd
import xarray as xr

from app.core.variables import VARIABLES
from app.services.aggregation import monthly_accumulation_mm
from app.services.normalization import ParsedPowerResponse


def build_climate_dataset(parsed_by_variable: dict[str, ParsedPowerResponse]) -> xr.Dataset:
    if set(parsed_by_variable) != set(VARIABLES):
        missing = sorted(set(VARIABLES) - set(parsed_by_variable))
        raise ValueError(f"Missing parsed variables: {', '.join(missing)}")

    coordinates: set[tuple[float, float]] = set()
    months: set[tuple[int, int]] = set()
    for parsed in parsed_by_variable.values():
        for observation in parsed.observations:
            coordinates.add((_coord(observation.latitude), _coord(observation.longitude)))
            months.add((observation.year, observation.month))

    latitudes = np.array(sorted({item[0] for item in coordinates}), dtype=float)
    longitudes = np.array(sorted({item[1] for item in coordinates}), dtype=float)
    time_keys = sorted(months)
    lat_index = {value: index for index, value in enumerate(latitudes)}
    lon_index = {value: index for index, value in enumerate(longitudes)}
    time_index = {key: index for index, key in enumerate(time_keys)}

    shape = (len(time_keys), len(latitudes), len(longitudes))
    arrays = {
        variable: np.full(shape, np.nan, dtype=float) for variable in VARIABLES
    }
    elevation = np.full((len(latitudes), len(longitudes)), np.nan, dtype=float)
    seen: set[tuple[str, int, int, float, float]] = set()

    for variable, parsed in parsed_by_variable.items():
        for observation in parsed.observations:
            latitude = _coord(observation.latitude)
            longitude = _coord(observation.longitude)
            identity = (variable, observation.year, observation.month, latitude, longitude)
            if identity in seen:
                raise ValueError(f"Duplicate observation for {identity}.")
            seen.add(identity)
            value = observation.value
            if variable == "precipitation":
                value = monthly_accumulation_mm(value, observation.year, observation.month)
            arrays[variable][
                time_index[(observation.year, observation.month)],
                lat_index[latitude],
                lon_index[longitude],
            ] = np.nan if value is None else value
            if observation.elevation_m is not None and not np.isfinite(
                elevation[lat_index[latitude], lon_index[longitude]]
            ):
                elevation[lat_index[latitude], lon_index[longitude]] = observation.elevation_m

    times = pd.to_datetime([f"{year:04d}-{month:02d}-01" for year, month in time_keys])
    dataset = xr.Dataset(
        data_vars={
            "precipitation": (("time", "latitude", "longitude"), arrays["precipitation"]),
            "temperature": (("time", "latitude", "longitude"), arrays["temperature"]),
            "relative_humidity": (("time", "latitude", "longitude"), arrays["relative_humidity"]),
            "elevation_m": (("latitude", "longitude"), elevation),
        },
        coords={"time": times, "latitude": latitudes, "longitude": longitudes},
    )
    dataset["precipitation"].attrs.update(
        {"units": "mm", "long_name": "Monthly precipitation accumulation", "source_parameter": "PRECTOTCORR"}
    )
    dataset["temperature"].attrs.update(
        {"units": "degC", "long_name": "Monthly mean air temperature at 2 m", "source_parameter": "T2M"}
    )
    dataset["relative_humidity"].attrs.update(
        {"units": "%", "long_name": "Monthly mean relative humidity at 2 m", "source_parameter": "RH2M"}
    )
    dataset.attrs.update(
        {
            "source": "NASA POWER",
            "processing_version": "0.2.0",
            "precipitation_conversion": "monthly_mm = mm_per_day * days_in_month",
            "time_meaning": "month_start",
            "built_at": datetime.now(UTC).isoformat(),
        }
    )
    return dataset


def _coord(value: float) -> float:
    return round(float(value), 4)
