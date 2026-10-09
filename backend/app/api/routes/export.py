import csv
import io
import json
from typing import Annotated

from fastapi import APIRouter, Query
from fastapi.responses import Response

from app.api.deps import call_catalog, reject_monthly_trends, validate_period
from app.core.config import get_settings
from app.schemas.climate import Aggregation, ClimateVariable, Season

router = APIRouter()


@router.get("/export/timeseries.csv")
def export_timeseries(
    variable: Annotated[ClimateVariable, Query()],
    start_year: Annotated[int, Query(ge=1981, le=2100)],
    end_year: Annotated[int, Query(ge=1981, le=2100)],
    aggregation: Annotated[Aggregation, Query()] = "annual",
    region_id: Annotated[str | None, Query()] = None,
    season: Annotated[Season | None, Query()] = None,
) -> Response:
    validate_period(start_year, end_year, aggregation, season)
    payload = call_catalog(
        "timeseries",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
        region_id=region_id,
    )
    rows = [
        {
            "variable": payload["variable"],
            "unit": payload["unit"],
            "aggregation": payload["aggregation"],
            "season": payload["season"] or "",
            "region_id": payload["region_id"],
            "region_name": payload["region_name"],
            "year": point["year"],
            "month": point["month"] if point["month"] is not None else "",
            "value": "" if point["value"] is None else point["value"],
            "coverage_fraction": ""
            if point["coverage_fraction"] is None
            else point["coverage_fraction"],
            "source": payload["source"],
            "source_parameter": payload["source_parameter"],
        }
        for point in payload["data"]
    ]
    return _csv(rows, "timeseries.csv")


@router.get("/export/trends.csv")
def export_trends(
    variable: Annotated[ClimateVariable, Query()] = "temperature",
    start_year: Annotated[int, Query(ge=1981, le=2100)] = 2001,
    end_year: Annotated[int, Query(ge=1981, le=2100)] = 2025,
    aggregation: Annotated[Aggregation, Query()] = "annual",
    season: Annotated[Season | None, Query()] = None,
) -> Response:
    validate_period(start_year, end_year, aggregation, season)
    reject_monthly_trends(aggregation)
    payload = call_catalog(
        "grid",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
    )
    rows = [feature["properties"] for feature in payload["features"]]
    return _csv(rows, "trends.csv")


@router.get("/export/trends.geojson")
def export_trends_geojson(
    variable: Annotated[ClimateVariable, Query()] = "temperature",
    start_year: Annotated[int, Query(ge=1981, le=2100)] = 2001,
    end_year: Annotated[int, Query(ge=1981, le=2100)] = 2025,
    aggregation: Annotated[Aggregation, Query()] = "annual",
    season: Annotated[Season | None, Query()] = None,
) -> Response:
    validate_period(start_year, end_year, aggregation, season)
    reject_monthly_trends(aggregation)
    payload = call_catalog(
        "grid",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
    )
    body = {"type": "FeatureCollection", "features": payload["features"]}
    return Response(
        json.dumps(body),
        media_type="application/geo+json",
        headers={"Content-Disposition": 'attachment; filename="trends.geojson"'},
    )


@router.get("/export/impact.csv")
def export_impact(
    variable: Annotated[ClimateVariable, Query()] = "temperature",
    start_year: Annotated[int, Query(ge=1981, le=2100)] = 2001,
    end_year: Annotated[int, Query(ge=1981, le=2100)] = 2025,
    aggregation: Annotated[Aggregation, Query()] = "annual",
    region_id: Annotated[str | None, Query()] = None,
    season: Annotated[Season | None, Query()] = None,
) -> Response:
    validate_period(start_year, end_year, aggregation, season)
    reject_monthly_trends(aggregation)
    settings = get_settings()
    payload = call_catalog(
        "impact_summary",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
        region_id=region_id,
        baseline_start=settings.default_start_year,
        baseline_end=settings.default_start_year + 9,
        comparison_start=settings.default_end_year - 9,
        comparison_end=settings.default_end_year,
    )
    row = {
        key: value
        for key, value in payload.items()
        if key not in {"interpretation", "limitation", "quality_flags"}
    }
    row["quality_flags"] = ";".join(payload["quality_flags"])
    row["interpretation"] = payload["interpretation"]
    return _csv([row], "impact.csv")


def _csv(rows: list[dict], filename: str) -> Response:
    buffer = io.StringIO()
    if not rows:
        buffer.write("message\nNo rows for the current filters.\n")
    else:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return Response(
        buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
