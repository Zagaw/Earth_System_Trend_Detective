from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import call_catalog, reject_monthly_trends, validate_period
from app.schemas.climate import Aggregation, ClimateVariable, Season

router = APIRouter()


@router.get("/trends/summary")
def trend_summary(
    variable: Annotated[ClimateVariable, Query()],
    start_year: Annotated[int, Query(ge=1981, le=2100)],
    end_year: Annotated[int, Query(ge=1981, le=2100)],
    aggregation: Annotated[Aggregation, Query()] = "annual",
    region_id: Annotated[str | None, Query()] = None,
    season: Annotated[Season | None, Query()] = None,
) -> dict:
    validate_period(start_year, end_year, aggregation, season)
    reject_monthly_trends(aggregation)
    return call_catalog(
        "trend",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
        region_id=region_id,
    )


@router.get("/trends/grid")
def trend_grid(
    variable: Annotated[ClimateVariable, Query()],
    start_year: Annotated[int, Query(ge=1981, le=2100)],
    end_year: Annotated[int, Query(ge=1981, le=2100)],
    aggregation: Annotated[Aggregation, Query()] = "annual",
    season: Annotated[Season | None, Query()] = None,
) -> dict:
    validate_period(start_year, end_year, aggregation, season)
    reject_monthly_trends(aggregation)
    return call_catalog(
        "grid",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
    )


@router.get("/trends/region")
def trend_region(
    variable: Annotated[ClimateVariable, Query()],
    start_year: Annotated[int, Query(ge=1981, le=2100)],
    end_year: Annotated[int, Query(ge=1981, le=2100)],
    region_id: Annotated[str, Query(min_length=1)],
    aggregation: Annotated[Aggregation, Query()] = "annual",
    season: Annotated[Season | None, Query()] = None,
) -> dict:
    validate_period(start_year, end_year, aggregation, season)
    reject_monthly_trends(aggregation)
    return call_catalog(
        "trend",
        variable=variable,
        start_year=start_year,
        end_year=end_year,
        aggregation=aggregation,
        season=season,
        region_id=region_id,
    )
