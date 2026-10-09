from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import call_catalog, reject_monthly_trends, validate_period
from app.core.config import get_settings
from app.schemas.climate import Aggregation, ClimateVariable, Season

router = APIRouter()


@router.get("/impact/summary")
def impact_summary(
    variable: Annotated[ClimateVariable, Query()],
    start_year: Annotated[int, Query(ge=1981, le=2100)],
    end_year: Annotated[int, Query(ge=1981, le=2100)],
    aggregation: Annotated[Aggregation, Query()] = "annual",
    region_id: Annotated[str | None, Query()] = None,
    season: Annotated[Season | None, Query()] = None,
    baseline_start: Annotated[int | None, Query(ge=1981, le=2100)] = None,
    baseline_end: Annotated[int | None, Query(ge=1981, le=2100)] = None,
    comparison_start: Annotated[int | None, Query(ge=1981, le=2100)] = None,
    comparison_end: Annotated[int | None, Query(ge=1981, le=2100)] = None,
) -> dict:
    validate_period(start_year, end_year, aggregation, season)
    reject_monthly_trends(aggregation)
    settings = get_settings()
    return call_catalog(
        "impact_summary",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
        region_id=region_id,
        baseline_start=baseline_start if baseline_start is not None else settings.default_start_year,
        baseline_end=baseline_end if baseline_end is not None else settings.default_start_year + 9,
        comparison_start=comparison_start if comparison_start is not None else settings.default_end_year - 9,
        comparison_end=comparison_end if comparison_end is not None else settings.default_end_year,
    )


@router.get("/impact/anomalies")
def impact_anomalies(
    variable: Annotated[ClimateVariable, Query()],
    start_year: Annotated[int, Query(ge=1981, le=2100)],
    end_year: Annotated[int, Query(ge=1981, le=2100)],
    aggregation: Annotated[Aggregation, Query()] = "annual",
    region_id: Annotated[str | None, Query()] = None,
    season: Annotated[Season | None, Query()] = None,
    baseline_start: Annotated[int | None, Query(ge=1981, le=2100)] = None,
    baseline_end: Annotated[int | None, Query(ge=1981, le=2100)] = None,
) -> dict:
    validate_period(start_year, end_year, aggregation, season)
    reject_monthly_trends(aggregation)
    settings = get_settings()
    return call_catalog(
        "anomalies",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
        region_id=region_id,
        baseline_start=baseline_start if baseline_start is not None else settings.default_start_year,
        baseline_end=baseline_end if baseline_end is not None else settings.default_start_year + 9,
    )
