import calendar
import math
import warnings

import numpy as np
import pandas as pd
import xarray as xr

SEASON_MONTHS: dict[str, tuple[int, ...]] = {
    "DJF": (12, 1, 2),
    "MAM": (3, 4, 5),
    "JJA": (6, 7, 8),
    "SON": (9, 10, 11),
    # Myanmar southwest monsoon, fixed as May–October for every region and year.
    "monsoon": (5, 6, 7, 8, 9, 10),
}

MEAN_MONTH_FRACTION = 10 / 12


def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def monthly_accumulation_mm(rate_mm_per_day: float | None, year: int, month: int) -> float | None:
    if rate_mm_per_day is None or not math.isfinite(rate_mm_per_day):
        return None
    return float(rate_mm_per_day) * days_in_month(year, month)


def required_valid_months(variable: str, expected_months: int) -> int:
    if variable == "precipitation":
        return expected_months
    return max(1, math.ceil(expected_months * MEAN_MONTH_FRACTION))


def aggregate_annual(monthly: xr.DataArray, variable: str) -> xr.Dataset:
    return _aggregate(monthly, variable, season=None)


def aggregate_seasonal(monthly: xr.DataArray, variable: str, season: str) -> xr.Dataset:
    if season not in SEASON_MONTHS:
        raise ValueError(f"Unknown season {season}.")
    return _aggregate(monthly, variable, season=season)


def _aggregate(monthly: xr.DataArray, variable: str, season: str | None) -> xr.Dataset:
    times = pd.to_datetime(monthly.time.values)
    data = np.asarray(monthly.values, dtype=float)
    latitudes = monthly.latitude.values
    longitudes = monthly.longitude.values
    if season is None:
        years = np.unique(times.year)
        expected = 12
        blocks = [np.where(times.year == int(year))[0] for year in years]
    else:
        months = SEASON_MONTHS[season]
        expected = len(months)
        first_year = int(times.year.min())
        last_year = int(times.year.max())
        if season == "DJF":
            years = np.arange(first_year + 1, last_year + 1)
        else:
            years = np.arange(first_year, last_year + 1)
        blocks = [_season_indexes(times, int(year), season) for year in years]

    required = required_valid_months(variable, expected)
    values = np.full((len(years), len(latitudes), len(longitudes)), np.nan)
    counts = np.zeros((len(years), len(latitudes), len(longitudes)), dtype=np.int16)

    for index, block in enumerate(blocks):
        if len(block) == 0:
            continue
        sample = data[block]
        valid = np.isfinite(sample).sum(axis=0)
        counts[index] = valid
        if variable == "precipitation":
            total = np.nansum(sample, axis=0)
            values[index] = np.where(valid >= required, total, np.nan)
        else:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                mean = np.nanmean(sample, axis=0)
            values[index] = np.where(valid >= required, mean, np.nan)

    coverage = counts / expected
    return xr.Dataset(
        data_vars={
            "value": (("year", "latitude", "longitude"), values),
            "valid_months": (("year", "latitude", "longitude"), counts),
            "coverage_fraction": (("year", "latitude", "longitude"), coverage),
        },
        coords={
            "year": years.astype(int),
            "latitude": latitudes,
            "longitude": longitudes,
        },
        attrs={
            "variable": variable,
            "season": season or "",
            "expected_months": expected,
            "required_valid_months": required,
        },
    )


def _season_indexes(times: pd.DatetimeIndex, year: int, season: str) -> np.ndarray:
    months = SEASON_MONTHS[season]
    if season == "DJF":
        wanted = {(year - 1, 12), (year, 1), (year, 2)}
    else:
        wanted = {(year, month) for month in months}
    indexes = [
        index
        for index, stamp in enumerate(times)
        if (int(stamp.year), int(stamp.month)) in wanted
    ]
    return np.array(indexes, dtype=int)
