import json
from pathlib import Path

import numpy as np
import xarray as xr

from app.core.config import Settings, get_settings
from app.core.variables import VARIABLES
from app.services.aggregation import SEASON_MONTHS, aggregate_annual, aggregate_seasonal
from app.services.dataset_builder import build_climate_dataset
from app.services.impact import (
    absolute_and_relative_difference,
    anomaly_series,
    period_statistic,
    unusual_year_counts,
    weighted_status_fraction,
)
from app.services.interpretation import interpret_impact, interpret_trend
from app.services.nasa_power import NasaPowerClient
from app.services.normalization import parse_power_response
from app.services.spatial_analysis import apply_boundaries
from app.services.trend_analysis import (
    adjust_pvalues,
    classify_trend,
    series_trend,
    trend_direction,
)

NATIONAL_ALIAS = "MMR"


class CatalogNotReady(Exception):
    pass


class UnknownRegion(Exception):
    pass


class ClimateCatalog:
    def __init__(self, dataset: xr.Dataset, region_catalog: dict, settings: Settings) -> None:
        self.dataset = dataset
        self.region_catalog = region_catalog
        self.settings = settings
        self.regions = self._index_regions(region_catalog)
        self._aggregated: dict[tuple, xr.Dataset] = {}
        self._grids: dict[tuple, dict] = {}
        self._case_files: dict[tuple, dict] = {}

    @classmethod
    def load(cls, settings: Settings | None = None) -> "ClimateCatalog":
        settings = settings or get_settings()
        dataset_path = settings.processed_dir / "climate_monthly.nc"
        region_path = settings.processed_dir / "regions.json"
        if not dataset_path.exists() or not region_path.exists():
            raise CatalogNotReady(
                "Myanmar climate data has not been ingested. "
                "From the backend folder, run: python -m app.cli ingest"
            )
        with xr.open_dataset(dataset_path) as dataset:
            loaded = dataset.load()
        return cls(loaded, json.loads(region_path.read_text(encoding="utf-8")), settings)

    @classmethod
    def build(cls, settings: Settings | None = None) -> "ClimateCatalog":
        settings = settings or get_settings()
        client = NasaPowerClient(settings)
        parsed = {}
        for definition in VARIABLES.values():
            payload = client.fetch_study_grid(
                definition.source_parameter,
                start_year=settings.default_start_year,
                end_year=settings.default_end_year,
            )
            parsed[definition.id] = parse_power_response(payload, definition.source_parameter)
        dataset = build_climate_dataset(parsed)
        dataset, region_catalog = apply_boundaries(dataset, settings.boundary_dir)
        settings.processed_dir.mkdir(parents=True, exist_ok=True)
        dataset_path = settings.processed_dir / "climate_monthly.nc"
        region_path = settings.processed_dir / "regions.json"
        dataset.to_netcdf(dataset_path)
        region_path.write_text(json.dumps(region_catalog, indent=2), encoding="utf-8")
        return cls(dataset, region_catalog, settings)

    def metadata(self) -> dict:
        time = self.dataset.time.to_pandas()
        return {
            "study_grid_status": "ready",
            "actual_start_year": int(time.min().year),
            "actual_end_year": int(time.max().year),
            "masked_cell_count": int(self.dataset["myanmar_mask"].sum()),
            "national_region_id": self.region_catalog["national"]["id"],
            "retrieved_at": str(self.dataset.attrs.get("built_at")),
            "mask_policy": self.region_catalog["mask_policy"],
            "boundary_overlap_cells": self.region_catalog["boundary_overlap_cells"],
            "unassigned_interior_cells": self.region_catalog["unassigned_interior_cells"],
        }

    def list_regions(self) -> list[dict]:
        national = self.region_catalog["national"]
        rows = [
            {
                "id": national["id"],
                "name": national["name"],
                "level": "ADM0",
                "iso": national["iso"],
                "cell_count": national["cell_count"],
            }
        ]
        rows.extend(self.region_catalog["regions"])
        return rows

    def timeseries(
        self,
        variable: str,
        start_year: int,
        end_year: int,
        aggregation: str,
        season: str | None,
        region_id: str | None,
    ) -> dict:
        region = self._region(region_id)
        years, values, coverage = self._series(variable, start_year, end_year, aggregation, season, region)
        definition = VARIABLES[variable]
        points = []
        for year, value, cover in zip(years, values, coverage, strict=True):
            if aggregation == "monthly":
                point_year = int(year) // 100
                point_month = int(year) % 100
            else:
                point_year = int(year)
                point_month = None
            points.append(
                {
                    "year": point_year,
                    "month": point_month,
                    "value": _number(value),
                    "coverage_fraction": _number(cover),
                }
            )
        trend_line = []
        if aggregation != "monthly":
            trend = self._numeric_trend(years, values)
            trend_line = _trend_line(years, trend.intercept, trend.sen_slope)
        return {
            "variable": variable,
            "variable_label": definition.label,
            "unit": definition.analysis_unit,
            "aggregation": aggregation,
            "season": season,
            "region_id": region["id"],
            "region_name": region["name"],
            "start_year": start_year,
            "end_year": end_year,
            "source": "NASA POWER",
            "source_parameter": definition.source_parameter,
            "retrieved_at": self.metadata()["retrieved_at"],
            "data": points,
            "trend_line": trend_line,
        }

    def trend(
        self,
        variable: str,
        start_year: int,
        end_year: int,
        aggregation: str,
        season: str | None,
        region_id: str | None,
    ) -> dict:
        self._require_summary_aggregation(aggregation)
        region = self._region(region_id)
        if region["level"] == "ADM1":
            family = self._admin_trends(variable, start_year, end_year, aggregation, season)
            selected = next(item for item in family if item["geography_id"] == region["id"])
            return selected
        years, values, _coverage = self._series(
            variable, start_year, end_year, aggregation, season, region
        )
        numeric = self._numeric_trend(years, values)
        return self._trend_record(
            variable,
            region,
            start_year,
            end_year,
            aggregation,
            season,
            numeric,
            adjusted_p_value=numeric.p_value,
            multiple_testing_method="none",
        )

    def grid(
        self,
        variable: str,
        start_year: int,
        end_year: int,
        aggregation: str,
        season: str | None,
    ) -> dict:
        self._require_summary_aggregation(aggregation)
        cached = self._grid_results(variable, start_year, end_year, aggregation, season)
        return {
            "variable": variable,
            "unit": VARIABLES[variable].analysis_unit,
            "slope_unit": VARIABLES[variable].slope_unit,
            "aggregation": aggregation,
            "season": season,
            "start_year": start_year,
            "end_year": end_year,
            "multiple_testing_method": "benjamini_hochberg",
            "significance_alpha": self.settings.significance_alpha,
            "type": "FeatureCollection",
            "features": cached["features"],
        }

    def compare(
        self,
        variable: str,
        start_year: int,
        end_year: int,
        aggregation: str,
        season: str | None,
        region_ids: list[str],
    ) -> dict:
        self._require_summary_aggregation(aggregation)
        if len(region_ids) < 2:
            raise ValueError("Choose at least two regions to compare.")
        family = {
            item["geography_id"]: item
            for item in self._admin_trends(variable, start_year, end_year, aggregation, season)
        }
        national = self.trend(variable, start_year, end_year, aggregation, season, None)
        family[national["geography_id"]] = national
        rows = []
        for region_id in region_ids:
            if region_id not in family and region_id != NATIONAL_ALIAS:
                raise UnknownRegion(region_id)
            key = self._region(region_id)["id"]
            rows.append(family[key])
        ranked = sorted(
            rows,
            key=lambda item: (item["sen_slope"] is None, -(item["sen_slope"] or 0)),
        )
        return {"variable": variable, "regions": ranked}

    def impact_summary(
        self,
        variable: str,
        start_year: int,
        end_year: int,
        aggregation: str,
        season: str | None,
        region_id: str | None,
        baseline_start: int,
        baseline_end: int,
        comparison_start: int,
        comparison_end: int,
    ) -> dict:
        self._require_summary_aggregation(aggregation)
        self._require_window("baseline", baseline_start, baseline_end, start_year, end_year)
        self._require_window("comparison", comparison_start, comparison_end, start_year, end_year)
        region = self._region(region_id)
        years, values, _coverage = self._series(
            variable, start_year, end_year, aggregation, season, region
        )
        baseline = period_statistic(years, values, baseline_start, baseline_end)
        comparison = period_statistic(years, values, comparison_start, comparison_end)
        definition = VARIABLES[variable]
        difference = absolute_and_relative_difference(
            baseline["value"],
            comparison["value"],
            allow_relative=variable == "precipitation",
        )
        unusual = unusual_year_counts(
            years,
            values,
            baseline_start=baseline_start,
            baseline_end=baseline_end,
            comparison_start=comparison_start,
            comparison_end=comparison_end,
        )
        grid = self._grid_results(variable, start_year, end_year, aggregation, season)
        status = grid["status"]
        increasing = weighted_status_fraction(status, self.dataset.latitude.values, "significant_increasing")
        decreasing = weighted_status_fraction(status, self.dataset.latitude.values, "significant_decreasing")
        payload = {
            "variable": variable,
            "variable_label": definition.label,
            "unit": definition.analysis_unit,
            "geography_id": region["id"],
            "geography_name": region["name"],
            "aggregation": aggregation,
            "season": season,
            "baseline_start_year": baseline_start,
            "baseline_end_year": baseline_end,
            "comparison_start_year": comparison_start,
            "comparison_end_year": comparison_end,
            "baseline_mean": baseline["value"],
            "comparison_mean": comparison["value"],
            "baseline_valid_years": baseline["valid_years"],
            "comparison_valid_years": comparison["valid_years"],
            "absolute_difference": difference["absolute_difference"],
            "relative_difference_percent": difference["relative_difference_percent"],
            "difference_text": _format_number(difference["absolute_difference"], variable),
            "spatial_weighting": "cos(latitude)",
            "tested_cell_count": int(np.sum(np.isin(
                status,
                ["significant_increasing", "significant_decreasing", "not_significant"],
            ))),
            "significant_increasing_cells": increasing["cell_count"],
            "significant_decreasing_cells": decreasing["cell_count"],
            "increasing_area_fraction": increasing["area_fraction"],
            "decreasing_area_fraction": decreasing["area_fraction"],
            "years_above_baseline_p90": unusual["years_above_baseline_p90"],
            "years_below_baseline_p10": unusual["years_below_baseline_p10"],
            "quality_flags": difference["quality_flags"] + unusual["quality_flags"],
            "limitation": (
                "Differences describe the climate series only. They are not measurements "
                "of crop loss, health impacts, flood damage, or economic cost."
            ),
            "source": "NASA POWER",
            "processing_version": "0.2.0",
        }
        payload["interpretation"] = interpret_impact(payload)
        return payload

    def anomalies(
        self,
        variable: str,
        start_year: int,
        end_year: int,
        aggregation: str,
        season: str | None,
        region_id: str | None,
        baseline_start: int,
        baseline_end: int,
    ) -> dict:
        self._require_summary_aggregation(aggregation)
        region = self._region(region_id)
        years, values, _coverage = self._series(
            variable, start_year, end_year, aggregation, season, region
        )
        definition = VARIABLES[variable]
        return {
            "variable": variable,
            "unit": definition.analysis_unit,
            "region_id": region["id"],
            "region_name": region["name"],
            "baseline_start_year": baseline_start,
            "baseline_end_year": baseline_end,
            "aggregation": aggregation,
            "season": season,
            "anomaly_definition": "aggregated value minus the baseline-period mean",
            "data": anomaly_series(years, values, baseline_start, baseline_end),
        }

    def case_file(self, start_year: int = 2001, end_year: int = 2025) -> dict:
        """One dossier for the case-file UI. Slopes, tests, and anomalies stay in Python."""
        key = (int(start_year), int(end_year))
        if key in self._case_files:
            return self._case_files[key]
        baseline_start, baseline_end, comparison_start, comparison_end = _case_windows(
            start_year, end_year
        )
        national = self.region_catalog["national"]
        places = [self._region(None), *[self._region(item["id"]) for item in self.region_catalog["regions"]]]
        variables = {}
        for variable in VARIABLES:
            admin = self._admin_trends(variable, start_year, end_year, "annual", None)
            national_trend = self.trend(variable, start_year, end_year, "annual", None, None)
            by_id = {item["geography_id"]: item for item in admin}
            by_id[national_trend["geography_id"]] = national_trend
            bundles = [
                self._place_bundle(
                    variable,
                    region,
                    start_year,
                    end_year,
                    by_id[region["id"]],
                    baseline_start,
                    baseline_end,
                    comparison_start,
                    comparison_end,
                )
                for region in places
            ]
            definition = VARIABLES[variable]
            variables[variable] = {
                "id": variable,
                "label": definition.label,
                "unit": definition.analysis_unit,
                "slope_unit": definition.slope_unit,
                "decade_unit": _decade_unit(variable),
                "source_parameter": definition.source_parameter,
                "source_unit": definition.source_unit,
                "temporal_meaning": definition.temporal_meaning,
                "aggregation_rule": definition.aggregation_rule,
                "conversion": definition.conversion,
                "national": bundles[0],
                "regions": bundles[1:],
            }
        payload = {
            "is_sample": False,
            "project": "EarthTrend Myanmar",
            "source": "NASA POWER",
            "community": self.settings.nasa_power_community,
            "anomaly_reference": (
                f"difference from the {baseline_start}–{baseline_end} average"
            ),
            "start_year": start_year,
            "end_year": end_year,
            "baseline_start_year": baseline_start,
            "baseline_end_year": baseline_end,
            "comparison_start_year": comparison_start,
            "comparison_end_year": comparison_end,
            "significance_alpha": self.settings.significance_alpha,
            "national": {
                "id": national["id"],
                "name": national["name"],
                "iso": national["iso"],
                "level": "ADM0",
            },
            "regions": [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "iso": item["iso"],
                    "level": item["level"],
                    "cell_count": item["cell_count"],
                }
                for item in self.region_catalog["regions"]
            ],
            "variables": variables,
            "evidence": {
                "mask_policy": self.region_catalog["mask_policy"],
                "boundary_overlap_cells": self.region_catalog["boundary_overlap_cells"],
                "unassigned_interior_cells": self.region_catalog["unassigned_interior_cells"],
                "masked_cell_count": int(self.dataset["myanmar_mask"].sum()),
                "minimum_valid_years": self.settings.minimum_valid_years,
                "minimum_spatial_coverage": self.settings.minimum_spatial_coverage,
                "spatial_weighting": "cos(latitude)",
                "trend_method": "Sen's slope, using year as the x coordinate",
                "significance_test": (
                    "Mann–Kendall on the annual series. Hamed–Rao correction is used "
                    "when the absolute lag-1 autocorrelation of the Sen residuals is at least 0.3."
                ),
                "multiple_testing_regions": "Benjamini–Hochberg across the 14 states and regions",
                "multiple_testing_national": "none, because the national series is a single test",
                "retrieved_at": self.metadata()["retrieved_at"],
                "limitations": [
                    "Results describe NASA POWER climate series, not crop loss, health, floods, or economic cost.",
                    "A non-significant result means the test did not meet the threshold. It is not proof that the climate is unchanged.",
                    "State and region names keep the geoBoundaries spellings, including Saigang and Tanitharyi.",
                    "A regional year is kept only when valid cells cover at least half of that region's area weight.",
                    "Elevation is stored and is not used in the trend calculations.",
                ],
            },
        }
        self._case_files[key] = payload
        return payload

    def understand_context(
        self,
        variable: str,
        start_year: int,
        end_year: int,
        region_id: str | None = None,
        compare_region_id: str | None = None,
    ) -> dict:
        dossier = self.case_file(start_year, end_year)
        if variable not in dossier["variables"]:
            raise ValueError(f"Unknown variable {variable}.")
        block = dossier["variables"][variable]
        selected = self._bundle_for(block, region_id)
        compare = None
        if compare_region_id:
            other = self._bundle_for(block, compare_region_id)
            if other["geography_id"] != selected["geography_id"]:
                compare = other
        spacing = self.region_catalog
        return {
            "is_sample": False,
            "source": dossier["source"],
            "community": dossier["community"],
            "parameter": block["source_parameter"],
            "source_unit": block["source_unit"],
            "analysis_unit": block["unit"],
            "slope_unit": block["slope_unit"],
            "decade_unit": block["decade_unit"],
            "aggregation_rule": block["aggregation_rule"],
            "variable": variable,
            "variable_label": block["label"],
            "start_year": dossier["start_year"],
            "end_year": dossier["end_year"],
            "baseline_start_year": dossier["baseline_start_year"],
            "baseline_end_year": dossier["baseline_end_year"],
            "comparison_start_year": dossier["comparison_start_year"],
            "comparison_end_year": dossier["comparison_end_year"],
            "significance_alpha": dossier["significance_alpha"],
            "spatial_resolution": (
                f"{spacing['latitude_spacing']}° latitude by {spacing['longitude_spacing']}° longitude"
            ),
            "evidence": dossier["evidence"],
            "selected": selected,
            "compare": compare,
            "region_summaries": [
                {
                    "geography_id": item["geography_id"],
                    "geography_name": item["geography_name"],
                    "sen_slope": item["sen_slope"],
                    "slope_per_decade": item["slope_per_decade"],
                    "trend_status": item["trend_status"],
                    "adjusted_p_value": item["adjusted_p_value"],
                    "valid_years": item["valid_years"],
                }
                for item in block["regions"]
            ],
        }

    def _bundle_for(self, block: dict, region_id: str | None) -> dict:
        region = self._region(region_id)
        if region["level"] == "ADM0":
            return block["national"]
        for item in block["regions"]:
            if item["geography_id"] == region["id"]:
                return item
        raise UnknownRegion(region["id"])

    def _place_bundle(
        self,
        variable: str,
        region: dict,
        start_year: int,
        end_year: int,
        trend: dict,
        baseline_start: int,
        baseline_end: int,
        comparison_start: int,
        comparison_end: int,
    ) -> dict:
        years, values, _coverage = self._series(variable, start_year, end_year, "annual", None, region)
        numeric = self._numeric_trend(years, values)
        baseline = period_statistic(years, values, baseline_start, baseline_end)
        comparison = period_statistic(years, values, comparison_start, comparison_end)
        difference = absolute_and_relative_difference(
            baseline["value"],
            comparison["value"],
            allow_relative=variable == "precipitation",
        )
        slope = _number(trend["sen_slope"])
        interval = trend["confidence_interval_95"]
        if interval is not None:
            interval = [_number(interval[0]), _number(interval[1])]
        return {
            "geography_id": region["id"],
            "geography_name": region["name"],
            "iso": region.get("iso"),
            "level": region["level"],
            "sen_slope": slope,
            "slope_per_decade": None if slope is None else slope * 10,
            "slope_text": trend["slope_text"],
            "slope_unit": trend["slope_unit"],
            "p_value": _number(trend["p_value"]),
            "adjusted_p_value": _number(trend["adjusted_p_value"]),
            "confidence_interval_95": interval,
            "trend_status": trend["trend_status"],
            "trend_direction": trend["trend_direction"],
            "valid_years": trend["valid_years"],
            "expected_years": trend["expected_years"],
            "coverage_fraction": _number(trend["coverage_fraction"]),
            "interpretation": trend["interpretation"],
            "test_method": trend["test_method"],
            "autocorrelation_method": trend["autocorrelation_method"],
            "multiple_testing_method": trend["multiple_testing_method"],
            "effective_start_year": trend["effective_start_year"],
            "effective_end_year": trend["effective_end_year"],
            "baseline_mean": baseline["value"],
            "comparison_mean": comparison["value"],
            "absolute_difference": difference["absolute_difference"],
            "relative_difference_percent": difference["relative_difference_percent"],
            "series": anomaly_series(years, values, baseline_start, baseline_end),
            "trend_line": _trend_line(years, numeric.intercept, numeric.sen_slope),
        }

    def _series(self, variable, start_year, end_year, aggregation, season, region):
        if aggregation == "monthly":
            return self._monthly_series(variable, start_year, end_year, region)
        aggregated = self._aggregated_dataset(variable, aggregation, season)
        values = aggregated["value"].values
        years = aggregated["year"].values.astype(int)
        include = self._include(region)
        weights = self._weights()
        total_weight = float(np.where(include, weights, 0).sum())
        selected = (years >= start_year) & (years <= end_year)
        output_years = years[selected]
        output_values = np.full(output_years.shape, np.nan)
        output_coverage = np.full(output_years.shape, np.nan)
        minimum = self.settings.minimum_spatial_coverage
        for position, year_index in enumerate(np.flatnonzero(selected)):
            valid = np.isfinite(values[year_index]) & include
            valid_weight = float(np.where(valid, weights, 0).sum())
            coverage = 0.0 if total_weight == 0 else valid_weight / total_weight
            output_coverage[position] = coverage
            if total_weight == 0 or coverage < minimum:
                continue
            output_values[position] = float(np.sum(values[year_index][valid] * weights[valid]) / valid_weight)
        return output_years, output_values, output_coverage

    def _monthly_series(self, variable, start_year, end_year, region):
        data = self.dataset[variable]
        times = data.time.to_pandas()
        include = self._include(region)
        weights = self._weights()
        total_weight = float(np.where(include, weights, 0).sum())
        years = []
        values = []
        coverage = []
        for index, stamp in enumerate(times):
            if not (start_year <= int(stamp.year) <= end_year):
                continue
            sample = data.values[index]
            valid = np.isfinite(sample) & include
            valid_weight = float(np.where(valid, weights, 0).sum())
            fraction = 0.0 if total_weight == 0 else valid_weight / total_weight
            years.append(int(stamp.year) * 100 + int(stamp.month))
            coverage.append(fraction)
            if fraction < self.settings.minimum_spatial_coverage or valid_weight == 0:
                values.append(np.nan)
            else:
                values.append(float(np.sum(sample[valid] * weights[valid]) / valid_weight))
        return np.array(years), np.array(values, dtype=float), np.array(coverage, dtype=float)

    def _aggregated_dataset(self, variable: str, aggregation: str, season: str | None) -> xr.Dataset:
        key = (variable, aggregation, season)
        if key not in self._aggregated:
            monthly = self.dataset[variable]
            if aggregation == "seasonal":
                self._aggregated[key] = aggregate_seasonal(monthly, variable, season or "")
            else:
                self._aggregated[key] = aggregate_annual(monthly, variable)
        return self._aggregated[key]

    def _grid_results(self, variable, start_year, end_year, aggregation, season) -> dict:
        key = (variable, start_year, end_year, aggregation, season)
        if key in self._grids:
            return self._grids[key]
        aggregated = self._aggregated_dataset(variable, aggregation, season)
        years = aggregated.year.values.astype(int)
        selected = (years >= start_year) & (years <= end_year)
        year_values = years[selected]
        grid_values = aggregated["value"].values[selected]
        mask = self.dataset["myanmar_mask"].values
        latitudes = self.dataset.latitude.values
        longitudes = self.dataset.longitude.values
        region_index = self.dataset["region_index"].values
        status = np.full(mask.shape, "insufficient_data", dtype=object)
        slopes = np.full(mask.shape, np.nan)
        p_values = np.full(mask.shape, np.nan)
        adjusted = np.full(mask.shape, np.nan)
        valid_counts = np.zeros(mask.shape, dtype=int)
        tested: list[tuple[int, int]] = []
        raw_p: list[float] = []
        numeric_by_cell: dict[tuple[int, int], object] = {}
        for lat_index in range(mask.shape[0]):
            for lon_index in range(mask.shape[1]):
                if not mask[lat_index, lon_index]:
                    continue
                numeric = series_trend(
                    year_values,
                    grid_values[:, lat_index, lon_index],
                    minimum_valid_years=self.settings.minimum_valid_years,
                    alpha=self.settings.significance_alpha,
                )
                numeric_by_cell[(lat_index, lon_index)] = numeric
                valid_counts[lat_index, lon_index] = numeric.valid_years
                if numeric.sen_slope is not None:
                    slopes[lat_index, lon_index] = numeric.sen_slope
                if numeric.p_value is not None and numeric.valid_years >= self.settings.minimum_valid_years:
                    tested.append((lat_index, lon_index))
                    raw_p.append(numeric.p_value)
                    p_values[lat_index, lon_index] = numeric.p_value
        corrected = adjust_pvalues(raw_p, alpha=self.settings.significance_alpha)
        for (lat_index, lon_index), p_adjusted in zip(tested, corrected, strict=True):
            adjusted[lat_index, lon_index] = p_adjusted
            numeric = numeric_by_cell[(lat_index, lon_index)]
            status[lat_index, lon_index] = classify_trend(
                numeric,
                p_adjusted,
                alpha=self.settings.significance_alpha,
                minimum_valid_years=self.settings.minimum_valid_years,
            )
        half_lat = self.region_catalog["latitude_spacing"] / 2
        half_lon = self.region_catalog["longitude_spacing"] / 2
        features = []
        for lat_index, latitude in enumerate(latitudes):
            for lon_index, longitude in enumerate(longitudes):
                if not mask[lat_index, lon_index]:
                    continue
                numeric = numeric_by_cell[(lat_index, lon_index)]
                region_name = self._region_name(int(region_index[lat_index, lon_index]))
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                _cell_ring(float(longitude), float(latitude), half_lon, half_lat)
                            ],
                        },
                        "properties": {
                            "latitude": float(latitude),
                            "longitude": float(longitude),
                            "region_name": region_name,
                            "sen_slope": _number(slopes[lat_index, lon_index]),
                            "p_value": _number(p_values[lat_index, lon_index]),
                            "adjusted_p_value": _number(adjusted[lat_index, lon_index]),
                            "trend_status": str(status[lat_index, lon_index]),
                            "valid_years": int(valid_counts[lat_index, lon_index]),
                            "coverage_fraction": (
                                None
                                if numeric.expected_years == 0
                                else numeric.valid_years / numeric.expected_years
                            ),
                            "test_method": numeric.test_method,
                            "slope_unit": VARIABLES[variable].slope_unit,
                        },
                    }
                )
        result = {"features": features, "status": status}
        self._grids[key] = result
        return result

    def _admin_trends(self, variable, start_year, end_year, aggregation, season) -> list[dict]:
        records = []
        p_values = []
        positions = []
        for index, region in enumerate(self.region_catalog["regions"]):
            resolved = self._region(region["id"])
            years, values, _coverage = self._series(
                variable, start_year, end_year, aggregation, season, resolved
            )
            numeric = self._numeric_trend(years, values)
            record = self._trend_record(
                variable,
                resolved,
                start_year,
                end_year,
                aggregation,
                season,
                numeric,
                adjusted_p_value=None,
                multiple_testing_method="benjamini_hochberg",
            )
            records.append(record)
            if numeric.p_value is not None and numeric.valid_years >= self.settings.minimum_valid_years:
                p_values.append(numeric.p_value)
                positions.append(index)
        corrected = adjust_pvalues(p_values, alpha=self.settings.significance_alpha)
        for index, p_adjusted in zip(positions, corrected, strict=True):
            records[index]["adjusted_p_value"] = p_adjusted
            records[index]["trend_status"] = classify_trend(
                _trend_from_record(records[index]),
                p_adjusted,
                alpha=self.settings.significance_alpha,
                minimum_valid_years=self.settings.minimum_valid_years,
            )
            records[index]["interpretation"] = interpret_trend(records[index])
        return records

    def _trend_record(
        self,
        variable,
        region,
        start_year,
        end_year,
        aggregation,
        season,
        numeric,
        adjusted_p_value,
        multiple_testing_method,
    ) -> dict:
        definition = VARIABLES[variable]
        p_for_status = numeric.p_value if multiple_testing_method == "none" else adjusted_p_value
        if multiple_testing_method == "none":
            adjusted_p_value = numeric.p_value
        status = classify_trend(
            numeric,
            p_for_status,
            alpha=self.settings.significance_alpha,
            minimum_valid_years=self.settings.minimum_valid_years,
        )
        coverage = None if numeric.expected_years == 0 else numeric.valid_years / numeric.expected_years
        season_label = None if aggregation != "seasonal" else f"{season} ({'-'.join(str(m) for m in SEASON_MONTHS[season])})"
        aggregation_label = "annual" if aggregation == "annual" else f"{season} seasonal"
        record = {
            "variable": variable,
            "variable_label": definition.label,
            "unit": definition.analysis_unit,
            "slope_unit": definition.slope_unit,
            "geography_type": region["level"],
            "geography_id": region["id"],
            "geography_name": region["name"],
            "requested_start_year": start_year,
            "requested_end_year": end_year,
            "effective_start_year": numeric.first_year,
            "effective_end_year": numeric.last_year,
            "aggregation": aggregation,
            "aggregation_label": aggregation_label,
            "season_definition": season_label,
            "first_valid_value": numeric.first_value,
            "first_valid_year": numeric.first_year,
            "last_valid_value": numeric.last_value,
            "last_valid_year": numeric.last_year,
            "absolute_change": numeric.absolute_change,
            "sen_slope": numeric.sen_slope,
            "slope_text": _format_number(numeric.sen_slope, variable),
            "p_value": numeric.p_value,
            "adjusted_p_value": adjusted_p_value,
            "confidence_interval_95": (
                None
                if numeric.ci_low is None or numeric.ci_high is None
                else [numeric.ci_low, numeric.ci_high]
            ),
            "trend_direction": trend_direction(numeric.sen_slope),
            "trend_status": status,
            "significance_alpha": self.settings.significance_alpha,
            "test_method": numeric.test_method,
            "autocorrelation_method": numeric.autocorrelation_method,
            "multiple_testing_method": multiple_testing_method,
            "valid_years": numeric.valid_years,
            "expected_years": numeric.expected_years,
            "coverage_fraction": coverage,
            "quality_flags": list(numeric.quality_flags),
            "source": "NASA POWER",
            "source_parameter": definition.source_parameter,
            "retrieved_at": self.metadata()["retrieved_at"],
            "processing_version": "0.2.0",
        }
        record["interpretation"] = interpret_trend(record)
        return record

    def _numeric_trend(self, years, values):
        return series_trend(
            years,
            values,
            minimum_valid_years=self.settings.minimum_valid_years,
            alpha=self.settings.significance_alpha,
        )

    def _weights(self) -> np.ndarray:
        latitude_weights = np.cos(np.radians(self.dataset.latitude.values))
        return np.repeat(latitude_weights[:, None], int(self.dataset.longitude.size), axis=1)

    def _include(self, region: dict) -> np.ndarray:
        mask = self.dataset["myanmar_mask"].values
        if region["level"] == "ADM0":
            return mask
        return self.dataset["region_index"].values == region["index"]

    def _region(self, region_id: str | None) -> dict:
        if region_id in (None, "", NATIONAL_ALIAS):
            region_id = self.region_catalog["national"]["id"]
        try:
            return self.regions[region_id]
        except KeyError as exc:
            raise UnknownRegion(str(region_id)) from exc

    def _region_name(self, index: int) -> str | None:
        if index < 0:
            return None
        return self.region_catalog["regions"][index]["name"]

    @staticmethod
    def _index_regions(region_catalog: dict) -> dict[str, dict]:
        national = dict(region_catalog["national"])
        national["index"] = None
        indexed = {national["id"]: national, NATIONAL_ALIAS: national}
        for index, region in enumerate(region_catalog["regions"]):
            item = dict(region)
            item["index"] = index
            indexed[item["id"]] = item
        return indexed

    @staticmethod
    def _require_summary_aggregation(aggregation: str) -> None:
        if aggregation == "monthly":
            raise ValueError(
                "Trend tests use annual or seasonal series. Raw monthly values are not tested."
            )

    @staticmethod
    def _require_window(name: str, start: int, end: int, requested_start: int, requested_end: int) -> None:
        if end < start:
            raise ValueError(f"The {name} window ends before it starts.")
        if start < requested_start or end > requested_end:
            raise ValueError(f"The {name} window must fall inside the requested period.")


_catalog: ClimateCatalog | None = None


def get_catalog() -> ClimateCatalog:
    global _catalog
    if _catalog is None:
        _catalog = ClimateCatalog.load()
    return _catalog


def clear_catalog() -> None:
    global _catalog
    _catalog = None


def _number(value: object) -> float | None:
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not np.isfinite(number):
        return None
    return number


def _format_number(value: float | None, variable: str) -> str:
    if value is None:
        return "unavailable"
    digits = 3 if variable == "temperature" else 2
    return f"{value:.{digits}f}"


def _cell_ring(longitude: float, latitude: float, half_lon: float, half_lat: float) -> list[list[float]]:
    return [
        [longitude - half_lon, latitude - half_lat],
        [longitude + half_lon, latitude - half_lat],
        [longitude + half_lon, latitude + half_lat],
        [longitude - half_lon, latitude + half_lat],
        [longitude - half_lon, latitude - half_lat],
    ]


def _case_windows(start_year: int, end_year: int) -> tuple[int, int, int, int]:
    baseline_end = min(start_year + 9, end_year)
    comparison_start = max(start_year, end_year - 9)
    return start_year, baseline_end, comparison_start, end_year


def _decade_unit(variable: str) -> str:
    if variable == "temperature":
        return "degC per 10 years"
    if variable == "precipitation":
        return "mm per 10 years"
    return "percentage points per 10 years"


def _trend_line(years: np.ndarray, intercept: float | None, slope: float | None) -> list[dict]:
    if intercept is None or slope is None:
        return []
    return [
        {"year": int(year), "value": float(intercept + slope * int(year))}
        for year in years
    ]


def _trend_from_record(record: dict):
    from app.services.trend_analysis import NumericTrend

    return NumericTrend(
        sen_slope=record["sen_slope"],
        intercept=None,
        p_value=record["p_value"],
        ci_low=None,
        ci_high=None,
        valid_years=record["valid_years"],
        expected_years=record["expected_years"],
        first_year=record["first_valid_year"],
        first_value=record["first_valid_value"],
        last_year=record["last_valid_year"],
        last_value=record["last_valid_value"],
        absolute_change=record["absolute_change"],
        test_method=record["test_method"],
        autocorrelation_method=record["autocorrelation_method"],
    )


def processed_dataset_path(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.processed_dir / "climate_monthly.nc"
