import math

import numpy as np

MINIMUM_PERIOD_FRACTION = 0.8


def period_statistic(
    years: np.ndarray,
    values: np.ndarray,
    start_year: int,
    end_year: int,
) -> dict:
    years = np.asarray(years, dtype=int)
    values = np.asarray(values, dtype=float)
    expected = end_year - start_year + 1
    selected = (years >= start_year) & (years <= end_year) & np.isfinite(values)
    count = int(selected.sum())
    fraction = count / expected if expected else 0.0
    if expected <= 0 or fraction < MINIMUM_PERIOD_FRACTION:
        return {
            "value": None,
            "valid_years": count,
            "expected_years": expected,
            "coverage_fraction": fraction,
            "accepted": False,
        }
    return {
        "value": float(np.mean(values[selected])),
        "valid_years": count,
        "expected_years": expected,
        "coverage_fraction": fraction,
        "accepted": True,
    }


def absolute_and_relative_difference(
    baseline: float | None,
    comparison: float | None,
    *,
    allow_relative: bool,
) -> dict:
    if baseline is None or comparison is None:
        return {"absolute_difference": None, "relative_difference_percent": None, "quality_flags": ["period_not_accepted"]}
    absolute = comparison - baseline
    flags: list[str] = []
    relative = None
    if allow_relative:
        if baseline == 0:
            flags.append("relative_difference_undefined_zero_baseline")
        else:
            relative = (absolute / baseline) * 100
    return {
        "absolute_difference": float(absolute),
        "relative_difference_percent": None if relative is None else float(relative),
        "quality_flags": flags,
    }


def anomaly_series(
    years: np.ndarray,
    values: np.ndarray,
    baseline_start: int,
    baseline_end: int,
) -> list[dict]:
    baseline = period_statistic(years, values, baseline_start, baseline_end)
    points = []
    for year, value in zip(years, values, strict=True):
        number = float(value) if math.isfinite(float(value)) else None
        anomaly = None
        if number is not None and baseline["value"] is not None:
            anomaly = number - baseline["value"]
        points.append({"year": int(year), "value": number, "anomaly": anomaly})
    return points


def unusual_year_counts(
    years: np.ndarray,
    values: np.ndarray,
    *,
    baseline_start: int,
    baseline_end: int,
    comparison_start: int,
    comparison_end: int,
) -> dict:
    years = np.asarray(years, dtype=int)
    values = np.asarray(values, dtype=float)
    baseline_mask = (years >= baseline_start) & (years <= baseline_end) & np.isfinite(values)
    comparison_mask = (years >= comparison_start) & (years <= comparison_end) & np.isfinite(values)
    baseline_values = values[baseline_mask]
    if baseline_values.size < 5:
        return {
            "high_threshold": None,
            "low_threshold": None,
            "years_above_baseline_p90": None,
            "years_below_baseline_p10": None,
            "quality_flags": ["baseline_too_short_for_percentiles"],
        }
    high = float(np.percentile(baseline_values, 90))
    low = float(np.percentile(baseline_values, 10))
    comparison_values = values[comparison_mask]
    return {
        "high_threshold": high,
        "low_threshold": low,
        "years_above_baseline_p90": int(np.sum(comparison_values > high)),
        "years_below_baseline_p10": int(np.sum(comparison_values < low)),
        "quality_flags": [],
    }


def area_weights(latitudes: np.ndarray) -> np.ndarray:
    return np.cos(np.radians(np.asarray(latitudes, dtype=float)))


def weighted_status_fraction(status_grid: np.ndarray, latitudes: np.ndarray, target: str) -> dict:
    weights = area_weights(latitudes)[:, None]
    tested = np.isin(
        status_grid,
        ["significant_increasing", "significant_decreasing", "not_significant"],
    )
    tested_weight = float(np.where(tested, weights, 0).sum())
    target_weight = float(np.where(status_grid == target, weights, 0).sum())
    if tested_weight == 0:
        return {"cell_count": int(np.sum(status_grid == target)), "area_fraction": None}
    return {
        "cell_count": int(np.sum(status_grid == target)),
        "area_fraction": target_weight / tested_weight,
    }
