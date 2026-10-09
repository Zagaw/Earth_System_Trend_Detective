import numpy as np
import pandas as pd
import xarray as xr

from app.services.aggregation import (
    aggregate_annual,
    aggregate_seasonal,
    monthly_accumulation_mm,
    required_valid_months,
)
from app.services.impact import absolute_and_relative_difference, period_statistic
from app.services.nasa_power import _tiles
from app.services.trend_analysis import classify_trend, series_trend


def test_tiles_stay_within_the_ten_degree_api_limit() -> None:
    tiles = _tiles(9, 29, 92, 102)
    assert tiles[0] == (9, 19, 92, 102)
    assert tiles[1][0] > 19
    assert tiles[1][1] == 29
    assert all(lat1 - lat0 <= 10 and lon1 - lon0 <= 10 for lat0, lat1, lon0, lon1 in tiles)


def test_february_accumulation_uses_leap_days() -> None:
    assert monthly_accumulation_mm(1, 2020, 2) == 29
    assert monthly_accumulation_mm(1, 2021, 2) == 28
    assert monthly_accumulation_mm(None, 2020, 2) is None


def test_rainfall_requires_every_month_and_means_require_ten() -> None:
    assert required_valid_months("precipitation", 12) == 12
    assert required_valid_months("temperature", 12) == 10
    assert required_valid_months("relative_humidity", 6) == 5


def test_partial_rainfall_year_is_missing_and_temperature_mean_is_not_a_sum() -> None:
    time = pd.date_range("2001-01-01", periods=12, freq="MS")
    rainfall = np.full((12, 1, 1), 10.0)
    rainfall[5, 0, 0] = np.nan
    temperature = np.arange(12, dtype=float).reshape(12, 1, 1)
    rain = aggregate_annual(_array(time, rainfall), "precipitation")
    temp = aggregate_annual(_array(time, temperature), "temperature")
    assert np.isnan(rain["value"].values[0, 0, 0])
    assert temp["value"].values[0, 0, 0] == np.mean(np.arange(12))


def test_djf_uses_december_from_the_previous_year() -> None:
    time = pd.to_datetime(["2001-12-01", "2002-01-01", "2002-02-01"])
    values = np.array([3, 4, 5], dtype=float).reshape(3, 1, 1)
    seasonal = aggregate_seasonal(_array(time, values), "temperature", "DJF")
    assert int(seasonal.year.values[0]) == 2002
    assert seasonal["value"].values[0, 0, 0] == 4


def test_increasing_decreasing_and_constant_series() -> None:
    years = np.arange(2001, 2021)
    increasing = series_trend(years, years - 2000, minimum_valid_years=10)
    decreasing = series_trend(years, 2000 - years, minimum_valid_years=10)
    constant = series_trend(years, np.ones(years.shape), minimum_valid_years=10)
    assert classify_trend(increasing, increasing.p_value, alpha=0.05, minimum_valid_years=10) == "significant_increasing"
    assert increasing.sen_slope == 1
    assert classify_trend(decreasing, decreasing.p_value, alpha=0.05, minimum_valid_years=10) == "significant_decreasing"
    assert classify_trend(constant, constant.p_value, alpha=0.05, minimum_valid_years=10) == "not_significant"
    assert constant.sen_slope == 0


def test_missing_years_use_year_coordinates_for_the_slope() -> None:
    years = np.array([2000, 2001, 2002, 2004])
    values = np.array([0.0, 1.0, 2.0, 4.0])
    trend = series_trend(years, values, minimum_valid_years=4)
    assert trend.sen_slope == 1


def test_short_series_is_not_classified() -> None:
    years = np.arange(2001, 2006)
    trend = series_trend(years, years.astype(float), minimum_valid_years=10)
    assert classify_trend(trend, trend.p_value, alpha=0.05, minimum_valid_years=10) == "insufficient_data"


def test_relative_rainfall_change_is_blocked_when_the_baseline_is_zero() -> None:
    result = absolute_and_relative_difference(0, 10, allow_relative=True)
    assert result["absolute_difference"] == 10
    assert result["relative_difference_percent"] is None
    temperature = absolute_and_relative_difference(20, 21, allow_relative=False)
    assert temperature["relative_difference_percent"] is None


def test_period_mean_rejects_a_sparse_window() -> None:
    years = np.arange(2001, 2011)
    values = np.array([1, np.nan, np.nan, np.nan, 1, np.nan, np.nan, np.nan, 1, np.nan])
    result = period_statistic(years, values, 2001, 2010)
    assert result["accepted"] is False


def _array(time: pd.DatetimeIndex, values: np.ndarray) -> xr.DataArray:
    return xr.DataArray(
        values,
        coords={"time": time, "latitude": [16.5], "longitude": [96.25]},
        dims=("time", "latitude", "longitude"),
    )
