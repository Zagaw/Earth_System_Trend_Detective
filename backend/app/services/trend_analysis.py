import math
from dataclasses import dataclass, field

import numpy as np
import pymannkendall as mk
from scipy import stats
from statsmodels.stats.multitest import multipletests

AUTOCORRELATION_THRESHOLD = 0.3


@dataclass
class NumericTrend:
    sen_slope: float | None
    intercept: float | None
    p_value: float | None
    ci_low: float | None
    ci_high: float | None
    valid_years: int
    expected_years: int
    first_year: int | None
    first_value: float | None
    last_year: int | None
    last_value: float | None
    absolute_change: float | None
    test_method: str
    autocorrelation_method: str
    quality_flags: list[str] = field(default_factory=list)
    fit_years: np.ndarray = field(default_factory=lambda: np.array([], dtype=int))
    fit_values: np.ndarray = field(default_factory=lambda: np.array([], dtype=float))


def series_trend(
    years: np.ndarray,
    values: np.ndarray,
    *,
    minimum_valid_years: int,
    alpha: float = 0.05,
) -> NumericTrend:
    years = np.asarray(years, dtype=int)
    values = np.asarray(values, dtype=float)
    expected = int(len(years))
    valid = np.isfinite(values)
    fit_years = years[valid]
    fit_values = values[valid]
    count = int(fit_years.size)
    base = NumericTrend(
        sen_slope=None,
        intercept=None,
        p_value=None,
        ci_low=None,
        ci_high=None,
        valid_years=count,
        expected_years=expected,
        first_year=int(fit_years[0]) if count else None,
        first_value=_plain(fit_values[0]) if count else None,
        last_year=int(fit_years[-1]) if count else None,
        last_value=_plain(fit_values[-1]) if count else None,
        absolute_change=None,
        test_method="not_tested",
        autocorrelation_method="not_applicable",
        fit_years=fit_years,
        fit_values=fit_values,
    )
    if count:
        base.absolute_change = _plain(fit_values[-1] - fit_values[0])
    if count < minimum_valid_years:
        base.quality_flags.append("insufficient_valid_years")
        return base
    if np.nanstd(fit_values) == 0:
        base.sen_slope = 0.0
        base.intercept = _plain(fit_values[0])
        base.p_value = 1.0
        base.ci_low = 0.0
        base.ci_high = 0.0
        base.test_method = "mann_kendall"
        base.autocorrelation_method = "none"
        base.quality_flags.append("constant_series")
        return base

    slope, intercept, low, high = stats.theilslopes(fit_values, fit_years, alpha=0.95)
    base.sen_slope = _plain(slope)
    base.intercept = _plain(intercept)
    base.ci_low = _plain(low)
    base.ci_high = _plain(high)
    residuals = fit_values - (intercept + slope * fit_years)
    correlation = _lag1(residuals)
    use_correction = correlation is not None and abs(correlation) >= AUTOCORRELATION_THRESHOLD
    try:
        if use_correction:
            result = mk.hamed_rao_modification_test(fit_values)
            base.test_method = "hamed_rao_modification_test"
            base.autocorrelation_method = "hamed_rao_variance_correction"
        else:
            result = mk.original_test(fit_values)
            base.test_method = "mann_kendall"
            base.autocorrelation_method = "none"
        base.p_value = _plain(result.p)
    except (ValueError, ZeroDivisionError, FloatingPointError):
        base.quality_flags.append("significance_test_failed")
        base.test_method = "not_tested"
        base.p_value = None
    return base


def classify_trend(
    trend: NumericTrend,
    p_value: float | None,
    *,
    alpha: float,
    minimum_valid_years: int,
) -> str:
    if trend.valid_years < minimum_valid_years or trend.sen_slope is None or p_value is None:
        return "insufficient_data"
    if p_value < alpha and trend.sen_slope > 0:
        return "significant_increasing"
    if p_value < alpha and trend.sen_slope < 0:
        return "significant_decreasing"
    return "not_significant"


def adjust_pvalues(p_values: list[float], *, alpha: float) -> list[float]:
    if not p_values:
        return []
    _, adjusted, _, _ = multipletests(p_values, alpha=alpha, method="fdr_bh")
    return [float(value) for value in adjusted]


def trend_direction(slope: float | None) -> str:
    if slope is None:
        return "unknown"
    if slope > 0:
        return "increasing"
    if slope < 0:
        return "decreasing"
    return "flat"


def _lag1(values: np.ndarray) -> float | None:
    if values.size < 4 or np.nanstd(values) == 0:
        return None
    correlation = np.corrcoef(values[:-1], values[1:])[0, 1]
    if not math.isfinite(float(correlation)):
        return None
    return float(correlation)


def _plain(value: object) -> float | None:
    number = float(value)  # type: ignore[arg-type]
    if not math.isfinite(number):
        return None
    return number
